import ifcopenshell
import ifcopenshell.api
from ifcopenshell.util.element import get_psets
from math import sqrt

# Dictionary
# TODO: Do we even need this? The ontology already knows the mappings. I think we can remove this, but further testing needed. -LJ


# 101 Lagegenauigkeit (Position Accuracy)
POSITION_ACCURACY_MAP = {
    "D": "Digitalisiert",
    "G": "Geschätzt",
    "V": "Vermessen"
}

# 102 Höhengenauigkeit (Height Accuracy)
HEIGHT_ACCURACY_MAP = {
    "B": "Berechnet",
    "G": "Geschätzt",
    "V": "Vermessen"
}

# 103 Kanalart (Channel Type)
CHANNEL_TYPE_MAP = {
    "F": "Offene Freispiegelleitung (Gerinne)",
    "D": "Druckrohrleitung",
    "G": "Dränageleitung",
    "K": "Geschlossene Freispiegelleitung"
}

# 104 Kanalnutzung (Channel Usage)
CHANNEL_USAGE_MAP = {
    "B": "Bach (Gewässer)",
    "M": "Mischwasser",
    "R": "Regenwasser",
    "S": "Schmutzwasser",
    "Z": "Sondernutzung"
}

# 105 Material (Material)
MATERIAL_MAP = {
    "AZ": "Asbestzement",
    "B": "Beton",
    "BIT": "Bitumen",
    "BS": "Betonsegmente",
    "BSK": "Betonsegmente kunststoffmodifiziert",
    "BT": "Bitumen",
    "CN": "Edelstahl",
    "EIS": "Nichtidentifiziertes Metall (z. B. Eisen und Stahl)",
    "EPX": "Epoxydharz",
    "EPSF": "Epoxydharz mit Synthesefaser",
    "FZ": "Faserzement",
    "GFK": "Glasfaserverstärkter Kunststoff",
    "GG": "Grauguß",
    "GGG": "Duktiles Gußeisen",
    "KST": "Nichtidentifizierter Kunststoff",
    "MA": "Mauerwerk",
    "OB": "Ortbeton",
    "PC": "Polymerbeton",
    "PCC": "Polymermodifizierter Zementbeton",
    "PE": "Polyethylen",
    "PH": "Polyesterharz",
    "PHB": "Polyesterharzbeton",
    "PP": "Polypropylen",
    "PUR": "Polyurethanharz",
    "PVCM": "Polyvinylchlorid modifiziert",
    "PVCU": "Polyvinylchlorid hart",
    "SFB": "Stahlfaserbeton",
    "SPB": "Spannbeton",
    "SB": "Stahlbeton",
    "ST": "Stahl",
    "STZ": "Steinzeug",
    "SZB": "Spritzbeton",
    "SZBK": "Spritzbeton kunststoffmodifiziert",
    "TF": "Teerfaser",
    "UPGF": "Ungesättigtes Polyesterharz mit Glasfaser",
    "UPSF": "Ungesättigtes Polyesterharz mit Synthesefaser",
    "VEGF": "Vinylesterharz mit Glasfaser",
    "VESF": "Vinylesterharz mit Synthesefaser",
    "VBK": "Verbundrohr Beton-/Stahlbeton-Kunststoff",
    "VBS": "Verbundrohr Beton-/Stahlbeton-Steinzeug",
    "W": "Nichtidentifizierter Werkstoff",
    "WPE": "Wickelrohr (PEHD)",
    "WPVC": "Wickelrohr (PVCU)",
    "Z": "Sonstiger Werkstoff",
    "ZM": "Zementmörtel",
    "ZG": "Ziegelwerk"
}

# 106 Profilart (Profile Type)
PROFILE_TYPE_MAP = {
    "BO": "Bogenförmig (kreisförmiger Scheitel und flache Sohle bei parallelen Wänden), Haubenquerschnitt",
    "DN": "Kreisförmig, Kreisquerschnitt",
    "EI": "Eiförmig, Eiquerschnitt",
    "GR": "Offener Graben",
    "MA": "Maulquerschnitt",
    "OV": "Oval (kreisförmige Sohle und Scheitel bei parallelen Wänden)",
    "RE": "Rechteckig, Rechteckquerschnitt",
    "RI": "Rinnenquerschnitt",
    "U": "U-förmig",
    "Z": "Sonstige Profilart",
    "10": "Kreisförmig, Kreisquerschnitt" 
}

# 107 Profilauskleidung (Profile Lining)
PROFILE_LINING_MAP = {
    "A": "Beschichtung werkseitig",
    "B": "Auskleidung werkseitig",
    "C": "Schlauchliner",
    "D": "Close-Fit Liner",
    "E": "Liner mit Ringraumverfüllung",
    "F": "Teil-/Vollauskleidung vor Ort",
    "G": "Teil-/Vollbeschichtung vor Ort",
    "Z": "Sonstige Auskleidung"
}

# 108 Haltungsart (Pipe Type)
PIPE_TYPE_MAP = {
    "A": "Kanal",
    "B": "Anschlussleitung",
    "C": "Entlastungsleitung",
    "Z": "Sonstige"
}

# 109 Funktionszustand (Operational Status)
FUNCTIONAL_STATUS_MAP = {
    "B": "In Betrieb",
    "N": "Nicht in Betrieb",
    "P": "Geplant",
    "V": "Verschlossen",
    "Z": "Sonstige"
}

# 110 Eigentum (Ownership)
OWNERSHIP_MAP = {
    "A": "Abwasserverband",
    "G": "Gemeinde",
    "P": "Privat",
    "S": "Stadt",
    "Z": "Sonstige"
}

# 111 Wasserschutzzone (Water Protection Zone)
WATER_PROTECTION_ZONE_MAP = {
    "0": "Keine Wasserschutzzone",
    "I": "Wasserschutzzone I",
    "II": "Wasserschutzzone II",
    "III": "Wasserschutzzone III",
    "IIIa": "Wasserschutzzone IIIa",
    "IIIb": "Wasserschutzzone IIIb",
    "T": "Trinkwasserschutzzone",
    "Th": "Thermal- und Heilquellenschutzzone",
    "Z": "Sonstige"
}

# 112 Lage im Verkehrsraum (Position in Traffic Area)
POSITION_IN_TRAFFIC_AREA_MAP = {
    "0": "Unbekannt",
    "A": "Acker",
    "BA": "Baustraße",
    "BG": "Bebautes Grundstück",
    "BO": "Böschung",
    "F": "Fahrbahn",
    "GL": "Gleisanlage",
    "GS": "Grünstreifen",
    "GW": "Gehweg",
    "P": "Parkplatz",
    "PS": "Parkstreifen",
    "PW": "Privatweg",
    "RW": "Radweg",
    "W": "Wiese",
    "Wb": "Wirtschaftsweg befestigt",
    "Wu": "Wirtschaftsweg unbefestigt",
    "Z": "Sonstige"
}

# 113 Grundwasser (Groundwater)
GROUNDWATER_MAP = {
    "A": "Außerhalb des Grundwassers",
    "I": "Innerhalb des Grundwassers",
    "W": "Wechselzone"
}

# 114 Überschwemmungsgebiet (Flood Zone)
FLOOD_ZONE_MAP = {
    "J": "Im Überschwemmungsgebiet",
    "N": "Nicht im Überschwemmungsgebiet"
}

# 115 Status Daten (Data Status)
DATA_STATUS_MAP = {
    "B": "Bestandsdokumentation",
    "K": "Aus Kanalinspektion",
    "V": "Vermessung vor Ort"
}

# 116 Knotenart (Node Type)
NODE_TYPE_MAP = {
    "A": "Auslass",
    "B": "Bauwerk",
    "E": "Straßenablauf",
    "F": "Fiktiver Schacht",
    "G": "Gebäudeanschluss",
    "I": "Inspektionsöffnung",
    "L": "Lampenschacht",
    "R": "Reinigungsöffnung",
    "S": "Schacht",
    "W": "Sanitärgegenstand (z. B. Waschbecken)",
    "Z": "Sonstige"
}

# 117 Bauwerksart (Structure Type)
STRUCTURE_TYPE_MAP = {
    "ZABA": "Absturzbauwerk mit außenliegendem Untersturz",
    "ZABI": "Absturzbauwerk mit innenliegendem Untersturz",
    "ZABK": "Absturzbauwerk mit Kaskaden",
    "ZABS": "Absturzbauwerk mit Schussrinne",
    "ZABU": "Absturzbauwerk mit Untersturz",
    "ZAL": "Auslaufbauwerk",
    "ZASA": "Abscheideranlagen",
    "ZDUE": "Düker",
    "ZERD": "Bauwerk für erdverlegte Abwasserleitungen und -kanäle",
    "ZEL": "Einlaufbauwerk",
    "ZES": "Einsteigschacht",
    "ZFS": "Fallschacht",
    "ZHEB": "Heber",
    "ZKB": "Kurvenbauwerk",
    "ZMS": "Messschächte",
    "ZPW": "Pumpwerke",
    "ZRKB": "Regenklärbecken",
    "ZRRB": "Regenrückhaltebecken",
    "ZRUB": "Regenüberlaufbecken",
    "ZRUE": "Regenüberlauf",
    "ZSA": "Straßenablauf",
    "ZSB": "Schieberbauwerk",
    "ZSS": "Spülschacht",
    "ZVB": "Verbindungsbauwerk",
    "ZVT": "Verteilerwerke",
    "ZWS": "Wirbelfallschacht",
    "Z": "Sonstige"
}

# 118 Form (Shape)
SHAPE_MAP = {
    "E": "Rechteckig",
    "Q": "Quadratisch",
    "R": "Rund",
    "Z": "Sonstige"
}

# 119 Deckelklasse (Cover Class)
COVER_CLASS_MAP = {
    "0": "Nicht bekannt",
    "A": "Klasse A",
    "B": "Klasse B",
    "C": "Klasse C",
    "D": "Klasse D",
    "E": "Klasse E",
    "F": "Klasse F",
    "Z": "Sonstige"
}

# 120 Innenschutz (Internal Protection)
INTERNAL_PROTECTION_MAP = {
    "A": "Beschichtung werkseitig",
    "B": "Auskleidung werkseitig",
    "C": "Teil-/Vollauskleidung Laminattechnik",
    "D": "Teil-/Vollbeschichtung Laminattechnik",
    "Z": "Sonstige"
}

# 121 Struktur (Structure)
STRUCTURE_MAP = {
    "A": "Abwasserleitung",
    "B": "Regenwasserrückhaltebecken",
    "C": "Wasserstandsmessung",
    "D": "Hydrologisches System",
    "Z": "Sonstiges"
}

# 122 Baustellenstatus (Construction Site Status)
CONSTRUCTION_STATUS_MAP = {
    "O": "Offen",
    "G": "Geschlossen",
    "S": "Stillgelegt"
}

# 123 Grundstücksstatus (Property Status)
PROPERTY_STATUS_MAP = {
    "E": "Erdverlegt",
    "S": "Oberirdisch"
}

# 124 Baumaßnahme (Construction Measure)
CONSTRUCTION_MEASURE_MAP = {
    "B": "Bau der Kanalisation",
    "A": "Anschluss an bestehendes System",
    "S": "Sanierung der Abwasserleitungen",
    "T": "Trassierung der Kanalisation",
    "P": "Pegel- und Volumenmessung",
    "Z": "Sonstiges"
}

# 125 Restriktionen (Restrictions)
RESTRICTIONS_MAP = {
    "W": "Wasserwirtschaftliche Restriktionen",
    "N": "Naturrechtliche Restriktionen",
    "B": "Baugrundrestriktionen",
    "Z": "Sonstige"
}

# 126 Sanierungstatus (Renovation Status)
RENOVATION_STATUS_MAP = {
    "N": "Neu",
    "S": "Sanierung erforderlich",
    "R": "Sanierung abgeschlossen"
}

# 127 Versicherung (Insurance)
INSURANCE_MAP = {
    "P": "Privat",
    "G": "Gemeinschaft",
    "V": "Verbund"
}

# 128 Zulassung (Approval)
APPROVAL_MAP = {
    "A": "Abgenommen",
    "G": "Genehmigt",
    "Z": "Zulässig"
}



# 201 Wurzeleinwuchs (Root Growth)
ROOT_GROWTH_MAP = {
    "A": "Stark",
    "B": "Mittelscharf",
    "C": "Gering",
    "Z": "Kein Einwuchs"
}

# 202 Wasser (Water)
WATER_MAP = {
    "J": "Vorsorgebecken",
    "N": "Kein Vorsorgebecken"
}

# 203 Wetter (Weather)
WEATHER_MAP = {
    "Frost": "Frost",
    "Regen": "Regen",
    "Schnee": "Schnee",
    "Trocken": "Trocken"
}

# 204 Reinigung (Cleaning)
CLEANING_MAP = {
    "J": "Wurde vor Inspektion gereinigt",
    "N": "Wurde vor Inspektion nicht gereinigt"
}

# 205 Reinigung (Cleaning)
FLOOD_PREVENTION_MAP = {
    "J": "Untersuchung mit Vorflutsicherung wurde durchgeführt",
    "N": "Untersuchung ohne Vorflutsicherung"
}

# 206 Videospeichermedium (Video Storage Medium)
VIDEO_STORAGE_MAP = {
    "CD": "Compact Disk",
    "DVD": "DVD-Medium",
    "HD": "Wechselfestplatte (HardDrive)",
    "MOD": "Magnet-optisches Laufwerk (magneto optical disk)",
    "SVHS": "SVHS Videokassette",
    "ST": "USB Stick",
    "Z": "Sonstige"
}

# 207 Fotospeichermedium (Photo Storage Medium)
PHOTO_STORAGE_MAP = {
    "FOTO": "Foto als Filmabzug",
    "DIGFOTO": "Digitales Bild",
    "Z": "Sonstige"
}

# 208 Meldung (Message)
MESSAGE_MAP = {
    "S": "Sofortmaßnahme",
    "Z": "Sonstige"
}

# 209 Bezugspunkt vertikal (Vertical Reference Point)
VERTICAL_REFERENCE_MAP = {
    "A": "Sohllage des niedrigsten Rohres",
    "B": "Überdeckung",
    "C": "Nationaler Bezugspunkt",
    "D": "Lokaler Bezugspunkt",
    "Z": "Sonstige"
}

# 210 Bezugspunkt am Umfang (Reference Point on Perimeter)
PERIMETER_REFERENCE_MAP = {
    "A": "Niedrigstes abgehendes Rohr bei 12 Uhr",
    "B": "Niedrigstes abgehendes Rohr bei 6 Uhr",
    "Z": "Sonstige"
}

# 211 Umgebungsluft (Ambient Air)
AMBIENT_AIR_MAP = {
    "A": "Sauerstoffmangel",
    "B": "Schwefelwasserstoff",
    "C": "Methan",
    "D": "Andere entzündliche Gase",
    "E": "Keine gefährliche Umgebungsluft",
    "Z": "Sonstige"
}

# 212 Punktuelle Reparatur Kanal (Point Repair Sewer)
POINT_REPAIR_SEWER_MAP = {
    "A": "Gel-Injektion",
    "B": "Harz-Injektion",
    "C": "Mörtel-Injektion",
    "D": "Robotertechnik",
    "E": "Kurzliner aus Laminat",
    "F": "Innenmanschetten",
    "G": "Zulauföffnung ohne Einbindung",
    "H": "Zulaufeinbindung Verpresstechnik",
    "I": "Zulaufeinbindung Injektionstechnik",
    "J": "Zulaufeinbindung Hutprofil",
    "K": "Manuelle Technik (z. B. Spachtelung)",
    "L": "Manuelle Laminattechnik",
    "M": "Injektionstechnik Bohrpacker",
    "N": "Verbindungsabdichtung dauerelastisch",
    "O": "Rohr ausgetauscht",
    "Z": "Sonstige Reparaturtechnik"
}

# 213 Punktuelle Reparatur Knoten (Point Repair Node)
POINT_REPAIR_NODE_MAP = {
    "A": "Manuelle Techniken (z. B. Spachtelung)",
    "B": "Manuelle Laminattechnik",
    "C": "Injektionstechnik Bohrpacker",
    "D": "Innenmanschetten verklebt/verspannt",
    "E": "Verbindungsabdichtung dauerelastisch",
    "F": "Anschlussöffnung, Auskleidung ohne Einbindung",
    "G": "Schachtbauteil ausgetauscht – Dichtring",
    "H": "Schachtbauteil ausgetauscht – Mörtelfuge",
    "Z": "Sonstige Reparaturtechnik"
}

# 214 Bearbeitungsstatus (Processing Status)
PROCESSING_STATUS_MAP = {
    "B": "Beauftragt",
    "E": "Erledigt",
    "NB": "Nicht beauftragt",
    "NE": "Nicht erledigt"
}

# 300 Geometrieobjektkennung (Geometry Object Identifier)
GEOMETRY_OBJECT_IDENTIFIER_MAP = {
    "B": "Bauwerk",
    "D": "Deckel",
    "G": "Gerinne",
    "H": "Haltung"
}

# 301 Geometrieobjekttyp (Geometry Object Type)
GEOMETRY_OBJECT_TYPE_MAP = {
    "Fl": "Fläche",
    "Kr": "Kreis",
    "L": "Linie",
    "Pkt": "Punkt",
    "Poly": "Polygon"
}

# 302 Koordinatensystem (Coordinate System)
COORDINATE_SYSTEM_MAP = {
    "GK": "Gauß-Krüger",
    "UTM": "Universal Transversal Mercator"
}

# 303 Höhensystem (Height System)
HEIGHT_SYSTEM_MAP = {
    "mNN": "m.ü.NN",
    "NHN": "Normalhöhennull"
}

# 304 Punkttyp bei Kreisbogen (Point Type at Circular Arc)
POINT_TYPE_CIRCULAR_ARC_MAP = {
    "B": "Bogenpunkt",
    "M": "Kreismittelpunkt"
}

# 401 Messwerttyp (Measurement Type)
MEASUREMENT_TYPE_MAP = {
    "N": "Neigung",
    "T": "Temperatur"
}
