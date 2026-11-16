#!/usr/bin/env python3
"""
Add rdfs:range axioms to owl:DatatypeProperty declarations in the M150 ontology.

Reads property-to-XSD-type mappings from a CSV file and inserts missing
rdfs:range elements into the RDF/XML ontology file. Properties that already
have a range are skipped with a warning.

Usage:
    python 5_add_datatype_property_ranges.py [--ontology m150-onto.rdf] [--csv dataproperties.csv] [--output <path>] [--dry-run]
"""

import argparse
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "owl":  "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd":  "http://www.w3.org/2001/XMLSchema#",
}

XSD_NS = "http://www.w3.org/2001/XMLSchema#"

SCRIPT_DIR = Path(__file__).parent
DEFAULT_ONTOLOGY = SCRIPT_DIR.parent / "m150-onto.rdf"
DEFAULT_CSV = SCRIPT_DIR / "dataproperties.csv"


def local_name(iri: str) -> str:
    """Extract local name from an IRI (after # or last /)."""
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.split("/")[-1]


def load_csv(csv_path: Path) -> dict:
    """Load CSV into {propertyName: xsdType} dict."""
    mapping = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                mapping[row[0].strip()] = row[1].strip()
    return mapping


def existing_range(element) -> str | None:
    """Return the rdf:resource value of an existing rdfs:range child, or None."""
    rdfs_range_tag = f"{{{NS['rdfs']}}}range"
    rdf_resource_attr = f"{{{NS['rdf']}}}resource"
    for child in element:
        if child.tag == rdfs_range_tag:
            return child.get(rdf_resource_attr)
    return None


def process(ontology_path: Path, csv_path: Path, output_path: Path, dry_run: bool) -> None:
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)

    csv_mapping = load_csv(csv_path)
    print(f"Loaded {len(csv_mapping)} properties from {csv_path}")

    tree = ET.parse(ontology_path)
    root = tree.getroot()

    owl_datatype_property_tag = f"{{{NS['owl']}}}DatatypeProperty"
    rdf_about_attr = f"{{{NS['rdf']}}}about"
    rdfs_range_tag = f"{{{NS['rdfs']}}}range"
    rdf_resource_attr = f"{{{NS['rdf']}}}resource"

    added = 0
    skipped_existing = 0
    not_in_csv = 0
    csv_hits = set()

    for prop in root.iter(owl_datatype_property_tag):
        about = prop.get(rdf_about_attr, "")
        name = local_name(about)

        if name not in csv_mapping:
            not_in_csv += 1
            continue

        csv_hits.add(name)
        xsd_type = csv_mapping[name]
        range_uri = XSD_NS + xsd_type.split(":")[-1]

        current_range = existing_range(prop)
        if current_range is not None:
            current_local = local_name(current_range)
            print(f"  SKIP {name}: already has range xsd:{current_local} (CSV says {xsd_type})")
            skipped_existing += 1
            continue

        if dry_run:
            print(f"  Would add to {name}: rdfs:range {xsd_type}")
        else:
            el = ET.SubElement(prop, rdfs_range_tag)
            el.set(rdf_resource_attr, range_uri)
        added += 1

    missing_from_rdf = set(csv_mapping.keys()) - csv_hits - {
        name for prop in root.iter(owl_datatype_property_tag)
        if (name := local_name(prop.get(rdf_about_attr, ""))) not in csv_mapping
        # only report names that were in CSV but never encountered in the RDF
    }
    # Simpler: recompute which CSV entries were never seen
    all_rdf_names = {
        local_name(prop.get(rdf_about_attr, ""))
        for prop in root.iter(owl_datatype_property_tag)
    }
    missing_from_rdf = set(csv_mapping.keys()) - all_rdf_names

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Results:")
    print(f"  Ranges {'would be ' if dry_run else ''}added:          {added}")
    print(f"  Skipped (existing range):  {skipped_existing}")
    print(f"  In RDF but not in CSV:     {not_in_csv}")
    if missing_from_rdf:
        print(f"  In CSV but not in RDF ({len(missing_from_rdf)}): {', '.join(sorted(missing_from_rdf))}")

    if not dry_run:
        tree.write(output_path, xml_declaration=True, encoding="utf-8")
        print(f"  Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ontology", default=str(DEFAULT_ONTOLOGY), help="Input ontology RDF file")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="CSV file with property-to-XSD-type mappings")
    parser.add_argument("--output", default=None, help="Output file (defaults to overwriting input)")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without saving")
    args = parser.parse_args()

    ontology_path = Path(args.ontology)
    csv_path = Path(args.csv)
    output_path = Path(args.output) if args.output else ontology_path

    if not ontology_path.exists():
        print(f"Error: ontology file not found: {ontology_path}")
        raise SystemExit(1)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        raise SystemExit(1)

    process(ontology_path, csv_path, output_path, args.dry_run)


if __name__ == "__main__":
    main()
