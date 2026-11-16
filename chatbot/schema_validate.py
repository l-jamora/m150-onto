"""Validates that a generated SPARQL query only uses real ontology predicates.

The two live bugs found so far in this chatbot (hasSiteManager, hasCameraSystem/
hasVideoFile) share a shape: the model guesses a plausible-sounding property name
that doesn't exist, wraps it in OPTIONAL (as instructed), and the query runs fine
but silently returns an unbound variable instead of erroring -- so the existing
"zero rows" retry in sparql_pipeline.py never has a *reason* to give the model,
just a generic "try again". This module extracts the predicates a generated query
actually references and checks them against the real property set, so a retry can
name the exact bad property and suggest the closest real one.
"""

import difflib
import re

import pyoxigraph
from rdflib.plugins.sparql.algebra import translateQuery
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.term import URIRef

from chatbot.schema_context import NAMESPACE, PREFIX

_ALWAYS_VALID = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "http://www.w3.org/2000/01/rdf-schema#label",
    "http://www.w3.org/2000/01/rdf-schema#comment",
}

_known_predicates_cache: dict[int, set[str]] = {}


def _local_name(iri: str) -> str:
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def known_predicates(store: pyoxigraph.Store) -> set[str]:
    """Every real m150: property IRI declared in the store, cached per store instance."""
    cached = _known_predicates_cache.get(id(store))
    if cached is not None:
        return cached

    rows = store.query(
        "SELECT ?p WHERE { ?p a ?type . FILTER(?type IN (owl:ObjectProperty, owl:DatatypeProperty)) }",
        prefixes={"owl": "http://www.w3.org/2002/07/owl#"},
    )
    predicates = {row["p"].value for row in rows} | _ALWAYS_VALID
    _known_predicates_cache[id(store)] = predicates
    return predicates


def extract_predicate_iris(sparql: str) -> set[str]:
    """Every predicate IRI used in a triple pattern of the query (ignores variable predicates)."""
    try:
        algebra = translateQuery(parseQuery(sparql)).algebra
    except Exception:
        return set()

    predicates: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, CompValue):
            triples = node.get("triples")
            if triples:
                for triple in triples:
                    if len(triple) == 3 and isinstance(triple[1], URIRef):
                        predicates.add(str(triple[1]))
            for key, value in node.items():
                if key != "triples":
                    walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)

    walk(algebra)
    return predicates


def find_unknown_predicates(sparql: str, store: pyoxigraph.Store) -> list[tuple[str, str | None]]:
    """Returns [(bad_local_name, closest_real_local_name_or_None), ...] for this query."""
    known = known_predicates(store)
    used = extract_predicate_iris(sparql)
    unknown = sorted(iri for iri in used if iri.startswith(NAMESPACE) and iri not in known)
    if not unknown:
        return []

    known_local_names = sorted(_local_name(iri) for iri in known if iri.startswith(NAMESPACE))
    results = []
    for iri in unknown:
        bad_name = _local_name(iri)
        match = difflib.get_close_matches(bad_name, known_local_names, n=1, cutoff=0.5)
        results.append((bad_name, match[0] if match else None))
    return results


def build_retry_note(unknown: list[tuple[str, str | None]]) -> str:
    lines = ["That query used properties that do not exist in the ontology:"]
    for bad_name, suggestion in unknown:
        if suggestion:
            lines.append(f'  {PREFIX}:{bad_name} -- did you mean {PREFIX}:{suggestion}?')
        else:
            lines.append(f"  {PREFIX}:{bad_name} -- no close match found, re-check the property reference")
    lines.append("Fix the property names and try again.")
    return "\n".join(lines)


_known_individuals_cache: dict[int, set[str]] = {}


def known_individuals(store: pyoxigraph.Store) -> set[str]:
    """Every real m150: individual IRI declared in the store, cached per store instance."""
    cached = _known_individuals_cache.get(id(store))
    if cached is not None:
        return cached

    rows = store.query(
        "SELECT ?s WHERE { ?s a owl:NamedIndividual }",
        prefixes={"owl": "http://www.w3.org/2002/07/owl#"},
    )
    individuals = {row["s"].value for row in rows}
    _known_individuals_cache[id(store)] = individuals
    return individuals


def extract_constant_iris(sparql: str) -> set[str]:
    """Every IRI used as a subject or object (not predicate) of a triple pattern."""
    try:
        algebra = translateQuery(parseQuery(sparql)).algebra
    except Exception:
        return set()

    iris: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, CompValue):
            triples = node.get("triples")
            if triples:
                for triple in triples:
                    if len(triple) == 3:
                        for term in (triple[0], triple[2]):
                            if isinstance(term, URIRef):
                                iris.add(str(term))
            for key, value in node.items():
                if key != "triples":
                    walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)

    walk(algebra)
    return iris


def find_unknown_individuals(sparql: str, store: pyoxigraph.Store) -> list[tuple[str, list[str]]]:
    """Returns [(bad_local_name, [close_real_local_names]), ...] for this query.

    Individual names in this ontology are not uniformly patterned (e.g. some Inspection
    individuals are named Beispiel_Inspection_<id> and others Beispiel_Inspection_<id>_<date>_
    <time>), so the model sometimes guesses a bare-ID IRI like Beispiel_1204012 that was never
    parsed from the source data. Since that guess is syntactically valid SPARQL, it just returns
    zero rows with no error -- so, like find_unknown_predicates, this has to be caught by checking
    against the real individual set before running the query.
    """
    known = known_individuals(store)
    used = extract_constant_iris(sparql)
    unknown = sorted(iri for iri in used if iri.startswith(NAMESPACE) and iri not in known)
    if not unknown:
        return []

    known_local_names = sorted(_local_name(iri) for iri in known if iri.startswith(NAMESPACE))
    results = []
    for iri in unknown:
        bad_name = _local_name(iri)
        digits = "".join(re.findall(r"\d+", bad_name))
        candidates = [n for n in known_local_names if digits and digits in n] if digits else []
        if not candidates:
            candidates = difflib.get_close_matches(bad_name, known_local_names, n=5, cutoff=0.4)
        else:
            # Shorter names are less-decorated entity IDs (e.g. Node_<id>, PipeSection_<id>)
            # and are far more likely to be what a bare-ID guess meant than a long,
            # multiply-qualified name like Condition_<id>_<station>_<code>.
            candidates = sorted(candidates, key=len)
        results.append((bad_name, candidates[:5]))
    return results


def build_individual_retry_note(unknown: list[tuple[str, list[str]]]) -> str:
    lines = ["That query referenced individuals that do not exist in the ontology:"]
    for bad_name, candidates in unknown:
        if candidates:
            options = ", ".join(f"{PREFIX}:{c}" for c in candidates)
            lines.append(f"  {PREFIX}:{bad_name} -- does not exist. Did you mean one of: {options}?")
        else:
            lines.append(f"  {PREFIX}:{bad_name} -- does not exist, and no similar individual was found")
    lines.append(
        "Individual IRIs must never be guessed from a bare ID number -- naming is inconsistent "
        "across entity types (e.g. some Inspections are Beispiel_Inspection_<id>, others "
        "Beispiel_Inspection_<id>_<date>_<time>). Instead, resolve them by traversing a "
        f"relationship from a Component whose name IS predictable ({PREFIX}:Beispiel_PipeSection_<id> "
        f"or {PREFIX}:Beispiel_Node_<id>), e.g. via {PREFIX}:inspects / {PREFIX}:inspectedIn to reach "
        "the correct Inspection individual."
    )
    return "\n".join(lines)
