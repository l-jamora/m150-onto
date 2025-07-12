import owlready2 as owl
from xml_parser_onto import parse_xml
from pathlib import Path
from config import BASIC_DATA_IRI, BASIC_OBJECT_IRI, INSPECTION_CONDITION_IRI
from objectproperties import OBJECT_PROPERTY_MAPPINGS

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

def main():
    print("Reading XML and parsing HG and KG entries...")
    hg_list, kg_list = parse_xml(str(XML_PATH))
    print("HG List:", [hg.get("hasDesignation", "unknown") for hg in hg_list])
    print("KG List:", [kg.get("hasDesignation", "unknown") for kg in kg_list])

    node_dict = {}
    pipe_section_dict = {}

    with onto:
        # Create PipeSection individuals
        for hg in hg_list:
            individual_name = f"PipeSection_{hg.get('hasDesignation', 'unknown')}"
            if individual_name in pipe_section_dict:
                print(f"Warning: Duplicate PipeSection {individual_name}, skipping")
                continue
            pipe_section = pipe_section_class(individual_name)
            for prop_name, value in hg.items():
                if value is not None and prop_name not in ["start_node_designation", "end_node_designation", "inspections", "measurements"]:
                    prop = onto.search_one(iri=f"{BASIC_DATA_IRI}{prop_name}")
                    if prop:
                        setattr(pipe_section, prop_name, [value])
                    else:
                        print(f"Warning: Property {prop_name} not found, skipping")
            pipe_section_dict[hg.get("hasDesignation", "unknown")] = pipe_section
            print(f"Created PipeSection: {individual_name}")

        # Create Node individuals
        for kg in kg_list:
            individual_name = f"Node_{kg.get('hasDesignation', 'unknown')}"
            if individual_name in node_dict:
                print(f"Warning: Duplicate Node {individual_name}, skipping")
                continue
            node = node_class(individual_name)
            for prop_name, value in kg.items():
                if value is not None and prop_name != "geometry_points":
                    prop = onto.search_one(iri=f"{BASIC_DATA_IRI}{prop_name}")
                    if prop:
                        setattr(node, prop_name, [value])
            node_dict[kg.get("hasDesignation", "unknown")] = node
            print(f"Created Node: {individual_name}")

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

        # Handle object properties for HG and KG (unchanged)
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
    print(f"Ontology saved to {OUTPUT_ONTOLOGY_PATH}")
    print(f"Parsed {len(hg_list)} HG elements.")
    print(f"Parsed {len(kg_list)} KG elements.")

if __name__ == "__main__":
    main()