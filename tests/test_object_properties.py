import csv
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CSV_PATH = REPO_ROOT / "dwa" / "mapping_DWA-to-m150onto.csv"
RDF_PATH = REPO_ROOT / "m150-onto.rdf"

OWL_NS = "http://www.w3.org/2002/07/owl#"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


def local_name(iri: str) -> str:
    return iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def test_all_mapped_properties_exist_in_ontology():
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        mapped = {
            row["Corresponding Ontology Object Property"].strip()
            for row in reader
            if row["Corresponding Ontology Object Property"].strip()
            and not row["Corresponding Ontology Object Property"].strip().startswith("Annotation:")
        }

    tree = ET.parse(RDF_PATH)
    root = tree.getroot()
    declared = {
        local_name(el.get(f"{{{RDF_NS}}}about"))
        for el in root.iter(f"{{{OWL_NS}}}ObjectProperty")
        if el.get(f"{{{RDF_NS}}}about")
    }

    missing = mapped - declared
    assert not missing, (
        f"{len(missing)} object propert{'y' if len(missing)==1 else 'ies'} "
        f"in the CSV are not declared in M150-Onto.rdf:\n"
        + "\n".join(sorted(missing))
    )
