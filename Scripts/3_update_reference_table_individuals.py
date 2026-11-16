#!/usr/bin/env python3
"""
Update M150 Ontology Reference Table Individuals

This script reads a CSV file with reference table data and updates the corresponding
individuals in an OWL/RDF ontology file. Each individual is renamed following the
naming convention: M150_RTXYZ_[suffix], where RTXYZ is the reference table number
and suffix is the letter identifier.

Usage:
    python 3_update_reference_table_individuals.py <csv_file> [rdf_file]
    
Example:
    python 3_update_reference_table_individuals.py reference_data.csv m150-onto.rdf
"""

import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Define XML namespaces
NAMESPACES = {
    '': 'https://l-jamora.github.io/m150-onto/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'owl': 'http://www.w3.org/2002/07/owl#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'term': 'http://purl.org/dc/terms/',
    'vann': 'http://purl.org/vocab/vann/'
}

# Register namespaces to preserve prefixes in output
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

XMLNS_NAMESPACE = 'http://www.w3.org/2000/xmlns/'


def register_namespaces_from_root(root):
    """Register any namespace prefixes declared on the RDF root element."""
    for attr_name, uri in root.attrib.items():
        if not isinstance(attr_name, str):
            continue
        if attr_name == f'{{{XMLNS_NAMESPACE}}}':
            ET.register_namespace('', uri)
        elif attr_name.startswith(f'{{{XMLNS_NAMESPACE}}}'):
            prefix = attr_name.split('}', 1)[1]
            ET.register_namespace(prefix, uri)


def read_csv_data(csv_file):
    """Read the CSV file containing reference table data."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            individuals = []
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    individuals.append(row)
            print(f"✓ Loaded {len(individuals)} individuals from CSV (encoding: {encoding})")
            return individuals
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"✗ Error: CSV file '{csv_file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Error reading CSV: {e}")
            sys.exit(1)
    
    print(f"✗ Error: Could not decode CSV file with any supported encoding ({', '.join(encodings)})")
    sys.exit(1)


def find_individual_in_tree(root, old_name, namespace):
    """Find an individual element by its old name."""
    for elem in root.findall('.//owl:NamedIndividual', namespace):
        about = elem.get(f'{{{namespace["rdf"]}}}about')
        if about and old_name in about:
            return elem
    return None


def update_individual(elem, new_name, rt_number, rdf_type, german_label, english_label, namespace):
    """Update an individual element with new data."""
    
    # Update the rdf:about attribute and comment
    base_uri = "https://l-jamora.github.io/m150-onto/"
    new_uri = f"{base_uri}{new_name}"
    elem.set(f'{{{namespace["rdf"]}}}about', new_uri)
    
    # Update rdfs:isDefinedBy
    is_defined_by_elem = elem.find(f'rdfs:isDefinedBy', namespace)
    if is_defined_by_elem is None:
        is_defined_by_elem = ET.SubElement(elem, f'{{{namespace["rdfs"]}}}isDefinedBy')
    is_defined_by_elem.text = f"DWA-M 150 Reference Table {rt_number}"
    
    # Update rdf:type
    type_elem = elem.find(f'rdf:type', namespace)
    if type_elem is None:
        type_elem = ET.SubElement(elem, f'{{{namespace["rdf"]}}}type')
    type_elem.set(f'{{{namespace["rdf"]}}}resource', f"{base_uri}{rdf_type}")
    
    # Remove existing labels
    for label_elem in list(elem.findall(f'rdfs:label', namespace)):
        elem.remove(label_elem)
    
    # Add German label
    de_label = ET.SubElement(elem, f'{{{namespace["rdfs"]}}}label')
    de_label.set(f'{{{NAMESPACES["xml"]}}}lang', 'de')
    de_label.text = german_label
    
    # Add English label
    en_label = ET.SubElement(elem, f'{{{namespace["rdfs"]}}}label')
    en_label.set(f'{{{NAMESPACES["xml"]}}}lang', 'en')
    en_label.text = english_label


def update_rdf_file(rdf_file, csv_file):
    """Main function to update the RDF file based on CSV data."""
    
    print(f"\n{'='*60}")
    print("M150 Ontology Reference Table Individual Updater")
    print(f"{'='*60}\n")
    
    # Read CSV
    individuals = read_csv_data(csv_file)
    
    # Parse RDF file
    try:
        tree = ET.parse(rdf_file)
        root = tree.getroot()
        print(f"✓ Loaded RDF file: {rdf_file}\n")
    except FileNotFoundError:
        print(f"✗ Error: RDF file '{rdf_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error parsing RDF: {e}")
        sys.exit(1)
    
    # Register any namespaces declared on the RDF root element
    register_namespaces_from_root(root)
    
    # Process each individual
    updated_count = 0
    failed_count = 0
    
    for individual in individuals:
        old_name = individual.get('old_individual_name', '').strip()
        rt_number = individual.get('reference_table_number', '').strip()
        suffix = individual.get('suffix_letter', '').strip()
        rdf_type = individual.get('rdf_type', '').strip()
        german_label = individual.get('german_label', '').strip()
        english_label = individual.get('english_label', '').strip()
        
        # Validate required fields
        if not all([old_name, rt_number, suffix, rdf_type, german_label, english_label]):
            print(f"⚠ Skipping incomplete row: {old_name}")
            failed_count += 1
            continue
        
        # Construct new individual name
        new_name = f"M150_RT{rt_number}_{suffix}"
        
        # Find individual in RDF
        elem = find_individual_in_tree(root, old_name, NAMESPACES)
        
        if elem is not None:
            try:
                update_individual(elem, new_name, rt_number, rdf_type, german_label, english_label, NAMESPACES)
                print(f"✓ Updated: {old_name} → {new_name}")
                updated_count += 1
            except Exception as e:
                print(f"✗ Error updating {old_name}: {e}")
                failed_count += 1
        else:
            print(f"✗ Individual not found: {old_name}")
            failed_count += 1
    
    # Save updated RDF file
    try:
        tree.write(rdf_file, encoding='utf-8', xml_declaration=True)
        print(f"\n{'='*60}")
        print(f"✓ Successfully updated and saved: {rdf_file}")
        print(f"✓ Total updated: {updated_count}")
        if failed_count > 0:
            print(f"⚠ Total failed: {failed_count}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"✗ Error saving RDF file: {e}")
        sys.exit(1)


def main():
    """Entry point."""
    if len(sys.argv) < 2:
        print("Usage: python 3_update_reference_table_individuals.py <csv_file> [rdf_file]")
        print("\nArguments:")
        print("  csv_file      Path to CSV file with reference table data")
        print("  rdf_file      Path to RDF ontology file (default: m150-onto.rdf)")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    rdf_file = sys.argv[2] if len(sys.argv) > 2 else "m150-onto.rdf"
    
    # Check if files exist
    if not Path(csv_file).exists():
        print(f"✗ CSV file not found: {csv_file}")
        sys.exit(1)
    
    if not Path(rdf_file).exists():
        print(f"✗ RDF file not found: {rdf_file}")
        sys.exit(1)
    
    update_rdf_file(rdf_file, csv_file)


if __name__ == "__main__":
    main()
