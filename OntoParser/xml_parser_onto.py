import xml.etree.ElementTree as ET
from xml_element_fields import FIELDS_CONFIG

# Datatype Conversion
def safe_convert(value, data_type):
    """Convert value to the specified data type, returning None if conversion fails."""
    if value is None:
        return None
    try:
        if data_type == "xsd:float":
            return float(value)
        elif data_type == "xsd:integer":
            return int(value)
        elif data_type == "xsd:boolean":
            return value.lower() in ('true', '1', 't', 'y', 'yes')
        else:  # xsd:string or other
            return str(value)
    except (ValueError, TypeError):
        return None

# XML Parsing Function
def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML file {file_path}: {e}")
    root = tree.getroot()
    if root is None:
        raise ValueError(f"XML file {file_path} has no root element")

    hg_list = []
    for hg in root.findall(".//HG"):
        hg_entry = {
            prop_name: safe_convert(hg.findtext(tag), data_type)
            for tag, prop_name, data_type in FIELDS_CONFIG['HG']
        }
        hg_entry = {k: v for k, v in hg_entry.items() if v is not None}
        hg_list.append(hg_entry)
    
    kg_list = []
    for kg in root.findall(".//KG"):
        kg_entry = {
            prop_name: safe_convert(kg.findtext(tag), data_type)
            for tag, prop_name, data_type in FIELDS_CONFIG['KG']
        }
        gp_list = []
        for gp in kg.findall(".//GP"):
            gp_entry = {
                key: safe_convert(gp.findtext(tag), data_type)
                for tag, key, data_type in FIELDS_CONFIG['GP']
            }
            gp_list.append(gp_entry)
        kg_entry["geometry_points"] = gp_list
        kg_entry = {k: v for k, v in kg_entry.items() if v is not None}
        kg_list.append(kg_entry)

    return hg_list, kg_list, gp_list