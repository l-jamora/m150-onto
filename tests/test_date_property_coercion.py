"""hasReportDate/hasAssessmentDate/hasClassificationDate moved from xsd:date to xsd:dateTime
(owlready2/HermiT don't support xsd:date). _coerce_data_value must follow the declared range,
not just guess a bare date -- otherwise it silently emits an xsd:date literal that no longer
matches m150-onto.rdf's rdfs:range.
"""
import sys
from datetime import datetime
from pathlib import Path

import owlready2 as owl

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ontoparser.parser import DEFAULT_ONTOLOGY, _coerce_data_value


def _load_property(name: str):
    onto = owl.get_ontology(str(DEFAULT_ONTOLOGY.resolve())).load()
    return onto.search_one(iri=onto.base_iri + name)


def test_date_only_properties_coerce_to_datetime():
    for prop_name in ("hasReportDate", "hasAssessmentDate", "hasClassificationDate"):
        prop = _load_property(prop_name)
        assert list(prop.range) == [datetime], f"{prop_name} range drifted from xsd:dateTime"

        value = _coerce_data_value("07.04.2006", prop)
        assert isinstance(value, datetime), f"{prop_name} coerced to {type(value)!r}, expected datetime"
        assert value == datetime(2006, 4, 7, 0, 0, 0)


if __name__ == "__main__":
    test_date_only_properties_coerce_to_datetime()
    print("OK")
