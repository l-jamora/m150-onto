"""Builds the local pyoxigraph triplestore for the M150-Onto chatbot.

Loads the base ontology and the parsed example instance data into an rdflib
graph, runs a full OWL-RL deductive closure over it (owlrl), and loads the
closed graph into an embedded pyoxigraph store. This replaces GraphDB's
owl-horst reasoner, which used to provide entailments like owl:inverseOf and
owl:SymmetricProperty live, at query time -- pyoxigraph has no reasoning of
its own, so everything has to be materialized once, up front.

Run: python -m chatbot.build_store [--store-path chatbot/store] [--rebuild]
"""

import argparse
import shutil
from pathlib import Path

import owlrl
import pyoxigraph
import rdflib
from rdflib.namespace import OWL

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = REPO_ROOT / "m150-onto.rdf"
INSTANCE_DATA_PATH = REPO_ROOT / "m150-onto-parsed-DWA.rdf"
DEFAULT_STORE_PATH = Path(__file__).resolve().parent / "store"

BASE_IRI = "https://l-jamora.github.io/m150-onto"
M150 = rdflib.Namespace(BASE_IRI + "#")

# hasPipeSectionBottomNodeDesignation is declared owl:inverseOf
# hasPipeSectionTopNodeDesignation, but both properties actually go
# PipeSection -> Node (see CLAUDE.md "Known limitations"). Under a real OWL-RL
# closure, removing just that one inverseOf triple is NOT enough: both
# properties are also separately declared owl:equivalentProperty to
# flowsTo/flowsFrom, and flowsFrom is correctly owl:inverseOf flowsTo. Chaining
# those three individually-correct axioms (equivalentProperty -> inverseOf ->
# equivalentProperty back) still fabricates the same wrong Node -> PipeSection
# triples even with the direct bad triple gone. So instead of editing axioms,
# these two predicates are snapshotted before closure and any new triple the
# reasoner adds on them is stripped afterward -- this keeps every other
# consequence of the equivalentProperty/inverseOf chain (flowsTo/flowsFrom/
# connectedWith still get populated from the real PipeSection -> Node data)
# while refusing to materialize new data for the two known-bad predicates.
EXCLUDED_PREDICATES = frozenset(
    {
        M150.hasPipeSectionTopNodeDesignation,
        M150.hasPipeSectionBottomNodeDesignation,
    }
)


def _run_closure(graph: rdflib.Graph) -> tuple[int, int]:
    """Runs OWL-RL closure in place. Returns (added, stripped) triple counts."""
    pre_excluded = {
        (s, p, o) for s, p, o in graph if p in EXCLUDED_PREDICATES
    }

    before = len(graph)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(graph)
    added = len(graph) - before

    stripped = 0
    for s, p, o in list(graph):
        if p in EXCLUDED_PREDICATES and (s, p, o) not in pre_excluded:
            graph.remove((s, p, o))
            stripped += 1

    return added, stripped


def build(store_path: Path, rebuild: bool) -> None:
    if rebuild and store_path.exists():
        shutil.rmtree(store_path)

    graph = rdflib.Graph()
    print(f"Loading {ONTOLOGY_PATH.name} ...")
    graph.parse(str(ONTOLOGY_PATH), format="xml", publicID=BASE_IRI)
    print(f"Loading {INSTANCE_DATA_PATH.name} ...")
    graph.parse(str(INSTANCE_DATA_PATH), format="xml", publicID=BASE_IRI)

    before = len(graph)
    print(f"\nTriples after load: {before}")

    print("\nRunning OWL-RL deductive closure...")
    added, stripped = _run_closure(graph)
    print(f"  closure added: +{added}")
    print(f"  stripped fabricated hasPipeSectionTopNode/BottomNodeDesignation triples: -{stripped}")

    # OWL-RL's eq-ref rule axiomatically asserts x owl:sameAs x for every term, so
    # reflexive pairs are expected noise, not a signal. A non-reflexive pair (s != o)
    # means two *distinct* individuals were merged -- e.g. a FunctionalProperty with
    # two different values for one subject -- which is worth a human look.
    non_reflexive_same_as = [
        (s, o) for s, _, o in graph.triples((None, OWL.sameAs, None)) if s != o
    ]
    print(f"  non-reflexive owl:sameAs triples after closure: {len(non_reflexive_same_as)}")
    if non_reflexive_same_as:
        print("  WARNING: distinct individuals were merged -- a FunctionalProperty may have")
        print("  two values for one individual, which can conflate unrelated data:")
        for s, o in non_reflexive_same_as:
            print(f"    {s} owl:sameAs {o}")

    # owlrl's datatype axioms produce generalized-RDF triples with a Literal as
    # subject (e.g. "26.0"^^xsd:decimal owl:sameAs "26.0"^^xsd:decimal), which is
    # not valid strict RDF -- literals can't be subjects. These carry no useful
    # information (self-identity/type-membership of a literal value, not of an
    # individual in our data) and pyoxigraph's N-Triples parser correctly rejects
    # them, so drop them before serializing.
    literal_subject_triples = [t for t in graph if isinstance(t[0], rdflib.Literal)]
    for t in literal_subject_triples:
        graph.remove(t)
    print(f"  dropped generalized-RDF (literal-subject) triples: -{len(literal_subject_triples)}")

    after_closure = len(graph)
    print(f"\nTriples after closure: {after_closure} (+{after_closure - before})")

    store = pyoxigraph.Store(str(store_path))
    store.load(
        input=graph.serialize(format="nt"),
        format=pyoxigraph.RdfFormat.N_TRIPLES,
    )
    print(f"Triples loaded into store: {len(store)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-path", type=Path, default=DEFAULT_STORE_PATH)
    parser.add_argument("--rebuild", action="store_true", help="delete and recreate the store")
    args = parser.parse_args()
    build(args.store_path, args.rebuild)


if __name__ == "__main__":
    main()
