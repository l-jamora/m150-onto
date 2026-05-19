import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import owlready2 as owl
import types

INDIVIDUAL_PREFIX = "Beispiel_"

DEFAULT_ONTOLOGY = Path(__file__).resolve().parents[1] / "m150-onto.rdf"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "m150-onto-parsed.rdf"


def normalize_text(element: Optional[ET.Element]) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def safe_entity_name(*parts: str) -> str:
    combined = "_".join(str(part).strip() for part in parts if part is not None)
    combined = re.sub(r"[^A-Za-z0-9_]+", "_", combined)
    combined = re.sub(r"_+", "_", combined)
    return combined.strip("_") or "Unnamed"


def parse_datetime(date_text: str, time_text: str) -> Optional[datetime]:
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


class M150XmlParser:
    def __init__(self, xml_path: Path, ontology_path: Path, output_path: Path):
        self.xml_path = xml_path
        self.ontology_path = ontology_path
        self.output_path = output_path
        self.onto = None

    def load_ontology(self) -> None:
        owl.onto_path.append(str(self.ontology_path.parent.resolve()))
        owl.onto_path.append(str(self.ontology_path.parent.resolve() / "Individual Ontologies"))

        print(f"Loading ontology from {self.ontology_path}")
        self.onto = owl.get_ontology(str(self.ontology_path.resolve())).load()

        imported_path = self.ontology_path.parent / "Individual Ontologies" / "M150-Onto.rdf"
        if imported_path.exists():
            owl.get_ontology(str(imported_path.resolve())).load()

    def _get_class(self, class_name: str):
        cls = self.onto.search_one(iri=f"{self.onto.base_iri}{class_name}")
        if cls is None:
            cls = getattr(self.onto, class_name, None)
        if cls is None:
            raise ValueError(f"Ontology class not found: {class_name}")
        return cls

    def _get_property(self, prop_name: str):
        prop = self.onto.search_one(iri=f"{self.onto.base_iri}{prop_name}")
        if prop is None:
            prop = getattr(self.onto, prop_name, None)
        if prop is None:
            with self.onto:
                if prop_name == "hasInspectionDateTime":
                    prop = types.new_class(prop_name, (owl.DatatypeProperty,))
                else:
                    prop = types.new_class(prop_name, (owl.ObjectProperty,))
        return prop

    def _create_individual(self, cls, entity_name: str, label: Optional[str] = None):
        existing = self.onto.search_one(iri=f"{self.onto.base_iri}{entity_name}")
        if existing is not None:
            return existing

        individual = cls(entity_name)
        if label:
            individual.label = [label]
        return individual

    def parse(self) -> None:
        tree = ET.parse(str(self.xml_path))
        root = tree.getroot()

        pipe_cls = self._get_class("PipeSection")
        node_cls = self._get_class("Node")
        inspection_cls = self._get_class("Inspection")
        condition_cls = self._get_class("Condition")

        inspects_prop = self._get_property("inspects")
        is_child_of_prop = self._get_property("isChildOf")

        pipe_sections = {}
        nodes = {}

        for hg in root.findall("HG"):
            hg_code = normalize_text(hg.find("HG001"))
            if not hg_code:
                continue

            pipe_name = INDIVIDUAL_PREFIX + safe_entity_name("PipeSection", hg_code)
            pipe_label = f"PipeSection[{hg_code}]"
            pipe_individual = self._create_individual(pipe_cls, pipe_name, label=pipe_label)
            pipe_sections[hg_code] = pipe_individual

            for hi in hg.findall("HI"):
                inspection_name = self._inspection_name(hg_code, hi)
                inspection_label = self._inspection_label(hg_code, hi)
                inspection_individual = self._create_individual(inspection_cls, inspection_name, label=inspection_label)

                if pipe_individual not in inspects_prop[inspection_individual]:
                    inspects_prop[inspection_individual].append(pipe_individual)

                datetime_value = parse_datetime(normalize_text(hi.find("HI104")), normalize_text(hi.find("HI105")))
                if datetime_value is not None:
                    has_datetime = self._get_property("hasInspectionDateTime")
                    setattr(inspection_individual, has_datetime.name, [datetime_value])

                for hz in hi.findall("HZ"):
                    hz_station = normalize_text(hz.find("HZ001"))
                    hz_code = normalize_text(hz.find("HZ002"))
                    if not hz_station or not hz_code:
                        continue

                    condition_name = INDIVIDUAL_PREFIX + safe_entity_name("Condition", hg_code, hz_station, hz_code)
                    condition_label = f"Condition[{hg_code}]_[{hz_station}]_[{hz_code}]"
                    condition_individual = self._create_individual(condition_cls, condition_name, label=condition_label)
                    if inspection_individual not in is_child_of_prop[condition_individual]:
                        is_child_of_prop[condition_individual].append(inspection_individual)

        for kg in root.findall("KG"):
            kg_code = normalize_text(kg.find("KG001"))
            if not kg_code:
                continue

            node_name = INDIVIDUAL_PREFIX + safe_entity_name("Node", kg_code)
            node_label = f"Node[{kg_code}]"
            node_individual = self._create_individual(node_cls, node_name, label=node_label)
            nodes[kg_code] = node_individual

            for ki in kg.findall("KI"):
                inspection_name = self._inspection_name(kg_code, ki)
                inspection_label = self._inspection_label(kg_code, ki)
                inspection_individual = self._create_individual(inspection_cls, inspection_name, label=inspection_label)

                if node_individual not in inspects_prop[inspection_individual]:
                    inspects_prop[inspection_individual].append(node_individual)

                datetime_value = parse_datetime(normalize_text(ki.find("KI104")), normalize_text(ki.find("KI105")))
                if datetime_value is not None:
                    has_datetime = self._get_property("hasInspectionDateTime")
                    setattr(inspection_individual, has_datetime.name, [datetime_value])

                for kz in ki.findall("KZ"):
                    kz_station = normalize_text(kz.find("KZ001"))
                    kz_code = normalize_text(kz.find("KZ002"))
                    if not kz_station or not kz_code:
                        continue

                    condition_name = INDIVIDUAL_PREFIX + safe_entity_name("Condition", kg_code, kz_station, kz_code)
                    condition_label = f"Condition[{kg_code}]_[{kz_station}]_[{kz_code}]"
                    condition_individual = self._create_individual(condition_cls, condition_name, label=condition_label)
                    if inspection_individual not in is_child_of_prop[condition_individual]:
                        is_child_of_prop[condition_individual].append(inspection_individual)

    def _inspection_name(self, component_code: str, inspection_elem: ET.Element) -> str:
        date_text = normalize_text(inspection_elem.find("HI104") or inspection_elem.find("KI104"))
        time_text = normalize_text(inspection_elem.find("HI105") or inspection_elem.find("KI105"))
        if date_text:
            safe_date = safe_entity_name(date_text, time_text)
            return INDIVIDUAL_PREFIX + safe_entity_name("Inspection", component_code, safe_date)
        return INDIVIDUAL_PREFIX + safe_entity_name("Inspection", component_code)

    def _inspection_label(self, component_code: str, inspection_elem: ET.Element) -> str:
        date_text = normalize_text(inspection_elem.find("HI104") or inspection_elem.find("KI104"))
        time_text = normalize_text(inspection_elem.find("HI105") or inspection_elem.find("KI105"))
        label = f"Inspection[{component_code}]"
        if date_text:
            label += f"_[{date_text}]"
        if time_text:
            label += f"_[{time_text}]"
        return label

    def save(self) -> None:
        print(f"Saving parsed ontology to {self.output_path}")
        self.onto.save(file=str(self.output_path), format="rdfxml")


def main() -> None:
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
    parser_obj = M150XmlParser(args.input, args.ontology, args.output)
    parser_obj.load_ontology()
    parser_obj.parse()
    if not args.dry_run:
        parser_obj.save()


if __name__ == "__main__":
    main()
