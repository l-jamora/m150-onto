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
package **materializes** those entailments once, up front, into the store itself — see
[`build_store.py`](#build_storepy) below.

## Setup

From the repository root, using the project's existing `.venv`:

```bash
.venv/Scripts/python.exe -m pip install -r chatbot/requirements.txt
```

Set your Azure OpenAI API key (the endpoint and deployment name are already hardcoded in
`llm_client.py`, matching the working pattern in the repo's local `azure.test.py` scratch file):

```bash
export AZURE_OPENAI_API_KEY="..."          # bash
$env:AZURE_OPENAI_API_KEY = "..."          # PowerShell
```

## Usage

### 1. Build the triplestore (once, or whenever the RDF source files change)

```bash
python -m chatbot.build_store [--store-path chatbot/store] [--rebuild]
```

Loads `m150-onto.rdf` and `m150-onto-parsed-DWA.rdf` from the repo root into a persistent store
at `chatbot/store/` (gitignored — it's a derived build artifact, regenerable in seconds), then
materializes `owl:inverseOf` and `owl:SymmetricProperty` entailments so reverse-direction
queries work. Prints before/after triple counts and a per-pair delta so you can sanity-check the
materialization. Pass `--rebuild` to delete and recreate the store from scratch (safe to omit —
the materialization step is idempotent and safe to re-run on an existing store).

### 2. Ask questions

```bash
python -m chatbot.repl
```

```
M150-Onto chatbot. Type a question, ':verbose' to toggle SPARQL/bindings output, 'exit' to quit.

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
| `build_store.py` | Loads the RDF, materializes inverse/symmetric closure into `chatbot/store/`. Run this first. |
| `schema_context.py` | System prompts and a few-shot NL→SPARQL example set, adapted from the ontology-specific rules originally drafted for GraphDB's TTYG (`TTYG-agent-instructions-draft.md` at the repo root). |
| `llm_client.py` | Thin `AzureOpenAI` wrapper — `generate_sparql()` and `compose_answer()`. |
| `sparql_pipeline.py` | Orchestrates one question end-to-end: generate SPARQL → run it → retry once on error or empty results → compose the final answer. |
| `repl.py` | The CLI loop (`python -m chatbot.repl`). |

Each question can cost up to **4 Azure OpenAI calls** in the worst case (generate SPARQL,
compose answer, one retry of each) — worth knowing if you're watching an Azure billing
dashboard.

### Key ontology rules baked into the prompts

- **Reference values (Material, SewerType, Shape, NodeType, etc.) are individuals, not
  classes.** Correct: `?pipe m150:hasMaterial m150:M150_RT105_STZ`. Wrong:
  `?pipe a m150:Concrete` — this silently returns nothing.
- Most `hasX` properties are single-valued; `flowsTo`, `flowsFrom`, `connectedWith`,
  `inspects`/`inspectedIn`, `isChildOf`/`isParentOf`, `renders`/`renderedBy` are multi-valued.
- `flowsTo`/`connectedWith` are essentially unpopulated in this demo dataset. Pipe-section
  connectivity is instead derived by joining on shared node IDs via
  `hasPipeSectionTopNodeDesignation` / `hasPipeSectionBottomNodeDesignation`.
- Individuals are prefixed `Beispiel_` (German "example") — a placeholder-data marker from the
  XML parser (`ontoparser.parser.INDIVIDUAL_PREFIX`), stripped from user-facing answers.

## Known limitations

- `hasPipeSectionTopNodeDesignation`/`hasPipeSectionBottomNodeDesignation` are declared
  `owl:inverseOf` in the ontology, but this is a known modeling bug (both properties actually go
  `PipeSection → Node`, see `CLAUDE.md`). `build_store.py` deliberately excludes this pair from
  materialization — don't "fix" this by adding it back.
- `owl:TransitiveProperty` closure on `connectedWith` is not materialized. It's currently
  empty/near-empty in the demo data, so there's nothing to close over; revisit if `ontoparser`
  starts populating `flowsTo`/`connectedWith` for real.
- No automated test suite covers the LLM-in-the-loop parts (nondeterministic, costs real Azure
  calls). Verify manually against the example questions above after any change to
  `schema_context.py` or `build_store.py`.
- The Azure endpoint and deployment name are hardcoded in `llm_client.py`; only the API key is
  read from the environment.
