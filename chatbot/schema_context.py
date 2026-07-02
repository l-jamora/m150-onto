"""System prompts and few-shot examples for the M150-Onto NL->SPARQL chatbot.

Adapted from TTYG-agent-instructions-draft.md (written for GraphDB's Talk to
Your Graph chatbot). The ontology facts are the same; the framing is
rewritten for a two-call pipeline (generate SPARQL, then compose an answer)
instead of a single tool-calling agent.
"""

from pathlib import Path

import rdflib
from rdflib.namespace import OWL, RDF, RDFS

PREFIX = "m150"
NAMESPACE = "https://l-jamora.github.io/m150-onto#"
INDIVIDUAL_PREFIX = "Beispiel_"  # mirrors ontoparser.parser.INDIVIDUAL_PREFIX

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ONTOLOGY_PATH = _REPO_ROOT / "m150-onto.rdf"


def _local_name(iri: str) -> str:
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _build_property_reference() -> str:
    """Mechanically enumerates every m150: object/datatype property straight from
    m150-onto.rdf, so the prompt can never omit a real property. This replaces
    relying on hand-curated prose lists to cover every property -- the class of
    bug that produced hasSiteManager/hasCameraSystem/hasVideoFile (plausible
    guesses for properties that were never mentioned in the prompt, silently
    returning empty OPTIONAL results instead of erroring).
    """
    graph = rdflib.Graph()
    graph.parse(str(_ONTOLOGY_PATH), format="xml", publicID=NAMESPACE.rstrip("#"))

    lines = []
    for prop_type in (OWL.ObjectProperty, OWL.DatatypeProperty):
        props = sorted(
            s for s in graph.subjects(RDF.type, prop_type) if str(s).startswith(NAMESPACE)
        )
        for prop in props:
            sig = f"{PREFIX}:{_local_name(str(prop))}"
            ranges = sorted({_local_name(str(r)) for r in graph.objects(prop, RDFS.range)})
            if ranges:
                sig += f" -> {'/'.join(ranges)}"
            if (prop, RDF.type, OWL.FunctionalProperty) in graph:
                sig += " [single-valued]"
            lines.append(sig)
    return "\n".join(lines)


_PROPERTY_REFERENCE = _build_property_reference()

_ONTOLOGY_FACTS = f"""
This ontology (prefix {PREFIX}:, namespace {NAMESPACE}) models the German DWA-M 150 standard
for sewer network inspection: pipe sections and nodes (both subclasses of Component, and
disjoint with each other), their inspection reports, and condition/damage findings.

Critical rule -- Reference values are individuals, not classes. Material, SewerType, Shape,
NodeType, and other Reference subclasses are named individuals (e.g. {PREFIX}:M150_RT105_STZ =
stoneware/Steinzeug), never OWL classes. Never generate a pattern like
"?pipe a {PREFIX}:Concrete". Always traverse via the relevant object property instead, e.g.
"?pipe {PREFIX}:hasMaterial {PREFIX}:M150_RT105_STZ". Getting this pattern wrong silently
returns empty results.

Property behavior: most hasX object properties are single-valued (functional). The following
are intentionally multi-valued: flowsTo, flowsFrom, connectedWith (network topology),
inspects/inspectedIn, isChildOf/isParentOf, renders/renderedBy. Inverse properties have been
pre-materialized into the store for reverse navigation -- isMaterialOf, isSewerTypeOf,
isInspectorIn, isStreetOf, isRoleOf, isParentOf, inspectedIn, flowsFrom -- so you can start a
query from either side of these relationships. Do NOT rely on the reverse direction of
hasPipeSectionTopNodeDesignation/hasPipeSectionBottomNodeDesignation -- those two are NOT valid
inverses of each other (a known ontology modeling issue) and no reverse triples were
materialized for that pair; both always go PipeSection -> Node.

People and organizations are linked to an Inspection via these exact role properties -- do not
guess a different spelling: hasClient, hasCompany, hasInspector, hasReporter,
hasSiteManagement (note: NOT "hasSiteManager" -- the Role individual is named SiteManager but
the linking property is hasSiteManagement), hasAssessor. A single Inspection can have several of
these at once (e.g. an inspector and a site manager and a company), so a question naming
multiple roles should use one OPTIONAL block per role property on the same ?inspection.

Inspection media are linked via these exact property spellings -- do not guess a different form:
hasCameraSystemUsed (NOT "hasCameraSystem"), hasVideoFilename (NOT "hasVideoFile"),
hasVideoStorageMedium / hasVideoStorageMediumName, hasImageName, hasNodeInspectionDigitalPhotoName,
hasNodeInspectionAmbientPhoto. Use OPTIONAL for each since not every inspection has every media
field recorded.

Individuals in this demo dataset are prefixed "{INDIVIDUAL_PREFIX}" (German for "example") --
this is a placeholder-data marker from the XML parser, not meaningful domain data. Do not
present it to the user as significant; strip it when showing entity names or labels.

Individual IRI naming is only predictable for PipeSection and Node: always exactly
{PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_<id> / {PREFIX}:{INDIVIDUAL_PREFIX}Node_<id>. Inspection
and Condition individual names are NOT uniformly patterned -- some Inspections are named
{INDIVIDUAL_PREFIX}Inspection_<id> and others {INDIVIDUAL_PREFIX}Inspection_<id>_<date>_<time>,
depending on the source data. When a question names an inspection or condition by a bare ID
number (e.g. "inspection 1204012"), never construct that IRI directly (e.g. never guess
{PREFIX}:{INDIVIDUAL_PREFIX}1204012 or {PREFIX}:{INDIVIDUAL_PREFIX}Inspection_1204012). Instead
always start from {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_<id> or
{PREFIX}:{INDIVIDUAL_PREFIX}Node_<id> and traverse to the Inspection via {PREFIX}:inspects /
{PREFIX}:inspectedIn (e.g. "?inspection {PREFIX}:inspects {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204012"),
then reach Conditions from there via {PREFIX}:isChildOf / {PREFIX}:isParentOf.

Condition findings carry a 3-letter DWA condition code (hasConditionCode, e.g. "BCA") and
German free text (hasLongText, e.g. "Längsriss" = longitudinal crack). There is no built-in
severity or priority score in this ontology. If asked to prioritize repairs, reason from the
available codes, text, and defect counts, and say explicitly that this is an approximation
rather than a defined severity field.

Network topology properties (flowsTo, connectedWith) are essentially unpopulated in this
dataset. Pipe sections must instead be chained by joining on shared node IDs via
hasPipeSectionTopNodeDesignation and hasPipeSectionBottomNodeDesignation -- e.g. pipe section A's
bottom node equals pipe section B's top node means A flows into B.

Full property reference, auto-generated directly from m150-onto.rdf -- these are the ONLY real
property names in this ontology. If a property you want isn't in this list, it does not exist;
do not invent a plausible-sounding variant (this is exactly how past mistakes like
"hasSiteManager"/"hasCameraSystem"/"hasVideoFile" happened -- none of those exist, the real
properties are hasSiteManagement/hasCameraSystemUsed/hasVideoFilename, all listed below).
"[single-valued]" means functional (at most one value per subject); everything else may repeat.
{_PROPERTY_REFERENCE}
""".strip()

SPARQL_GENERATION_SYSTEM_PROMPT = f"""
You translate natural-language questions from a sewer network operator into SPARQL 1.1 SELECT
queries against a local RDF store containing the M150-Onto ontology and example inspection data.

{_ONTOLOGY_FACTS}

Output rules:
- Respond with ONLY the SPARQL query text. No explanation, no markdown code fences, no prose.
- Always start the query with "PREFIX {PREFIX}: <{NAMESPACE}>".
- Always use SELECT -- never ASK, CONSTRUCT, or DESCRIBE, even for yes/no-sounding questions
  ("does X have..." should be a SELECT that returns rows or no rows, not an ASK boolean). Use
  OPTIONAL for fields that might not exist rather than failing the whole query.
- If given a previous failed attempt and an error or "no results" note, fix the query instead of
  repeating the same mistake.
""".strip()

ANSWER_COMPOSITION_SYSTEM_PROMPT = f"""
You compose a short, decision-ready natural-language answer for a sewer network operator, based
on a SPARQL query that was just run against the M150-Onto ontology and its result rows.

{_ONTOLOGY_FACTS}

Output rules:
- Strip the "{INDIVIDUAL_PREFIX}" placeholder prefix from any entity name before showing it to
  the user (e.g. "{INDIVIDUAL_PREFIX}PipeSection_1204015" -> "pipe section 1204015").
- If the result rows are empty, say plainly that no matching data was found -- do not invent an
  answer.
- If you are approximating something the ontology doesn't directly encode (e.g. repair
  priority), say so explicitly.
- Keep the answer concise and grounded only in the provided result rows.
""".strip()

# Hand-verified against the actual materialized store (chatbot/store), not invented.
FEW_SHOT_EXAMPLES: list[tuple[str, str]] = [
    (
        "What material is pipe section 1204015?",
        f"""PREFIX {PREFIX}: <{NAMESPACE}>
SELECT ?material WHERE {{
  {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204015 {PREFIX}:hasMaterial ?material .
}}""",
    ),
    (
        "Who inspected pipe section 1204015?",
        f"""PREFIX {PREFIX}: <{NAMESPACE}>
SELECT ?inspection ?person WHERE {{
  ?inspection {PREFIX}:inspects {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204015 .
  ?inspection {PREFIX}:hasInspector ?person .
}}""",
    ),
    (
        "Who inspected pipe section 1204015, and who was the site manager on that inspection?",
        f"""PREFIX {PREFIX}: <{NAMESPACE}>
SELECT ?inspector ?siteManager ?company WHERE {{
  ?inspection {PREFIX}:inspects {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204015 .
  OPTIONAL {{ ?inspection {PREFIX}:hasInspector ?inspector }}
  OPTIONAL {{ ?inspection {PREFIX}:hasSiteManagement ?siteManager }}
  OPTIONAL {{ ?inspection {PREFIX}:hasCompany ?company }}
}}""",
    ),
    (
        "What camera system and video file were used for the inspection of 1204015?",
        f"""PREFIX {PREFIX}: <{NAMESPACE}>
SELECT ?cameraSystem ?videoFile WHERE {{
  ?inspection {PREFIX}:inspects {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204015 .
  OPTIONAL {{ ?inspection {PREFIX}:hasCameraSystemUsed ?cameraSystem }}
  OPTIONAL {{ ?inspection {PREFIX}:hasVideoFilename ?videoFile }}
}}""",
    ),
    (
        "What pipe sections connect to pipe section 1204015?",
        f"""PREFIX {PREFIX}: <{NAMESPACE}>
SELECT ?otherPipe WHERE {{
  {{
    {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204015 {PREFIX}:hasPipeSectionTopNodeDesignation ?n .
    ?otherPipe {PREFIX}:hasPipeSectionBottomNodeDesignation ?n .
  }} UNION {{
    {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204015 {PREFIX}:hasPipeSectionBottomNodeDesignation ?n .
    ?otherPipe {PREFIX}:hasPipeSectionTopNodeDesignation ?n .
  }}
}}""",
    ),
    (
        "List the condition findings for pipe section 1204015 with their DWA codes and descriptions.",
        f"""PREFIX {PREFIX}: <{NAMESPACE}>
SELECT ?condition ?code ?text WHERE {{
  ?inspection {PREFIX}:inspects {PREFIX}:{INDIVIDUAL_PREFIX}PipeSection_1204015 .
  ?condition {PREFIX}:isChildOf ?inspection .
  ?condition {PREFIX}:hasConditionCode ?code .
  OPTIONAL {{ ?condition {PREFIX}:hasLongText ?text }}
}}""",
    ),
]
