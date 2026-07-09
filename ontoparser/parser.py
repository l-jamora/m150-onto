import argparse
import csv
import hashlib
import re
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import owlready2 as owl
import rdflib
import types
from rdflib.compare import graph_diff
from rdflib.namespace import OWL, RDFS
from tqdm import tqdm

try:
    from ontoparser import banner
    from ontoparser.run_log import RunLogger
except ImportError:
    # Fall back to a plain sibling-module import when run directly as a script
    # (e.g. `python ontoparser/parser.py`), where the package parent isn't on sys.path.
    import banner
    from run_log import RunLogger

INDIVIDUAL_PREFIX = "Beispiel_"

DEFAULT_ONTOLOGY = Path(__file__).resolve().parents[1] / "m150-onto.rdf"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "m150-onto-parsed.rdf"
CSV_MAPPING_PATH = Path(__file__).resolve().parent / "mapping_DWA-to-m150onto.csv"

# Identity of the derived output ontology. Individuals keep the base ontology's own
# namespace (self.onto.base_iri) unchanged -- this IRI only labels the output file
# itself as a distinct artifact that imports the base ontology rather than duplicating it.
OUTPUT_ONTOLOGY_IRI = "https://l-jamora.github.io/m150-onto-parsed"

# HI104/HI105/KI104/KI105 are combined into one hasInspectionDateTime assignment; exclude from generic mapping
_DATETIME_CODES = frozenset({"HI104", "HI105", "KI104", "KI105"})

# All declared DatatypeProperty names — used to choose the right fallback class when dynamically creating properties
# that are not yet defined in the ontology. Keep this in sync with owl:DatatypeProperty declarations in m150-onto.rdf.
_DATATYPE_PROPERTIES = frozenset({
    "hasInspectionDateTime", "hasReportDate", "hasAssessmentDate", "hasClassificationDate",
    # Basic component data (HG/KG) — converted from ObjectProperty in metamodel rework
    "hasDesignation", "hasAlternativeDesignation",
    "hasYearOfConstruction", "hasDepth",
    "hasPipeSectionConnectingPipeStationing", "hasPipeSectionConnectingPipePositioning",
    "hasPipeSectionPipelineDesignation",
    "hasPipeSectionProfileWidth", "hasPipeSectionProfileHeight",
    "hasPipeSectionLength", "hasPipeSectionGradient",
    "hasPipeSectionPipeLength", "hasPipeSectionSelfSupportingLining", "hasPipeSectionWallThickness",
    "hasNodeManholeLength", "hasNodeManholeWidth",
    "hasNodeCoverWidth", "hasNodeCoverLength", "isNodeCoverBolted",
    "hasNodeChannelWidth", "hasNodeChannelLength",
    "hasNodeNumberOfClimbingIrons",
    "hasNodeStructureHeight", "hasNodeStructureLength", "hasNodeStructureQuantity", "hasNodeStructureWidth",
    # Inspection data (HI/KI) — converted from ObjectProperty in refactoring
    "hasProjectNumber", "hasInspectionNumber", "hasProcessingNote",
    "hasTemperature", "hasWaterLevel",
    "hasMaximumConditionClassTightness", "hasMaximumConditionClassStructuralStability", "hasMaximumConditionClassOperationalSafety",
    "hasConditionPointsTightness", "hasConditionPointsStructuralStability", "hasConditionPointsOperationalSafety",
    "hasEvaluationPointsTightness", "hasEvaluationPointsStructuralStability", "hasEvaluationPointsOperationalSafety",
    "hasRehabilitationRequirementNumber", "hasAssessmentClass", "hasPriority",
    "hasNodeInspectionOperationalSafety", "hasNodeInspectionCorrectCone",
    # Condition data (HZ/KZ) — converted from ObjectProperty in refactoring
    "hasConditionCode", "hasCharacterization1", "hasCharacterization2",
    "hasQuantification1", "hasQuantification2", "hasLinearDamage",
    "hasPositionFrom", "hasPositionTo", "hasVideoCounterReading",
    "hasLongText", "hasConnection", "hasStandardizedComment", "hasCameraSpecificDataPlaceholder",
    "hasConditionClassTightness", "hasConditionClassStructuralStability", "hasConditionClassOperationalSafety",
    "hasPipeSectionConditionStation", "hasPipeSectionConditionLining",
    "hasNodeConditionDepth", "hasNodeConditionManholeArea",
    # Geometry data (GO/GP) — converted from ObjectProperty in metamodel rework
    "hasGeometryObjectDesignation", "hasGeometryPointDesignation",
    "hasEasting", "hasNorthing", "hasEastCoordinate", "hasNorthCoordinate", "hasHeight",
    # Measurement data (HM) — converted from ObjectProperty in metamodel rework
    "hasMeasurementStation", "hasMeasurementValue", "hasMeasurementUnit",
    # Format and reference table metadata (FD/RT elements)
    "hasFormatVersionNumber", "hasFormatType",
    "hasReferenceTable", "hasReferenceTableCode", "hasReferenceTableShortText", "hasReferenceTableLongText",
})

# Object properties whose XML values are Node codes (looked up / eagerly created as Node individuals)
_NODE_REFERENCE_PROPERTIES = frozenset({"hasPipeSectionTopNodeDesignation", "hasPipeSectionBottomNodeDesignation"})

# Object properties whose XML values become typed individuals of a specific ontology class
_NAMED_ENTITY_PROPERTIES: dict = {
    "hasStreetName":                        "Street",
    "hasDistrictName":                      "District",
    "hasTreatmentPlantNumber":              "TreatmentPlant",
    "hasStreetCode":                        "StreetCode",
    "hasDistrictCode":                      "DistrictCode",
    "hasMunicipalityCode":                  "MunicipalityCode",
    "hasAreaCode":                          "AreaCode",
    "hasCatchmentAreaCode":                 "CatchmentAreaCode",
    # Inspection media (HI/KI)
    "hasCameraSystemUsed":                  "CameraSystem",
    "hasVideoStorageMediumName":            "VideoStorageMedium",
    "hasVideoFilename":                     "VideoFile",
    "hasNodeInspectionDigitalPhotoName":    "DigitalPhoto",
    "hasNodeInspectionAmbientPhoto":        "AmbientPhoto",
    # Condition media (HZ/KZ)
    "hasImageName":                         "Photo",
    # Inspection reference point (HI102)
    "hasPipeSectionInspectionReferencePointStart": "PipeSectionInspectionReferencePointStart",
}

# Object properties whose XML values become typed Person/Organization individuals with a hasRole assertion
_ROLE_ENTITY_PROPERTIES: dict = {
    "hasClient":         ("Person",       "Client"),
    "hasCompany":        ("Organization", "Company"),
    "hasInspector":      ("Person",       "Inspector"),
    "hasSiteManagement": ("Person",       "SiteManager"),
    "hasReporter":       ("Person",       "Reporter"),
    "hasAssessor":       ("Person",       "Assessor"),
}

# Object properties whose coded XML values map to specific pre-existing named individuals
_CODED_VALUE_INDIVIDUALS: dict = {
    "hasPipeSectionConnectingPipeStationingDirection": {
        "I": "InFlowingDirection",
        "G": "AgainstFlowingDirection",
    },
    "hasPipeSectionInspectionDirection": {
        "I": "InFlowingDirection",
        "G": "AgainstFlowingDirection",
    },
    "hasOrientation": {
        "I": "Clockwise",
        "G": "CounterClockwise",
    },
}


def normalize_text(element: Optional[ET.Element]) -> str:
    """Extracts and strips text from an XML element, returning an empty string if None."""
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def safe_entity_name(*parts: str) -> str:
    """Combines string parts into a valid, URI-friendly entity name by removing non-alphanumeric characters."""
    combined = "_".join(str(part).strip() for part in parts if part is not None)
    combined = re.sub(r"[^A-Za-z0-9_]+", "_", combined)
    combined = re.sub(r"_+", "_", combined)
    return combined.strip("_") or "Unnamed"


def parse_datetime(date_text: str, time_text: str) -> Optional[datetime]:
    """Attempts to parse date and optional time strings into a datetime object using various formats."""
    if not date_text:
        return None

    raw_date = date_text.strip().replace(".", "-").replace("/", "-")
    raw_time = time_text.strip() if time_text else ""

    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d-%m-%Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            if raw_time:
                return datetime.strptime(f"{raw_date} {raw_time}", fmt)
            if fmt in ["%d-%m-%Y", "%Y-%m-%d"]:
                return datetime.strptime(raw_date, fmt)
        except ValueError:
            continue

    return None


def parse_date(date_text: str) -> Optional[date]:
    """Attempts to parse a date-only string into a date object. Returns None on failure."""
    if not date_text:
        return None
    raw = date_text.strip().replace(".", "-").replace("/", "-")
    for fmt in ["%d-%m-%Y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def load_mapping(csv_path: Path) -> dict:
    """Loads the DWA-to-ontology CSV into a lookup dict keyed by DWA element code.

    Each entry is a dict with keys: type ('object'|'data'|'annotation'), property (str|None),
    rt_table (RT table number string, or '' if not a reference lookup).
    Combined datetime codes (HI104, HI105, KI104, KI105) are excluded — handled separately.
    """
    mapping: dict = {}
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("DWA Element Code", "").strip()
            if not code or code in _DATETIME_CODES:
                continue
            obj_prop = row.get("Corresponding Ontology Object Property", "").strip()
            data_prop = row.get("Corresponding Ontology Data Property", "").strip()
            annotation = row.get("Annotation", "").strip()
            rt_table = row.get("Corresponding Reference Table RT", "").strip()

            if obj_prop:
                mapping[code] = {"type": "object", "property": obj_prop, "rt_table": rt_table}
            elif data_prop:
                mapping[code] = {"type": "data", "property": data_prop, "rt_table": ""}
            elif "rdfs:comment" in annotation:
                mapping[code] = {"type": "annotation", "property": None, "rt_table": ""}
    return mapping


def _coerce_data_value(value: str, prop) -> object:
    """Coerces a raw XML string to the Python type that matches the property's declared rdfs:range.

    Order of attempts: date → range-guided type → raw string fallback.
    """
    date_val = parse_date(value)
    if date_val is not None:
        return date_val

    ranges = list(prop.range) if hasattr(prop, "range") else []
    if ranges:
        r = ranges[0]
        # owlready2 maps XSD types to Python natives (bool, int, float); check those first
        if r is bool:
            return value.strip().lower() in ("true", "yes", "j", "ja", "1", "a")
        if r is int:
            try:
                return int(value)
            except ValueError:
                pass
        if r is float:
            try:
                return float(value.replace(",", "."))
            except ValueError:
                pass
        iri = getattr(r, "iri", str(r))
        if "boolean" in iri:
            return value.strip().lower() in ("true", "yes", "j", "ja", "1", "a")
        if "integer" in iri or "#int" in iri:
            try:
                return int(value)
            except ValueError:
                pass
        if "float" in iri or "double" in iri or "decimal" in iri:
            try:
                return float(value.replace(",", "."))
            except ValueError:
                pass

    return value


def _count_total_items(root: ET.Element) -> int:
    """Estimates the number of leaf-level individuals parse() will create, for progress tracking.

    This is an upper bound: it mirrors parse()'s nesting shape but does not replicate its
    skip-guards (e.g. missing HG001/KG001/HZ001+HZ002/KZ001+KZ002/RT001+RT002), so the actual
    tick count may fall slightly short of this total.
    """
    total = 0
    for hg in root.findall("HG"):
        total += 1  # PipeSection
        for go in hg.findall("GO"):
            total += 1  # GeometryObject
            total += len(go.findall("GP"))  # GeometryPoint
        for hi in hg.findall("HI"):
            total += 1  # Inspection
            total += len(hi.findall("HM"))  # MeasurementData
            total += len(hi.findall("HZ"))  # Condition

    for kg in root.findall("KG"):
        total += 1  # Node
        total += len(kg.findall("KA"))  # NodeStructureData
        for ki in kg.findall("KI"):
            total += 1  # Inspection
            total += len(ki.findall("KZ"))  # Condition

    if root.find("FD") is not None:
        total += 1  # FormatData

    total += len(root.findall("RT"))  # Reference rows

    return total


def _tick(pbar: tqdm) -> None:
    """Advances the progress bar by one item and refreshes its wall-clock finish-time estimate."""
    d = pbar.format_dict
    rate = d.get("rate")
    total = d.get("total")
    if rate and total:
        remaining = (total - d["n"]) / rate
        eta_str = (datetime.now() + timedelta(seconds=remaining)).strftime("%H:%M:%S")
    else:
        eta_str = "--:--:--"
    pbar.set_postfix_str(f"ETA {eta_str}", refresh=False)
    pbar.update(1)


class M150XmlParser:
    def __init__(self, xml_path: Path, ontology_path: Path, output_path: Path, run_logger: "RunLogger | None" = None):
        """Initializes the parser with paths for input XML, base ontology, and output file."""
        self.xml_path = xml_path
        self.ontology_path = ontology_path
        self.output_path = output_path
        self.onto = None
        self._before_graph: "rdflib.Graph | None" = None
        self.mapping: dict = {}
        self._valid_rt_tables: set = set()  # RT table numbers actually referenced by self.mapping
        self._node_cls = None  # set during parse() for use in _resolve_object_individual
        self._pbar = None  # set during parse() for use in _warn
        self._run_logger = run_logger

    def _log(self, message: str) -> None:
        """Prints message to stdout and appends it to the run log, if active."""
        print(message)
        if self._run_logger is not None:
            self._run_logger.write(message)

    def load_ontology(self) -> None:
        """Configures ontology search paths and loads the base ontology and its imports."""
        owl.onto_path.append(str(self.ontology_path.parent.resolve()))
        owl.onto_path.append(str(self.ontology_path.parent.resolve() / "Individual Ontologies"))

        self._log(f"Loading ontology from {self.ontology_path}")
        self.onto = owl.get_ontology(str(self.ontology_path.resolve())).load()

        imported_path = self.ontology_path.parent / "Individual Ontologies" / "M150-Onto.rdf"
        if imported_path.exists():
            owl.get_ontology(str(imported_path.resolve())).load()

        # The ontology is entirely hash-based (xmlns="...#", xml:base without a
        # trailing fragment), so onto.base_iri already gives the correct namespace
        # for all pre-existing and newly created entities.
        self._entity_base = self.onto.base_iri

        # Snapshot the pristine (pre-parse) ontology as an rdflib graph, via owlready2's
        # own serializer, so save() can later diff it against the fully-populated ontology
        # and write out only the triples that this run actually added. Using owlready2's
        # serializer for both snapshots (rather than parsing the on-disk .rdf file directly)
        # keeps any representational quirks identical on both sides of the diff.
        with tempfile.TemporaryDirectory(prefix="ontoparser_") as tmp_dir:
            pristine_path = Path(tmp_dir) / "pristine.owl"
            self.onto.save(file=str(pristine_path), format="rdfxml")
            self._before_graph = rdflib.Graph()
            self._before_graph.parse(str(pristine_path), format="xml")

    def _entity_iri(self, name: str) -> str:
        """Returns the IRI for a named entity within the ontology's namespace."""
        return self._entity_base + name

    def _get_class(self, class_name: str):
        """Retrieves a class from the loaded ontology by name, raising an error if not found."""
        cls = self.onto.search_one(iri=self._entity_iri(class_name))
        if cls is None:
            cls = getattr(self.onto, class_name, None)
        if cls is None:
            raise ValueError(f"Ontology class not found: {class_name}")
        return cls

    def _get_property(self, prop_name: str):
        """Retrieves a property by name or dynamically creates it as an Object or Datatype property."""
        prop = self.onto.search_one(iri=self._entity_iri(prop_name))
        if prop is None:
            prop = getattr(self.onto, prop_name, None)
        if prop is None:
            with self.onto:
                if prop_name in _DATATYPE_PROPERTIES:
                    prop = types.new_class(prop_name, (owl.DatatypeProperty,))
                else:
                    prop = types.new_class(prop_name, (owl.ObjectProperty,))
        return prop

    def _search_case_insensitive(self, name: str):
        """Looks up an individual by name, falling back to a case-insensitive match on the
        local name if an exact-case lookup fails (ontology naming conventions are not always
        consistently cased, e.g. RT303 codes like 'mNN' vs 'MNN')."""
        existing = self.onto.search_one(iri=self._entity_iri(name))
        if existing is not None:
            return existing
        target = name.lower()
        for ind in self.onto.individuals():
            local_name = ind.iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            if local_name.lower() == target:
                return ind
        return None

    def _create_individual(self, cls, entity_name: str, label: Optional[str] = None):
        """Returns an existing individual or creates a new one for the given class and name.

        Searches by IRI to avoid duplicates across parse runs.
        """
        existing = self.onto.search_one(iri=self._entity_iri(entity_name))
        if existing is not None:
            return existing

        with self.onto:
            individual = cls(entity_name)
        if label:
            individual.label = [label]
        return individual

    def _warn(self, message: str) -> None:
        """Prints a warning, routing through the active progress bar's write() to avoid corrupting it."""
        if self._pbar is not None:
            self._pbar.write(message, file=sys.stdout)
        else:
            print(message)
        if self._run_logger is not None:
            self._run_logger.write(message)

    def _resolve_object_individual(self, prop_name: str, value: str, rt_table: str):
        """Resolves an object property value string to an OWL individual.

        Strategy (in order):
        1. Node cross-reference: if prop_name is a node-reference property, look up / eagerly
           create a Node individual so HG003/HG004 links are resolved even before KG is parsed.
        2. Reference lookup: if rt_table is provided, search for M150_RT{rt_table}_{value} by IRI
           (case-insensitively, since RT code casing is not always consistent). If missing
           (should already exist from migration scripts), a placeholder individual is created
           with an "_PLACEHOLDER" suffix.
        3. Named entity: if prop_name is in _NAMED_ENTITY_PROPERTIES, create a typed individual
           of the mapped class and return it (deduplicated by IRI).
        4. Role entity: if prop_name is in _ROLE_ENTITY_PROPERTIES, create a typed Person or
           Organization individual and assert hasRole on it with the mapped Role named individual.
        5. Coded value: if prop_name is in _CODED_VALUE_INDIVIDUALS, map the value to a
           pre-existing named individual (e.g. "I" → InFlowingDirection).
        6. Free-text fallback: create a generic owl:Thing individual named after the property
           and value, with the raw value as rdfs:label.
        """
        if prop_name in _NODE_REFERENCE_PROPERTIES:
            node_name = INDIVIDUAL_PREFIX + safe_entity_name("Node", value)
            return self._create_individual(self._node_cls, node_name)

        if rt_table:
            # Normalize the code: uppercase and strip hyphens to match ontology naming convention
            norm_value = value.upper().replace("-", "")
            ref_name = f"M150_RT{rt_table}_{norm_value}"
            existing = self._search_case_insensitive(ref_name)
            if existing is not None:
                return existing
            placeholder_name = f"{ref_name}_PLACEHOLDER"
            self._warn(f"  Warning: Reference {ref_name} not found; creating placeholder {placeholder_name}")
            ref_cls = self._get_class("Reference")
            return self._create_individual(ref_cls, placeholder_name, label=value)

        if prop_name in _NAMED_ENTITY_PROPERTIES:
            class_name = _NAMED_ENTITY_PROPERTIES[prop_name]
            cls = self._get_class(class_name)
            ind_name = INDIVIDUAL_PREFIX + safe_entity_name(class_name, value)
            return self._create_individual(cls, ind_name, label=value)

        if prop_name in _ROLE_ENTITY_PROPERTIES:
            class_name, role_name = _ROLE_ENTITY_PROPERTIES[prop_name]
            cls = self._get_class(class_name)
            ind_name = INDIVIDUAL_PREFIX + safe_entity_name(class_name, value)
            individual = self._create_individual(cls, ind_name, label=value)
            role_ind = self.onto.search_one(iri=self._entity_iri(role_name))
            if role_ind is not None:
                has_role_prop = self._get_property("hasRole")
                if role_ind not in has_role_prop[individual]:
                    has_role_prop[individual].append(role_ind)
            else:
                self._warn(f"  Warning: Role individual '{role_name}' not found in ontology")
            return individual

        if prop_name in _CODED_VALUE_INDIVIDUALS:
            ind_name = _CODED_VALUE_INDIVIDUALS[prop_name].get(value.upper())
            if ind_name:
                existing = self.onto.search_one(iri=self._entity_iri(ind_name))
                if existing is not None:
                    return existing
                self._warn(f"  Warning: Named individual {ind_name} not found in ontology")
            return None

        ind_name = safe_entity_name(prop_name.replace("has", "", 1), value)
        return self._create_individual(owl.Thing, ind_name, label=value)

    def _apply_mapping(self, individual, entry: dict, value: str) -> None:
        """Applies one CSV mapping entry to an individual for the given element value."""
        entry_type = entry["type"]
        prop_name = entry.get("property")
        rt_table = entry.get("rt_table", "")

        if entry_type == "annotation":
            individual.comment.append(value)
            return

        prop = self._get_property(prop_name)

        # Use the ontology property type as ground truth. The CSV type hint is
        # the fallback for properties dynamically created at parse time.
        if isinstance(prop, owl.DatatypeProperty) or entry_type == "data":
            typed_value = _coerce_data_value(value, prop)
            if typed_value is not None:
                setattr(individual, prop.name, [typed_value])
            return

        ref_ind = self._resolve_object_individual(prop_name, value, rt_table)
        if ref_ind is not None and ref_ind not in prop[individual]:
            prop[individual].append(ref_ind)

    def _assign_properties(self, individual, xml_element: ET.Element, skip_codes: frozenset = frozenset()) -> None:
        """Iterates direct children of xml_element and assigns all mapped properties to individual.

        Child tags absent from self.mapping (e.g. nested element groups like HI, GO) are silently
        skipped, so this method is safe to call on any XML element regardless of nesting.
        """
        for child in xml_element:
            code = child.tag
            if code in skip_codes:
                continue
            value = normalize_text(child)
            if not value:
                continue
            entry = self.mapping.get(code)
            if entry is None:
                continue
            self._apply_mapping(individual, entry, value)

    def parse(self) -> None:
        """Parses the M150 XML file to populate the ontology with assets, inspections, and conditions."""
        tree = ET.parse(str(self.xml_path))
        root = tree.getroot()

        self.mapping = load_mapping(CSV_MAPPING_PATH)
        self._valid_rt_tables = {
            int(entry["rt_table"]) for entry in self.mapping.values() if entry.get("rt_table")
        }

        pipe_cls = self._get_class("PipeSection")
        node_cls = self._get_class("Node")
        inspection_cls = self._get_class("InspectionReport")
        condition_cls = self._get_class("ConditionReport")
        object_cls = self._get_class("GeometryObject")
        point_cls = self._get_class("GeometryPoint")
        reference_cls = self._get_class("Reference")
        self._node_cls = node_cls

        inspects_prop = self._get_property("inspects")
        is_child_of_prop = self._get_property("isChildOf")
        has_geom_obj_data_prop = self._get_property("hasGeometryObjectData")
        has_geom_pt_data_prop = self._get_property("hasGeometryPointData")
        has_node_struct_data_prop = self._get_property("hasNodeStructureData")
        has_measurement_data_prop = self._get_property("hasMeasurementData")

        total = _count_total_items(root)
        self._pbar = tqdm(
            total=total,
            desc="Parsing M150 XML",
            unit="item",
            file=sys.stdout,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{postfix}]",
        )
        try:
            # ── HG: Pipe Sections ────────────────────────────────────────────
            for hg in root.findall("HG"):
                hg_code = normalize_text(hg.find("HG001"))
                if not hg_code:
                    continue

                pipe_name = INDIVIDUAL_PREFIX + safe_entity_name("PipeSection", hg_code)
                pipe_individual = self._create_individual(pipe_cls, pipe_name, label=f"PipeSection[{hg_code}]")
                _tick(self._pbar)

                self._assign_properties(pipe_individual, hg)

                # GO: Geometry Objects
                for go in hg.findall("GO"):
                    go_designation = normalize_text(go.find("GO001")) or hg_code
                    go_name = INDIVIDUAL_PREFIX + safe_entity_name("GeometryObject", hg_code, go_designation)
                    go_individual = self._create_individual(
                        object_cls, go_name, label=f"GeometryObject[{go_designation}]"
                    )
                    _tick(self._pbar)
                    if go_individual not in has_geom_obj_data_prop[pipe_individual]:
                        has_geom_obj_data_prop[pipe_individual].append(go_individual)
                    self._assign_properties(go_individual, go)

                    # GP: Geometry Points
                    for gp in go.findall("GP"):
                        gp_designation = normalize_text(gp.find("GP001")) or f"GP_{go_designation}"
                        gp_name = INDIVIDUAL_PREFIX + safe_entity_name("GeometryPoint", hg_code, gp_designation)
                        gp_individual = self._create_individual(
                            point_cls, gp_name, label=f"GeometryPoint[{gp_designation}]"
                        )
                        _tick(self._pbar)
                        if gp_individual not in has_geom_pt_data_prop[go_individual]:
                            has_geom_pt_data_prop[go_individual].append(gp_individual)
                        self._assign_properties(gp_individual, gp)

                # HI: Pipe Inspections
                for hi in hg.findall("HI"):
                    inspection_name = self._inspection_name(hg_code, hi)
                    inspection_label = self._inspection_label(hg_code, hi)
                    inspection_individual = self._create_individual(inspection_cls, inspection_name, label=inspection_label)
                    _tick(self._pbar)

                    if pipe_individual not in inspects_prop[inspection_individual]:
                        inspects_prop[inspection_individual].append(pipe_individual)

                    datetime_value = parse_datetime(normalize_text(hi.find("HI104")), normalize_text(hi.find("HI105")))
                    if datetime_value is not None:
                        has_datetime = self._get_property("hasInspectionDateTime")
                        setattr(inspection_individual, has_datetime.name, [datetime_value])

                    # HI104/HI105 are excluded from self.mapping; no explicit skip needed
                    self._assign_properties(inspection_individual, hi)

                    # HM: Measurement Data
                    for hm_idx, hm in enumerate(hi.findall("HM")):
                        hm_name = INDIVIDUAL_PREFIX + safe_entity_name("MeasurementData", inspection_name, str(hm_idx))
                        hm_individual = self._create_individual(owl.Thing, hm_name)
                        _tick(self._pbar)
                        if hm_individual not in has_measurement_data_prop[inspection_individual]:
                            has_measurement_data_prop[inspection_individual].append(hm_individual)
                        self._assign_properties(hm_individual, hm)

                    # HZ: Pipe Condition Findings
                    for hz in hi.findall("HZ"):
                        hz_station = normalize_text(hz.find("HZ001"))
                        hz_code = normalize_text(hz.find("HZ002"))
                        if not hz_station or not hz_code:
                            continue

                        condition_name = INDIVIDUAL_PREFIX + safe_entity_name("Condition", hg_code, hz_station, hz_code)
                        condition_individual = self._create_individual(
                            condition_cls, condition_name,
                            label=f"Condition[{hg_code}]_[{hz_station}]_[{hz_code}]"
                        )
                        _tick(self._pbar)
                        if inspection_individual not in is_child_of_prop[condition_individual]:
                            is_child_of_prop[condition_individual].append(inspection_individual)

                        self._assign_properties(condition_individual, hz)

            # ── KG: Nodes ────────────────────────────────────────────────────
            for kg in root.findall("KG"):
                kg_code = normalize_text(kg.find("KG001"))
                if not kg_code:
                    continue

                node_name = INDIVIDUAL_PREFIX + safe_entity_name("Node", kg_code)
                node_individual = self._create_individual(node_cls, node_name, label=f"Node[{kg_code}]")
                _tick(self._pbar)

                self._assign_properties(node_individual, kg)

                # KA: Node Structure Component Records
                for ka_idx, ka in enumerate(kg.findall("KA")):
                    ka_name = INDIVIDUAL_PREFIX + safe_entity_name("NodeStructureData", kg_code, str(ka_idx))
                    ka_individual = self._create_individual(owl.Thing, ka_name)
                    _tick(self._pbar)
                    if ka_individual not in has_node_struct_data_prop[node_individual]:
                        has_node_struct_data_prop[node_individual].append(ka_individual)
                    self._assign_properties(ka_individual, ka)

                # KI: Node Inspections
                for ki in kg.findall("KI"):
                    inspection_name = self._inspection_name(kg_code, ki)
                    inspection_label = self._inspection_label(kg_code, ki)
                    inspection_individual = self._create_individual(inspection_cls, inspection_name, label=inspection_label)
                    _tick(self._pbar)

                    if node_individual not in inspects_prop[inspection_individual]:
                        inspects_prop[inspection_individual].append(node_individual)

                    datetime_value = parse_datetime(normalize_text(ki.find("KI104")), normalize_text(ki.find("KI105")))
                    if datetime_value is not None:
                        has_datetime = self._get_property("hasInspectionDateTime")
                        setattr(inspection_individual, has_datetime.name, [datetime_value])

                    # KI104/KI105 are excluded from self.mapping; no explicit skip needed
                    self._assign_properties(inspection_individual, ki)

                    # KZ: Node Condition Findings
                    for kz in ki.findall("KZ"):
                        kz_station = normalize_text(kz.find("KZ001"))
                        kz_code = normalize_text(kz.find("KZ002"))
                        if not kz_station or not kz_code:
                            continue

                        condition_name = INDIVIDUAL_PREFIX + safe_entity_name("Condition", kg_code, kz_station, kz_code)
                        condition_individual = self._create_individual(
                            condition_cls, condition_name,
                            label=f"Condition[{kg_code}]_[{kz_station}]_[{kz_code}]"
                        )
                        _tick(self._pbar)
                        if inspection_individual not in is_child_of_prop[condition_individual]:
                            is_child_of_prop[condition_individual].append(inspection_individual)

                        self._assign_properties(condition_individual, kz)

            # ── FD: Format Metadata ───────────────────────────────────────────
            fd_elem = root.find("FD")
            if fd_elem is not None:
                fd001 = normalize_text(fd_elem.find("FD001"))
                fd002 = normalize_text(fd_elem.find("FD002"))
                fd_name = INDIVIDUAL_PREFIX + safe_entity_name("FormatData", fd001, fd002)
                fd_individual = self._create_individual(owl.Thing, fd_name)
                _tick(self._pbar)
                self._assign_properties(fd_individual, fd_elem)

            # ── RT: Reference Table Rows ──────────────────────────────────────
            # RT003 (short text) and RT004 (long text) are assigned directly as rdfs:label /
            # rdfs:comment rather than via the object-property resolution path, since their
            # values are free-form German strings (not reference codes).
            #
            # Only tables actually referenced by a mapping's rt_table column (the fixed DWA
            # vocabulary tables, e.g. RT105 materials, RT124 node components) are materialized
            # as Reference individuals here. Other tables (e.g. RT001 street codes) are
            # site-specific lookup data, not fixed vocabulary, and are already captured via
            # hasStreetName/hasStreetCode when HG/KG elements are parsed — creating a Reference
            # individual for them here would just produce an unlinked duplicate.
            for rt in root.findall("RT"):
                rt001 = normalize_text(rt.find("RT001"))
                rt002 = normalize_text(rt.find("RT002"))
                if not rt001 or not rt002:
                    continue
                if int(rt001) not in self._valid_rt_tables:
                    continue

                rt_name = safe_entity_name("M150_RT" + rt001, rt002)
                rt_individual = self._create_individual(reference_cls, rt_name)
                _tick(self._pbar)

                rt003 = normalize_text(rt.find("RT003"))
                rt004 = normalize_text(rt.find("RT004"))
                if rt003:
                    rt_individual.label.append(rt003)
                if rt004:
                    rt_individual.comment.append(rt004)
        finally:
            self._pbar.n = self._pbar.total
            self._pbar.refresh()
            if self._run_logger is not None:
                self._run_logger.write(str(self._pbar))
            self._pbar.close()
            self._pbar = None

    def _inspection_name(self, component_code: str, inspection_elem: ET.Element) -> str:
        """Generates a unique IRI-safe name for an inspection individual based on component ID and date."""
        date_text = normalize_text(inspection_elem.find("HI104") or inspection_elem.find("KI104"))
        time_text = normalize_text(inspection_elem.find("HI105") or inspection_elem.find("KI105"))
        if date_text:
            safe_date = safe_entity_name(date_text, time_text)
            return INDIVIDUAL_PREFIX + safe_entity_name("Inspection", component_code, safe_date)
        return INDIVIDUAL_PREFIX + safe_entity_name("Inspection", component_code)

    def _inspection_label(self, component_code: str, inspection_elem: ET.Element) -> str:
        """Generates a human-readable label for an inspection individual."""
        date_text = normalize_text(inspection_elem.find("HI104") or inspection_elem.find("KI104"))
        time_text = normalize_text(inspection_elem.find("HI105") or inspection_elem.find("KI105"))
        label = f"Inspection[{component_code}]"
        if date_text:
            label += f"_[{date_text}]"
        if time_text:
            label += f"_[{time_text}]"
        return label

    def save(self) -> None:
        """Writes only the triples added by this run to the output path, importing the base ontology.

        Diffs the fully-populated ontology against the pristine snapshot taken in load_ontology()
        via rdflib.compare.graph_diff (blank-node-safe, unlike plain triple-set subtraction --
        the base ontology has at least one owl:AllDisjointClasses/rdf:parseType="Collection"
        construct whose blank node identifiers are not stable across separate parses).
        """
        self._log(f"Saving parsed ontology to {self.output_path}")

        hash_before = hashlib.sha256(self.ontology_path.read_bytes()).hexdigest()

        with tempfile.TemporaryDirectory(prefix="ontoparser_") as tmp_dir:
            populated_path = Path(tmp_dir) / "populated.owl"
            self.onto.save(file=str(populated_path), format="rdfxml")
            after_graph = rdflib.Graph()
            after_graph.parse(str(populated_path), format="xml")

        _, _, new_only = graph_diff(self._before_graph, after_graph)

        base_onto_iri = rdflib.URIRef(self._entity_base.rstrip("#/"))
        output_onto_iri = rdflib.URIRef(OUTPUT_ONTOLOGY_IRI)

        out_graph = rdflib.Graph()
        out_graph.bind("m150", self._entity_base)
        for triple in new_only:
            out_graph.add(triple)
        out_graph.add((output_onto_iri, rdflib.RDF.type, OWL.Ontology))
        out_graph.add((output_onto_iri, OWL.imports, base_onto_iri))
        out_graph.add((
            output_onto_iri,
            RDFS.comment,
            rdflib.Literal(
                f"Auto-generated by ontoparser.parser from {self.xml_path.name}. "
                "Contains only the individuals/assertions parsed from that XML file; "
                "imports the base M150-Onto ontology rather than duplicating it. "
                "DO NOT HAND-EDIT -- regenerate with python -m ontoparser.parser."
            ),
        ))

        out_graph.serialize(destination=str(self.output_path), format="xml")

        hash_after = hashlib.sha256(self.ontology_path.read_bytes()).hexdigest()
        if hash_after != hash_before:
            raise RuntimeError(f"{self.ontology_path} was modified while saving output -- this must never happen")


def main() -> None:
    """CLI entry point for parsing M150 XML data into the ontology."""
    parser = argparse.ArgumentParser(description="Parse M150 Type B XML into the M150-Onto ontology.")
    parser.add_argument("--input", "-i", type=Path, required=True, help="Path to the M150 Type B XML file")
    parser.add_argument(
        "--ontology",
        "-o",
        type=Path,
        default=DEFAULT_ONTOLOGY,
        help="Path to the M150 ontology RDF/XML file",
    )
    parser.add_argument(
        "--output",
        "-s",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output ontology file path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without writing output",
    )

    args = parser.parse_args()

    run_logger = RunLogger()
    banner.print_banner(log=run_logger)

    try:
        parser_obj = M150XmlParser(args.input, args.ontology, args.output, run_logger=run_logger)
        parser_obj.load_ontology()
        parser_obj.parse()
        if not args.dry_run:
            parser_obj.save()
    finally:
        run_logger.write(f"Run log saved to {run_logger.path}")
        print(f"Run log saved to {run_logger.path}")
        run_logger.close()


if __name__ == "__main__":
    main()
