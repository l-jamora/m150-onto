#!/usr/bin/env python3
"""
Add OWL property characteristics to M150 object properties.

Adds owl:FunctionalProperty, owl:AsymmetricProperty, and owl:IrreflexiveProperty
to every ObjectProperty in the ontology, except for the nine properties in
EXCEPTIONS which have intentionally different characteristics.

Usage:
    python 4_add_property_characteristics.py [--ontology m150-onto.rdf] [--output m150-onto.rdf] [--dry-run]
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

EXCEPTIONS = {
    "inspectedIn", "inspects",
    "isChildOf", "isParentOf",
    "renderedBy", "renders",
    "connectedWith", "flowsFrom", "flowsTo",
}

CHARACTERISTICS = [
    "http://www.w3.org/2002/07/owl#FunctionalProperty",
    "http://www.w3.org/2002/07/owl#AsymmetricProperty",
    "http://www.w3.org/2002/07/owl#IrreflexiveProperty",
]

NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "owl": "http://www.w3.org/2002/07/owl#",
}


def local_name(iri: str) -> str:
    """Extract the local name from an IRI (after # or last /)."""
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.split("/")[-1]


def existing_types(element) -> set:
    """Return the set of rdf:resource values already declared as rdf:type on this element."""
    rdf_type_tag = f"{{{NS['rdf']}}}type"
    rdf_resource_attr = f"{{{NS['rdf']}}}resource"
    return {
        child.get(rdf_resource_attr)
        for child in element
        if child.tag == rdf_type_tag and child.get(rdf_resource_attr)
    }


def process(ontology_path: Path, output_path: Path, dry_run: bool) -> None:
    ET.register_namespace("rdf", NS["rdf"])
    ET.register_namespace("owl", NS["owl"])

    # Preserve namespace declarations by parsing with full namespace awareness
    tree = ET.parse(ontology_path)
    root = tree.getroot()

    owl_object_property_tag = f"{{{NS['owl']}}}ObjectProperty"
    rdf_about_attr = f"{{{NS['rdf']}}}about"
    rdf_type_tag = f"{{{NS['rdf']}}}type"
    rdf_resource_attr = f"{{{NS['rdf']}}}resource"

    modified = 0
    skipped_exceptions = 0

    for prop in root.iter(owl_object_property_tag):
        about = prop.get(rdf_about_attr, "")
        name = local_name(about)

        if name in EXCEPTIONS:
            skipped_exceptions += 1
            continue

        current_types = existing_types(prop)
        added = []
        for characteristic in CHARACTERISTICS:
            if characteristic not in current_types:
                el = ET.SubElement(prop, rdf_type_tag)
                el.set(rdf_resource_attr, characteristic)
                added.append(characteristic.split("#")[-1])

        if added:
            modified += 1
            if dry_run:
                print(f"  Would add to {name}: {', '.join(added)}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Results:")
    print(f"  Properties modified: {modified}")
    print(f"  Exception properties skipped: {skipped_exceptions}")

    if not dry_run:
        # Preserve the original XML declaration and register all namespaces
        tree.write(output_path, xml_declaration=True, encoding="utf-8")
        print(f"  Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ontology", default="m150-onto.rdf", help="Input ontology RDF file")
    parser.add_argument("--output", default=None, help="Output file (defaults to overwriting input)")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without saving")
    args = parser.parse_args()

    ontology_path = Path(args.ontology)
    output_path = Path(args.output) if args.output else ontology_path

    if not ontology_path.exists():
        print(f"Error: ontology file not found: {ontology_path}")
        raise SystemExit(1)

    process(ontology_path, output_path, args.dry_run)


if __name__ == "__main__":
    main()
