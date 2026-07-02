# M150-Onto Chatbot

A local, natural-language chatbot over the M150-Onto ontology: ask a plain-language question
about the sewer network, and it translates the question into SPARQL, runs it against a local
triplestore, and answers in prose grounded in the actual query results.

## Why this exists

The original plan was GraphDB's "Talk to Your Graph" (TTYG) feature, backed by the project's
Azure OpenAI resource. GraphDB Desktop couldn't reliably call that Azure endpoint, so this
package replaces it with a self-contained alternative: an embedded [pyoxigraph](https://pyoxigraph.readthedocs.io/)
triplestore instead of a GraphDB server, and a small hand-rolled pipeline instead of GraphDB's
built-in reasoning + chat agent.

GraphDB's `owl-horst` reasoner would normally infer things like reverse-direction properties
(`hasMaterial` → `isMaterialOf`) live, at query time. Since pyoxigraph doesn't reason, this
package **materializes** those entailments once, up front: `build_store.py` loads the RDF into
[rdflib](https://rdflib.readthedocs.io/), runs a full OWL-RL deductive closure over it with
[owlrl](https://owl-rl.readthedocs.io/), and loads the closed graph into the pyoxigraph store — see
[`build_store.py`](#build_storepy) below.

## Setup

From the repository root, using the project's existing `.venv`:

```bash
.venv/Scripts/python.exe -m pip install -r chatbot/requirements.txt
```

Set your Azure OpenAI API key (the endpoint is hardcoded in `llm_client.py`, matching the working
pattern in the repo's local `azure.test.py` scratch file). The deployment name defaults to
`gpt-5.4-mini` there too, but can be overridden with `AZURE_OPENAI_DEPLOYMENT` without touching
code:

```bash
export AZURE_OPENAI_API_KEY="..."          # bash
$env:AZURE_OPENAI_API_KEY = "..."          # PowerShell

# optional, only if you want a different deployment than the gpt-5.4-mini default
export AZURE_OPENAI_DEPLOYMENT="..."       # bash
$env:AZURE_OPENAI_DEPLOYMENT = "..."       # PowerShell
```

## Usage

### 1. Build the triplestore (once, or whenever the RDF source files change)

```bash
python -m chatbot.build_store [--store-path chatbot/store] [--rebuild]
```

Loads `m150-onto.rdf` and `m150-onto-parsed-DWA.rdf` from the repo root into an rdflib graph, runs
a full OWL-RL deductive closure over it (`owlrl.DeductiveClosure(owlrl.OWLRL_Semantics)`), and
loads the closed graph into a persistent pyoxigraph store at `chatbot/store/` (gitignored — it's a
derived build artifact, regenerable in seconds). This gets general entailment (subclass reasoning,
`owl:inverseOf`, `owl:SymmetricProperty`, `owl:TransitiveProperty`, `owl:equivalentProperty`, etc.)
for free instead of hand-coding each axiom type. Prints before/after triple counts, plus two
sanity-check counts worth reading before trusting a rebuilt store:

- **Fabricated triples stripped**: `hasPipeSectionTopNodeDesignation`/
  `hasPipeSectionBottomNodeDesignation` are declared in a way that, under full OWL-RL closure,
  would fabricate backwards `Node → PipeSection` triples (see "Known limitations" below) — these
  are detected and removed after closure.
- **Non-reflexive `owl:sameAs` triples**: OWL-RL axiomatically asserts `x owl:sameAs x` for every
  term (expected noise, not printed), but a triple where the two sides differ means two *distinct*
  individuals got merged — e.g. an `owl:FunctionalProperty` with two different values for one
  subject. The build prints these instead of silently trusting the closure.

Pass `--rebuild` to delete and recreate the store from scratch (safe to omit — loading is additive
and safe to re-run on an existing store, though a full `--rebuild` is the only way to drop triples
whose source data changed or was removed).

### 2. Ask questions

```bash
python -m chatbot.repl
```

Startup shows a banner with a mascot, the auto-detected model name (read from `llm_client.py`,
overridable via `AZURE_OPENAI_DEPLOYMENT`), and the available commands (`:verbose`, `:history`,
`:help`, `exit`/`quit`). The transcript below is the same conversation content, rendered with
color in an actual terminal:

```
> What material is pipe section 1204015?

Pipe section 1204015 is made of stoneware (Steinzeug).

> :verbose
verbose = True

> Who inspected pipe section 1204015?

[SPARQL]
PREFIX m150: <https://l-jamora.github.io/m150-onto#>
SELECT ?inspection ?person WHERE {
  ?inspection m150:inspects m150:Beispiel_PipeSection_1204015 .
  ?inspection m150:hasInspector ?person .
}

[bindings]
[{'inspection': '...Beispiel_Inspection_1204015', 'person': '...Beispiel_Person_H_Potter'}]

Pipe section 1204015 was inspected by H. Potter.
```

Type `exit`, `quit`, or Ctrl-C to leave.

### Example questions to try

- "What material is pipe section 1204015?"
- "Who inspected pipe section 1204015?"
- "What pipe sections connect to pipe section 1204015?" (network topology is sparse in this
  demo dataset, so this is answered via shared node-ID joins — see below)
- "List the condition findings for pipe section 1204015 with their DWA codes and descriptions."
- "Where should a crew go first?" / prioritization-style questions — the ontology has no
  built-in severity/priority field, so the model reasons from condition codes and text and
  should say explicitly that it's approximating.

## How it works

| File | Purpose |
|------|---------|
| `build_store.py` | Loads the RDF, runs the OWL-RL closure into `chatbot/store/`. Run this first. |
| `schema_context.py` | System prompts and a few-shot NL→SPARQL example set. The full `m150:` property list is auto-generated straight from `m150-onto.rdf` at import time (`_build_property_reference()`), so a real property can never be missing from the prompt — only the handful of "don't confuse this with X" gotchas and the few-shot examples need hand maintenance now. |
| `schema_validate.py` | Checks a generated query's predicates against the real property set (via rdflib's SPARQL algebra, not regex) and builds a "did you mean X?" retry note for any that don't exist — catches the class of bug where the model guesses a plausible but nonexistent property name and it silently returns empty `OPTIONAL` results instead of erroring. |
| `llm_client.py` | Thin `AzureOpenAI` wrapper — `generate_sparql()` and `compose_answer()`. |
| `sparql_pipeline.py` | Orchestrates one question end-to-end: generate SPARQL → validate predicates (retry with a specific hint if any are unknown) → run it → retry once on error or empty results → compose the final answer. |
| `repl.py` | The CLI loop (`python -m chatbot.repl`). |
| `ui.py` | `rich`-based terminal styling — startup/`:help` banner, mascot, colored prompt/labels. |
| `eval.py` | Regression eval built from real demonstration questions (`python -m chatbot.eval`). Makes real Azure calls — run it after touching `schema_context.py`, `sparql_pipeline.py`, or `schema_validate.py` instead of hand-testing one question at a time in the REPL. |

Each question can cost up to **4 Azure OpenAI calls** in the worst case (generate SPARQL,
compose answer, one retry of each) — worth knowing if you're watching an Azure billing
dashboard.

### Key ontology rules baked into the prompts

- **Reference values (Material, SewerType, Shape, NodeType, etc.) are individuals, not
  classes.** Correct: `?pipe m150:hasMaterial m150:M150_RT105_STZ`. Wrong:
  `?pipe a m150:Concrete` — this silently returns nothing.
- Most `hasX` properties are single-valued; `flowsTo`, `flowsFrom`, `connectedWith`,
  `inspects`/`inspectedIn`, `isChildOf`/`isParentOf`, `renders`/`renderedBy` are multi-valued.
- `flowsTo`/`connectedWith` prompt guidance still tells the model to derive pipe-section
  connectivity by joining on shared node IDs via `hasPipeSectionTopNodeDesignation` /
  `hasPipeSectionBottomNodeDesignation`, rather than querying `connectedWith` directly. This was
  written when `connectedWith` was empty; since the OWL-RL closure in `build_store.py` started
  populating it (106 triples in the current demo data, via the `equivalentProperty`/
  `subPropertyOf`/`TransitiveProperty` chain from real `hasPipeSectionTopNodeDesignation`/
  `BottomNodeDesignation` data), querying `connectedWith` directly may now work too — this hasn't
  been re-verified against the prompt/few-shot examples in `schema_context.py`.
- Individuals are prefixed `Beispiel_` (German "example") — a placeholder-data marker from the
  XML parser (`ontoparser.parser.INDIVIDUAL_PREFIX`), stripped from user-facing answers.

## Known limitations

- `hasPipeSectionTopNodeDesignation`/`hasPipeSectionBottomNodeDesignation` are declared
  `owl:inverseOf` in the ontology, but this is a known modeling bug (both properties actually go
  `PipeSection → Node`, see `CLAUDE.md`). Removing just that one bad `owl:inverseOf` triple isn't
  enough under full OWL-RL closure: both properties are also separately `owl:equivalentProperty`
  to `flowsTo`/`flowsFrom`, and `flowsFrom` is correctly `owl:inverseOf` `flowsTo` — chaining those
  three individually-correct axioms still fabricates the same backwards `Node → PipeSection`
  triples. `build_store.py` instead snapshots these two predicates before closure and strips any
  triple the reasoner added to them afterward — don't "fix" this by asserting a correct inverse
  pair instead; that reintroduces the fabrication via the equivalence chain.
- `owl:TransitiveProperty` closure on `connectedWith` is now handled generically by the OWL-RL
  closure (no more hand-coded no-op) — it picks up the `equivalentProperty`/`subPropertyOf` chain
  from real `hasPipeSectionTopNodeDesignation`/`BottomNodeDesignation` data.
- No automated test suite covers the LLM-in-the-loop parts (nondeterministic, costs real Azure
  calls). Verify manually against the example questions above after any change to
  `schema_context.py` or `build_store.py`.
- The Azure endpoint is hardcoded in `llm_client.py`; the API key and (optionally) the deployment
  name (`AZURE_OPENAI_DEPLOYMENT`) are read from the environment.
