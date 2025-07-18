import xml.etree.ElementTree as ET
from xml_element_fields import FIELDS_CONFIG

def safe_convert(value, data_type):
    """Convert value to the specified data type, returning None if conversion fails."""
    if value is None:
        return None
    try:
        if data_type == "xsd:float":
            # Replace comma with dot for decimal values
            value = value.replace(',', '.')
            result = float(value)
            print(f"Converting {value} to xsd:float, result: {result}, type: {type(result)}")
            return result
        elif data_type == "xsd:integer":
            return int(value)
        elif data_type == "xsd:boolean":
            return value.lower() in ('true', '1', 't', 'y', 'yes')
        elif data_type == "xsd:date":
            return str(value)  # Adjust based on date format if needed
        else:  # xsd:string or other
            return str(value)
    except (ValueError, TypeError):
        return None

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

        # Extract HI elements within HG
        hi_list = []
        for hi in hg.findall(".//HI"):
            hi_entry = {
                prop_name: safe_convert(hi.findtext(tag), data_type)
                for tag, prop_name, data_type in FIELDS_CONFIG['HI']
            }
            hi_entry = {k: v for k, v in hi_entry.items() if v is not None}

            # Extract HZ elements within HI
            hz_list = []
            for hz in hi.findall(".//HZ"):
                hz_entry = {
                    prop_name: safe_convert(hz.findtext(tag), data_type)
                    for tag, prop_name, data_type in FIELDS_CONFIG['HZ']
                }
                hz_entry = {k: v for k, v in hz_entry.items() if v is not None}
                hz_list.append(hz_entry)
            hi_entry['conditions'] = hz_list
            hi_list.append(hi_entry)
        hg_entry['inspections'] = hi_list

        # Extract HM elements within HG (assumed nesting)
        hm_list = []
        for hm in hg.findall(".//HM"):
            hm_entry = {
                prop_name: safe_convert(hm.findtext(tag), data_type)
                for tag, prop_name, data_type in FIELDS_CONFIG['HM']
            }
            hm_entry = {k: v for k, v in hm_entry.items() if v is not None}
            hm_list.append(hm_entry)
        hg_entry['measurements'] = hm_list

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

    return hg_list, kg_list

# Note: gp_list is no longer returned separately as it’s nested in kg_list