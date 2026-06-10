import csv
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CSV_PATH = REPO_ROOT / "ontoparser" / "mapping_DWA-to-m150onto.csv"
RDF_PATH = REPO_ROOT / "m150-onto.rdf"

OWL_NS = "http://www.w3.org/2002/07/owl#"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


def local_name(iri: str) -> str:
    return iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def _read_csv_column(column: str) -> set:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {
            row[column].strip()
            for row in reader
            if row[column].strip() and not row[column].strip().startswith("Annotation:")
        }


def _declared_in_rdf(owl_tag: str) -> set:
    tree = ET.parse(RDF_PATH)
    root = tree.getroot()
    return {
        local_name(el.get(f"{{{RDF_NS}}}about"))
        for el in root.iter(f"{{{OWL_NS}}}{owl_tag}")
        if el.get(f"{{{RDF_NS}}}about")
    }


def test_csv_object_properties_exist_in_ontology():
    mapped = _read_csv_column("Corresponding Ontology Object Property")
    declared = _declared_in_rdf("ObjectProperty")
    missing = mapped - declared
    assert not missing, (
        f"{len(missing)} object propert{'y' if len(missing)==1 else 'ies'} "
        f"in the CSV are not declared as owl:ObjectProperty in M150-Onto.rdf:\n"
        + "\n".join(sorted(missing))
    )


def test_csv_data_properties_exist_in_ontology():
    mapped = _read_csv_column("Corresponding Ontology Data Property")
    declared = _declared_in_rdf("DatatypeProperty")
    missing = mapped - declared
    assert not missing, (
        f"{len(missing)} data propert{'y' if len(missing)==1 else 'ies'} "
        f"in the CSV are not declared as owl:DatatypeProperty in M150-Onto.rdf:\n"
        + "\n".join(sorted(missing))
    )
