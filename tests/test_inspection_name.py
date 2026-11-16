import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ontoparser.parser import M150XmlParser


def test_hi_inspection_name_keeps_date():
    elem = ET.fromstring("<HI><HI104>07.04.2006</HI104><HI105>08:30:00</HI105></HI>")
    # the methods use no instance state, so skip __init__
    parser = M150XmlParser.__new__(M150XmlParser)
    assert "07_04_2006" in parser._inspection_name("1204015", elem)
    assert "[07.04.2006]" in parser._inspection_label("1204015", elem)
