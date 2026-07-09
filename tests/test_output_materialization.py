import hashlib
import sys
from pathlib import Path

import pytest
import rdflib
from rdflib.namespace import OWL, RDF

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ontoparser.parser import DEFAULT_ONTOLOGY, OUTPUT_ONTOLOGY_IRI, M150XmlParser

XML_PATH = REPO_ROOT / "xml" / "DWA M 150 Beispiel 04_2010 Typ B .xml"


@pytest.fixture(scope="module")
def parser_output(tmp_path_factory):
    """Runs the parser once for the whole module -- owlready2's default World is a
    process-global singleton, so re-running load_ontology()/parse() per test would let
    individuals created by an earlier test bleed into a later test's "before" snapshot."""
    hash_before = hashlib.sha256(DEFAULT_ONTOLOGY.read_bytes()).hexdigest()

    output_path = tmp_path_factory.mktemp("ontoparser_output") / "test-output.rdf"
    parser_obj = M150XmlParser(XML_PATH, DEFAULT_ONTOLOGY, output_path)
    parser_obj.load_ontology()
    parser_obj.parse()
    parser_obj.save()

    hash_after = hashlib.sha256(DEFAULT_ONTOLOGY.read_bytes()).hexdigest()
    return output_path, hash_before, hash_after


def test_output_imports_base_ontology_and_skips_tbox_duplication(parser_output):
    output_path, _, _ = parser_output

    out_graph = rdflib.Graph()
    out_graph.parse(str(output_path), format="xml")

    base_onto_iri = rdflib.URIRef("https://l-jamora.github.io/m150-onto")
    output_onto_iri = rdflib.URIRef(OUTPUT_ONTOLOGY_IRI)

    assert (output_onto_iri, OWL.imports, base_onto_iri) in out_graph

    pipe_section_cls = rdflib.URIRef("https://l-jamora.github.io/m150-onto#PipeSection")
    assert (pipe_section_cls, RDF.type, OWL.Class) not in out_graph, (
        "base ontology's PipeSection class must not be redeclared in the output"
    )

    individuals_of_pipe_section = list(out_graph.subjects(RDF.type, pipe_section_cls))
    assert individuals_of_pipe_section, "expected at least one new PipeSection individual in the output"


def test_output_declares_no_base_tbox_classes(parser_output):
    """The output should never redeclare the base ontology's schema -- only reference it by
    IRI. A byte-size comparison isn't a reliable proxy (a large XML input can legitimately
    produce more instance data than the base ontology's own schema triples), so this checks
    structurally: zero owl:Class declarations, and no more than a couple of dynamically
    created schema-drift properties (see ontoparser.parser._get_property's fallback branch)."""
    output_path, _, _ = parser_output

    out_graph = rdflib.Graph()
    out_graph.parse(str(output_path), format="xml")

    assert list(out_graph.subjects(RDF.type, OWL.Class)) == []
    new_properties = list(out_graph.subjects(RDF.type, OWL.ObjectProperty)) + list(
        out_graph.subjects(RDF.type, OWL.DatatypeProperty)
    )
    assert len(new_properties) <= 2, f"unexpectedly many new property declarations: {new_properties}"


def test_base_ontology_file_is_not_modified_on_disk(parser_output):
    _, hash_before, hash_after = parser_output
    assert hash_before == hash_after
