import owlready2 as owl
from xml_parser_onto import parse_xml
from pathlib import Path
from config import BASIC_DATA_IRI, BASIC_OBJECT_IRI
from objectproperties import OBJECT_PROPERTY_MAPPINGS

# Define paths relative to the repository root
REPO_ROOT = Path(__file__).parent
XML_DIR = REPO_ROOT / "XML"
ONTOLOGY_DIR = REPO_ROOT / "m150-onto"
OUTPUT_DIR = REPO_ROOT / "output"
XML_PATH = XML_DIR / "DWA M 150 Beispiel 04_2010 Typ B .xml"
MAIN_ONTOLOGY_PATH = ONTOLOGY_DIR / "merged_m150-onto.rdf"
OUTPUT_ONTOLOGY_PATH = OUTPUT_DIR / "updated_M150-Onto.rdf"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Check if input files exist
for path in [XML_PATH, MAIN_ONTOLOGY_PATH]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

# Configure Owlready2 to use local files
owl.onto_path.append(str(ONTOLOGY_DIR))

# Load the main ontology
print(f"Loading ontology from {MAIN_ONTOLOGY_PATH}")
onto = owl.get_ontology(f"file://{MAIN_ONTOLOGY_PATH}").load()
print("Ontology loaded successfully")

# Find Node and PipeSection classes
node_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}Node")
pipe_section_class = onto.search_one(iri=f"{BASIC_OBJECT_IRI}PipeSection")
if node_class is None or pipe_section_class is None:
    raise ValueError("Node or PipeSection class not found in ontology")

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
    hg_list, kg_list, gp_list = parse_xml(str(XML_PATH))
    print("HG List:", [hg.get("hasDesignation", "unknown") for hg in hg_list])
    print("KG List:", [kg.get("hasDesignation", "unknown") for kg in kg_list])

    # Dictionaries to store individuals
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
                if value is not None and prop_name not in ["start_node_designation", "end_node_designation"]:
                    prop = onto.search_one(iri=f"{BASIC_DATA_IRI}{prop_name}")
                    if prop is None:
                        print(f"Warning: Property {prop_name} not found in ontology, skipping")
                        continue
                    setattr(pipe_section, prop_name, [value])
            pipe_section_dict[hg.get("hasDesignation", "unknown")] = pipe_section
            print(f"\nCreated PipeSection individual: {individual_name}")

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
                    if prop is None:
                        print(f"Warning: Property {prop_name} not found in ontology, skipping")
                        continue
                    setattr(node, prop_name, [value])
            node_dict[kg.get("hasDesignation", "unknown")] = node
            print(f"\nCreated Node individual: {individual_name}")

        # Handle object properties
        for hg in hg_list:
            pipe_section_name = hg.get("hasDesignation", "unknown")
            pipe_section = pipe_section_dict.get(pipe_section_name)
            if not pipe_section:
                print(f"Error: PipeSection {pipe_section_name} not found")
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

    # Save the updated ontology
    onto.save(file=str(OUTPUT_ONTOLOGY_PATH), format="rdfxml")
    print(f"Ontology saved to {OUTPUT_ONTOLOGY_PATH}")
    print(f"Parsed {len(hg_list)} HG elements.")
    print(f"Parsed {len(kg_list)} KG elements.")

if __name__ == "__main__":
    main()