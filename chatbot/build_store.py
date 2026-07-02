"""Builds the local pyoxigraph triplestore for the M150-Onto chatbot.

Loads the base ontology and the parsed example instance data, then
materializes the entailments GraphDB's owl-horst reasoner used to provide
live: owl:inverseOf and owl:SymmetricProperty. This makes reverse-direction
SPARQL queries (e.g. "who inspected X" via isInspectorIn) return results
without needing a reasoning-capable store at query time.

Run: python -m chatbot.build_store [--store-path chatbot/store] [--rebuild]
"""

import argparse
import shutil
from pathlib import Path

import pyoxigraph

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = REPO_ROOT / "m150-onto.rdf"
INSTANCE_DATA_PATH = REPO_ROOT / "m150-onto-parsed-DWA.rdf"
DEFAULT_STORE_PATH = Path(__file__).resolve().parent / "store"

BASE_IRI = "https://l-jamora.github.io/m150-onto"

OWL = "http://www.w3.org/2002/07/owl#"

# hasPipeSectionBottomNodeDesignation is declared owl:inverseOf
# hasPipeSectionTopNodeDesignation, but both properties actually go
# PipeSection -> Node (see CLAUDE.md "Known limitations and future work").
# Materializing this pair would fabricate a nonsensical Node -> PipeSection
# triple, so it is excluded by name rather than discovered generically.
EXCLUDED_INVERSE_PAIRS = frozenset(
    {
        frozenset(
            {
                "hasPipeSectionTopNodeDesignation",
                "hasPipeSectionBottomNodeDesignation",
            }
        )
    }
)


def _local_name(iri: str) -> str:
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _discover_inverse_pairs(store: pyoxigraph.Store) -> list[tuple[str, str]]:
    """Returns unordered (p, inv) IRI pairs declared via owl:inverseOf, deduped."""
    rows = store.query(
        "SELECT ?p ?inv WHERE { ?p owl:inverseOf ?inv }",
        prefixes={"owl": OWL},
    )
    seen: set[frozenset[str]] = set()
    pairs: list[tuple[str, str]] = []
    for row in rows:
        p, inv = row["p"].value, row["inv"].value
        key = frozenset({p, inv})
        if key in seen:
            continue
        seen.add(key)
        if frozenset({_local_name(p), _local_name(inv)}) in EXCLUDED_INVERSE_PAIRS:
            print(f"  skipping excluded pair: {_local_name(p)} / {_local_name(inv)}")
            continue
        pairs.append((p, inv))
    return pairs


def _discover_symmetric_properties(store: pyoxigraph.Store) -> list[str]:
    rows = store.query(
        "SELECT ?p WHERE { ?p a owl:SymmetricProperty }",
        prefixes={"owl": OWL},
    )
    return [row["p"].value for row in rows]


def _materialize_inverse_direction(store: pyoxigraph.Store, p: str, inv: str) -> int:
    """INSERTs the missing <inv> triples implied by existing <p> triples. Idempotent."""
    before = len(store)
    store.update(
        f"INSERT {{ ?o <{inv}> ?s }} "
        f"WHERE {{ ?s <{p}> ?o . FILTER NOT EXISTS {{ ?o <{inv}> ?s }} }}"
    )
    return len(store) - before


def _materialize_symmetric(store: pyoxigraph.Store, p: str) -> int:
    before = len(store)
    store.update(
        f"INSERT {{ ?o <{p}> ?s }} "
        f"WHERE {{ ?s <{p}> ?o . FILTER NOT EXISTS {{ ?o <{p}> ?s }} }}"
    )
    return len(store) - before


def build(store_path: Path, rebuild: bool) -> None:
    if rebuild and store_path.exists():
        shutil.rmtree(store_path)

    store = pyoxigraph.Store(str(store_path))

    print(f"Loading {ONTOLOGY_PATH.name} ...")
    store.load(path=str(ONTOLOGY_PATH), format=pyoxigraph.RdfFormat.RDF_XML, base_iri=BASE_IRI)
    print(f"Loading {INSTANCE_DATA_PATH.name} ...")
    store.load(
        path=str(INSTANCE_DATA_PATH), format=pyoxigraph.RdfFormat.RDF_XML, base_iri=BASE_IRI
    )

    before = len(store)
    print(f"\nTriples after load: {before}")

    print("\nMaterializing owl:inverseOf pairs...")
    pairs = _discover_inverse_pairs(store)
    for p, inv in pairs:
        delta_fwd = _materialize_inverse_direction(store, p, inv)
        delta_bwd = _materialize_inverse_direction(store, inv, p)
        print(f"  {_local_name(p)} <-> {_local_name(inv)}: +{delta_fwd} / +{delta_bwd}")

    print("\nMaterializing owl:SymmetricProperty closure...")
    for p in _discover_symmetric_properties(store):
        delta = _materialize_symmetric(store, p)
        print(f"  {_local_name(p)}: +{delta}")

    # owl:TransitiveProperty closure (connectedWith) is intentionally NOT
    # materialized: connectedWith has 0 triples and flowsTo has only 4, all on
    # disconnected placeholder individuals unrelated to the real demo data.
    # The populated topology chain (1204015 -> 1204014 -> ...) only exists via
    # hasPipeSectionTopNodeDesignation/BottomNodeDesignation node-ID joins.
    # Revisit if ontoparser starts populating flowsTo/connectedWith for real.

    after = len(store)
    print(f"\nTriples after materialization: {after} (+{after - before})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-path", type=Path, default=DEFAULT_STORE_PATH)
    parser.add_argument("--rebuild", action="store_true", help="delete and recreate the store")
    args = parser.parse_args()
    build(args.store_path, args.rebuild)


if __name__ == "__main__":
    main()
