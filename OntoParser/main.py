import owlready2 as owl
from xml_parser_onto import parse_xml
from pathlib import Path
from config import *
from objectproperties import OBJECT_PROPERTY_MAPPINGS
import re

# Paths (unchanged)
REPO_ROOT = Path(__file__).parent
XML_DIR = REPO_ROOT / "XML"
ONTOLOGY_DIR = REPO_ROOT / "m150-onto"
OUTPUT_DIR = REPO_ROOT / "output"
XML_PATH = XML_DIR / "DWA M 150 Beispiel 04_2010 Typ B .xml"
MAIN_ONTOLOGY_PATH = ONTOLOGY_DIR / "merged_m150-onto.rdf"
OUTPUT_ONTOLOGY_PATH = OUTPUT_DIR / "updated_M150-Onto.rdf"

OUTPUT_DIR.mkdir(exist_ok=True)
for path in [XML_PATH, MAIN_ONTOLOGY_PATH]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

owl.onto_path.append(str(ONTOLOGY_DIR))
print(f"Loading ontology from {MAIN_ONTOLOGY_PATH}")
onto = owl.get_ontology(f"file://{MAIN_ONTOLOGY_PATH}").load()
print("Ontology loaded successfully")

# Find existing classes
node_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}Node")
pipe_section_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}PipeSection")
inspection_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}Inspection")
condition_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}Condition")
measurement_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}Measurement")
geo_object_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}Object")
geo_point_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}Point")

if not all([node_class, pipe_section_class, inspection_class, condition_class, measurement_class]):
    raise ValueError("One or more ontology classes not found")

# Load object properties
object_properties = {}
for xml_key, prop_info in OBJECT_PROPERTY_MAPPINGS.items():
    oprop = onto.search_one(iri=prop_info["iri"])
    if oprop is None:
        print(f"Error: Object property {prop_info['name']} not found in ontology")
    else:
        object_properties[xml_key] = oprop

# This function replaces xsd:decimal with xsd:float in the RDF/XML file manually and InspectionDateTime. For some reason, owlready2 saves it as xsd:decimal, despite the datatype being float. Bandaid fixes pretty much.
def fix_datatypes_in_rdf(file_path):
    """
    Post-processes the RDF/XML file to:
    1. Replace 'rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal"' with 'rdf:datatype="http://www.w3.org/2001/XMLSchema#float"'.
    2. Ensure <m1503:hasInspectionDateTime> tags have 'rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime"',
       replacing 'rdf:datatype="http://www.w3.org/2001/XMLSchema#string"' or adding it if missing.
    
    Args:
        file_path (str): The path to the RDF/XML file to be modified.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace xsd:decimal with xsd:float
        updated_content = content.replace(
            'rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal"',
            'rdf:datatype="http://www.w3.org/2001/XMLSchema#float"'
        )
        
        # Fix hasInspectionDateTime: replace xsd:string with xsd:dateTime or add xsd:dateTime if missing
        # Matches <m1503:hasInspectionDateTime>value</m1503:hasInspectionDateTime>
        # or <m1503:hasInspectionDateTime rdf:datatype="...#string">value</m1503:hasInspectionDateTime>
        pattern = r'(<m1504:hasInspectionDateTime(?:\s+rdf:datatype="http://www.w3.org/2001/XMLSchema#string")?>)([^<]+)(</m1504:hasInspectionDateTime>)'
        replacement = r'<m1504:hasInspectionDateTime rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">\2\3'
        updated_content = re.sub(pattern, replacement, updated_content)
        
        # Check if any replacements were made
        if updated_content != content:
            print(f"Updated datatypes in {file_path} (float and/or dateTime)")
        else:
            print(f"No datatype changes needed in {file_path}")
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred while updating the RDF file: {e}")

def main():
    print("Reading XML and parsing HG and KG entries...")
    hg_list, kg_list = parse_xml(str(XML_PATH))
    print("HG List:", [hg.get("hasDesignation", "unknown") for hg in hg_list])
    print("KG List:", [kg.get("hasDesignation", "unknown") for kg in kg_list])

    node_dict = {}
    pipe_section_dict = {}
    geo_object_dict = {}

    with onto:
        # Create PipeSection individuals
        for hg in hg_list:
            hg_designation = hg.get('hasDesignation', 'unknown')
            individual_name = f"PipeSection_{hg.get('hasDesignation', 'unknown')}"
            if individual_name in pipe_section_dict:
                print(f"Warning: Duplicate PipeSection {individual_name}, skipping")
                continue
            pipe_section = pipe_section_class(individual_name)
            for prop_name, value in hg.items():
                if value is not None and prop_name not in ["start_node_designation", "end_node_designation", "inspections", "measurements", "geometry_objects"]:
                    prop = onto.search_one(iri=f"{BASIC_DATA_IRI}{prop_name}")
                    if prop:
                        setattr(pipe_section, prop_name, [value])
                    else:
                        print(f"Warning: Property {prop_name} not found, skipping")
            pipe_section_dict[hg.get("hasDesignation", "unknown")] = pipe_section
            print(f"Created PipeSection: {individual_name}")


        # Create GO individuals for HG
            for go in hg.get('geometry_objects', []):
                go_designation = go.get('hasGeometryObjectDesignation', hg_designation)
                go_individual_name = f"GeoObject{go_designation}"
                if go_individual_name in geo_object_dict:
                    print(f"Warning: GeoObject {go_individual_name} already exists, skipping creation")
                    continue
                go_individual = geo_object_class(go_individual_name)
                geo_object_dict[go_individual_name] = go_individual
                for prop_name, value in go.items():
                    if prop_name != 'geometry_points' and value is not None:
                        prop = onto.search_one(iri=f"{GEOMETRY_IRI}{prop_name}")
                        if prop:
                            setattr(go_individual, prop_name, [value])
                if "is_child_of" in object_properties:
                    object_properties["is_child_of"][go_individual].append(pipe_section)
                    print(f"Set is_child_of: {go_individual_name} -> {individual_name}")
                print(f"Created GeoObject: {go_individual_name}")

                # Create GP individuals for GO
                gp_index = 0
                for gp in go.get('geometry_points', []):
                    gp_index += 1
                    gp_individual_name = f"GeoPoint{go_designation}_{gp_index}"
                    gp_individual = geo_point_class(gp_individual_name)
                    for prop_name, value in gp.items():
                        if value is not None:
                            prop = onto.search_one(iri=f"{GEOMETRY_IRI}{prop_name}")
                            if prop:
                                setattr(gp_individual, prop_name, [value])
                    if "is_child_of" in object_properties:
                        object_properties["is_child_of"][gp_individual].append(go_individual)
                        print(f"Set is_child_of: {gp_individual_name} -> {go_individual_name}")
                    print(f"Created GeoPoint: {gp_individual_name}")




        # Create HI and HZ individuals
        for hg in hg_list:
            pipe_section = pipe_section_dict.get(hg.get("hasDesignation", "unknown"))
            if not pipe_section:
                continue

            for hi in hg.get('inspections', []):
                inspection_name = f"Inspection{hg.get('hasDesignation', 'unknown')}_{hi.get('hasInspectionNumber', 'unknown')}"
                inspection = inspection_class(inspection_name)
                for prop_name, value in hi.items():
                    if prop_name != 'conditions' and value is not None:
                        prop = onto.search_one(iri=f"{INSPECTION_CONDITION_IRI}{prop_name}")
                        if prop:
                            setattr(inspection, prop_name, [value])
                if "inspects" in object_properties:
                    object_properties["inspects"][inspection].append(pipe_section)
                print(f"Created Inspection: {inspection_name}")

                for hz in hi.get('conditions', []):
                    condition_name = f"Condition{hg.get('hasDesignation', 'unknown')}_{hz.get('hasPipeSectionConditionStation', 'unknown')}_{hz.get('hasConditionCode', 'unknown')}"
                    condition = condition_class(condition_name)
                    for prop_name, value in hz.items():
                        if value is not None:
                            prop = onto.search_one(iri=f"{INSPECTION_CONDITION_IRI}{prop_name}")
                            if prop:
                                setattr(condition, prop_name, [value])
                            else:
                                print(f"Warning: Property {prop_name} not found, skipping")
                    if "is_child_of" in object_properties:
                        object_properties["is_child_of"][condition].append(inspection)
                        print(f"Set is_child_of: {condition_name} -> {inspection_name}")
                    else:
                        print(f"Error: is_child_of property not found in object_properties")
                    print(f"Created Condition: {condition_name}")

            # Create HM individuals (placeholder)
            for hm in hg.get('measurements', []):
                measurement_name = f"Measurement{hg.get('hasDesignation', 'unknown')}_{hm.get('hasMeasurementStation', 'unknown')}"
                measurement = measurement_class(measurement_name)
                for prop_name, value in hm.items():
                    if value is not None:
                        prop = onto.search_one(iri=f"{INSPECTION_CONDITION_IRI}{prop_name}")
                        if prop:
                            setattr(measurement, prop_name, [value])
                if "inspects" in object_properties:  # Adjust relation as needed
                    object_properties["inspects"][measurement].append(pipe_section)
                print(f"Created Measurement: {measurement_name}")

        # Create Node individuals
        for kg in kg_list:
            kg_designation = kg.get('hasDesignation', 'unknown')
            individual_name = f"Node_{kg.get('hasDesignation', 'unknown')}"
            if individual_name in node_dict:
                print(f"Warning: Duplicate Node {individual_name}, skipping")
                continue
            node = node_class(individual_name)
            for prop_name, value in kg.items():
                if value is not None and prop_name not in ["geometry_objects"]:
                    prop = onto.search_one(iri=f"{BASIC_DATA_IRI}{prop_name}")
                    if prop:
                        setattr(node, prop_name, [value])
            node_dict[kg.get("hasDesignation", "unknown")] = node
            print(f"Created Node: {individual_name}")

        # Create GO individuals for KG
            for go in kg.get('geometry_objects', []):
                go_designation = go.get('hasGeometryObjectDesignation', kg_designation)
                go_individual_name = f"GeoObject{go_designation}"
                if go_individual_name in geo_object_dict:
                    print(f"Warning: GeoObject {go_individual_name} already exists, skipping creation")
                    continue
                go_individual = geo_object_class(go_individual_name)
                geo_object_dict[go_individual_name] = go_individual
                for prop_name, value in go.items():
                    if prop_name != 'geometry_points' and value is not None:
                        prop = onto.search_one(iri=f"{GEOMETRY_IRI}{prop_name}")
                        if prop:
                            setattr(go_individual, prop_name, [value])
                if "is_child_of" in object_properties:
                    object_properties["is_child_of"][go_individual].append(node)
                    print(f"Set is_child_of: {go_individual_name} -> {individual_name}")
                print(f"Created GeoObject: {go_individual_name}")

                # Create GP individuals for GO
                gp_index = 0
                for gp in go.get('geometry_points', []):
                    gp_index += 1
                    gp_individual_name = f"GeoPoint{go_designation}_{gp_index}"
                    gp_individual = geo_point_class(gp_individual_name)
                    for prop_name, value in gp.items():
                        if value is not None:
                            prop = onto.search_one(iri=f"{GEOMETRY_IRI}{prop_name}")
                            if prop:
                                setattr(gp_individual, prop_name, [value])
                    if "is_child_of" in object_properties:
                        object_properties["is_child_of"][gp_individual].append(go_individual)
                        print(f"Set is_child_of: {gp_individual_name} -> {go_individual_name}")
                    print(f"Created GeoPoint: {gp_individual_name}")


        # Handle object properties for HG and KG
        for hg in hg_list:
            pipe_section_name = hg.get("hasDesignation", "unknown")
            pipe_section = pipe_section_dict.get(pipe_section_name)
            if not pipe_section:
                continue
            start_node_designation = hg.get("start_node_designation")
            end_node_designation = hg.get("end_node_designation")
            if start_node_designation in node_dict and "flows_from" in object_properties:
                start_node = node_dict[start_node_designation]
                object_properties["flows_from"][pipe_section].append(start_node)
                print(f"{pipe_section_name} flowsFrom {start_node_designation}")
            if end_node_designation in node_dict and "flows_to" in object_properties:
                end_node = node_dict[end_node_designation]
                object_properties["flows_to"][pipe_section].append(end_node)
                print(f"{pipe_section_name} flowsTo {end_node_designation}")

    onto.save(file=str(OUTPUT_ONTOLOGY_PATH), format="rdfxml")
    fix_datatypes_in_rdf(str(OUTPUT_ONTOLOGY_PATH))
    print(f"Ontology saved to {OUTPUT_ONTOLOGY_PATH}")
    print(f"Parsed {len(hg_list)} HG elements.")
    print(f"Parsed {len(kg_list)} KG elements.")

if __name__ == "__main__":
    main()