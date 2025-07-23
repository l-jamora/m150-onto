import xml.etree.ElementTree as ET
import datetime
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
        elif data_type == "xsd:dateTime":
            return value
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

            # Combine HI104 and HI105 into hasInspectionDateTime
            date_str = hi.findtext("HI104")  # e.g., "07.04.2006"
            time_str = hi.findtext("HI105")  # e.g., "11:32:00"
            if date_str and time_str:
                try:
                    # Parse date from DD.MM.YYYY
                    date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y")
                    # Parse time from HH:MM:SS
                    time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S")
                    # Combine date and time
                    datetime_obj = date_obj.replace(
                        hour=time_obj.hour,
                        minute=time_obj.minute,
                        second=time_obj.second
                    )
                    # Format as xsd:dateTime (YYYY-MM-DDTHH:MM:SS)
                    hi_entry['hasInspectionDateTime'] = datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    print(f"Warning: Invalid date/time format - HI104={date_str}, HI105={time_str}")
                    hi_entry['hasInspectionDateTime'] = None
            else:
                hi_entry['hasInspectionDateTime'] = Non

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

        # Parse GO within HG
        go_list = []
        for go in hg.findall(".//GO"):
            go_entry = {
                prop_name: safe_convert(go.findtext(tag), data_type)
                for tag, prop_name, data_type in FIELDS_CONFIG['GO']
            }
            go_entry = {k: v for k, v in go_entry.items() if v is not None}
            # Parse GP within GO
            gp_list = []
            for gp in go.findall(".//GP"):
                gp_entry = {
                    key: safe_convert(gp.findtext(tag), data_type)
                    for tag, key, data_type in FIELDS_CONFIG['GP']
                }
                gp_entry = {k: v for k, v in gp_entry.items() if v is not None}
                gp_list.append(gp_entry)
            go_entry['geometry_points'] = gp_list
            go_list.append(go_entry)
        hg_entry['geometry_objects'] = go_list

        hg_list.append(hg_entry)



    # Parse KG elements
    kg_list = []
    for kg in root.findall(".//KG"):
        kg_entry = {
            prop_name: safe_convert(kg.findtext(tag), data_type)
            for tag, prop_name, data_type in FIELDS_CONFIG['KG']
        }
        kg_entry = {k: v for k, v in kg_entry.items() if v is not None}
        
        # Parse GO within KG
        go_list = []
        for go in kg.findall(".//GO"):
            go_entry = {
                prop_name: safe_convert(go.findtext(tag), data_type)
                for tag, prop_name, data_type in FIELDS_CONFIG['GO']
            }
            # Parse GP within GO
            gp_list = []
            for gp in go.findall(".//GP"):
                gp_entry = {
                    key: safe_convert(gp.findtext(tag), data_type)
                    for tag, key, data_type in FIELDS_CONFIG['GP']
                }
                gp_list.append(gp_entry)
            go_entry['geometry_points'] = gp_list
            go_list.append(go_entry)
        kg_entry['geometry_objects'] = go_list

        kg_list.append(kg_entry)

    return hg_list, kg_list

# Note: gp_list is no longer returned separately as it’s nested in kg_list