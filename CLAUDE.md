# M150-Onto — Agent Context

## Project Overview

This is a semantic web / ontology project that models the DWA M 150 standard for sewer infrastructure in OWL. The goal is to represent sewer network assets (pipe sections, nodes), their inspection reports, and condition findings as OWL individuals, then reason over them.

The main ontology file is **`m150-onto.rdf`** at the repo root. All class/property definitions are consolidated into this single file; the `Individual Ontologies/` sub-ontology folder has been removed.

---

## Repository Layout

```
m150-onto.rdf                        # Root ontology (all class/property definitions)
ontoparser/
  parser.py                          # Main XML → OWL parser (owlready2)
  __init__.py
  requirements.txt                   # owlready2>=0.8.2
  README.md
Scripts/
  1_reference_subclasses_to_individuals.py   # One-time migration scripts
  2_create_reference_object_properties.py
  3_update_reference_table_individuals.py
xml/                                 # Example DWA M 150 Type B XML input files
xsd/                                 # XML schema definitions
dwa/                                 # DWA M 150 standard PDF documentation
docs/                                # Additional documentation
```

---

## Ontology Class Hierarchy (key classes)

```
owl:Thing
├── Component
│   ├── PipeSection   (disjoint with Node)
│   └── Node
├── Report
│   └── Inspection
│       └── Condition
├── Reference         (all material/type code individuals are instances of subclasses)
│   ├── Material      (e.g. Beispiel_M150_RT105_B = Beton/Concrete)
│   ├── SewerType, NodeType, Shape, …
├── SpatialEntity     (physical/geographic locations; individuals created per XML value)
│   ├── Street
│   ├── District
│   └── TreatmentPlant
├── InformationEntity (administrative identifiers; individuals created per XML value)
│   ├── StreetCode
│   ├── DistrictCode
│   ├── MunicipalityCode
│   ├── AreaCode
│   └── CatchmentAreaCode
├── Directionality
│   ├── FlowingDirection
│   │   ├── InFlowingDirection    (named individual)
│   │   └── AgainstFlowingDirection (named individual)
│   └── Orientation               (GP102 circular arc orientation)
│       ├── Clockwise             (named individual; GP102=I)
│       └── CounterClockwise      (named individual; GP102=G)
└── Geometry
    └── Object
        └── Point
```

**Key design decision:** `Reference` subclasses (Material, SewerType, etc.) are **individuals**, not classes. A `PipeSection` relates to material via object property `hasMaterial`, not via datatype or class membership. This prevents the reasoner from inferring that a pipe section *is* a material.

`SpatialEntity` and `InformationEntity` individuals are created dynamically by the OntoParser when the XML contains location/code data (HG101–HG108 / KG101–KG108). They are deduped — multiple assets sharing the same street get the same `Street` individual.

---

## Key Object Properties

| Property | Domain | Range | Notes |
|---|---|---|---|
| `inspects` | Inspection | Component | Links an inspection report to the asset it covers |
| `isChildOf` / `isParentOf` | Condition | Inspection | Links a condition finding to its parent inspection |
| `hasMaterial` | Component | Material | Functional; range is a Material individual |
| `renders` / `renderedBy` | Geometry | Component | Links geometry objects to assets |
| `flowsTo` / `flowsFrom` | Node | Node | Network topology |

---

## ontoparser

### What it does

Reads a **DWA M 150 Type B XML** file and creates OWL individuals in the ontology for:

| XML element | OWL class | Example individual name |
|---|---|---|
| `HG` (Haltungsgrunddaten) | `PipeSection` | `Beispiel_PipeSection_1204015` |
| `KG` (Knotengrunddaten) | `Node` | `Beispiel_Node_1204015` |
| `HI` (nested in HG) | `Inspection` | `Beispiel_Inspection_1204015_07_04_2006_08_30_00` |
| `KI` (nested in KG) | `Inspection` | same pattern |
| `HZ` (nested in HI) | `Condition` | `Beispiel_Condition_1204015_0_0_BCD` |
| `KZ` (nested in KI) | `Condition` | same pattern |
| `HG102/KG102` value | `Street` | `Beispiel_Street_Hauptstrasse` |
| `HG104/KG104` value | `District` | `Beispiel_District_Mitte` |
| `HG108/KG108` value | `TreatmentPlant` | `Beispiel_TreatmentPlant_KA1` |
| `HG101/KG101` value | `StreetCode` | `Beispiel_StreetCode_001` |
| `HG103/KG103` value | `DistrictCode` | `Beispiel_DistrictCode_05` |
| `HG105/KG105` value | `MunicipalityCode` | `Beispiel_MunicipalityCode_05334` |
| `HG106/KG106` value | `AreaCode` | `Beispiel_AreaCode_A` |
| `HG107/KG107` value | `CatchmentAreaCode` | `Beispiel_CatchmentAreaCode_EG1` |

SpatialEntity/InformationEntity individuals are deduplicated: if two pipe sections share the same street name, they reference the same `Street` individual.

### Naming conventions

- All new individuals are prefixed with `Beispiel_` (module constant `INDIVIDUAL_PREFIX`).
- Names are sanitised through `safe_entity_name()` which collapses non-alphanumeric chars to `_`.
- Labels (human-readable) omit the prefix: `PipeSection[1204015]`, `Inspection[1204015]_[07.04.2006]`.

### How to run

```bash
cd m150-onto
python -m ontoparser.parser \
  --input "xml/DWA M 150 Beispiel 04_2010 Typ B .xml" \
  [--ontology m150-onto.rdf] \
  [--output m150-onto-parsed.rdf] \
  [--dry-run]
```

Output is written to `m150-onto-parsed.rdf` by default.

### Critical implementation detail — owlready2 property assignment

**Always** use the retrieved property object (not attribute-style access) when asserting object properties. Attribute access may fall back to an annotation property and produce incorrect RDF:

```python
# CORRECT — uses the property object retrieved via _get_property()
inspects_prop[inspection_individual].append(pipe_individual)
is_child_of_prop[condition_individual].append(inspection_individual)

# WRONG — may create an owl:AnnotationProperty triple instead
inspection_individual.inspects.append(pipe_individual)
condition_individual.isChildOf.append(inspection_individual)
```

`_get_property(name)` looks up the property in the ontology by IRI; if not found it creates a new `ObjectProperty` (or `DatatypeProperty` when the name is in `_DATATYPE_PROPERTIES`).

### Typed individual resolution

`_resolve_object_individual()` follows a four-tier strategy (in order):

1. **Node cross-reference** (`_NODE_REFERENCE_PROPERTIES`): `hasPipeSectionTopNodeDesignation` / `hasPipeSectionBottomNodeDesignation` — creates/looks up a `Node` individual eagerly.
2. **Named entity** (`_NAMED_ENTITY_PROPERTIES`): maps property names to target classes (e.g. `hasStreetName` → `Street`). Creates a `Beispiel_<ClassName>_<value>` individual of the correct type. Multiple assets with the same value share one individual.
3. **Coded value** (`_CODED_VALUE_INDIVIDUALS`): maps specific coded XML values to pre-existing named individuals (e.g. HG008 `I` → `InFlowingDirection`). Looks up the individual by slash IRI; prints a warning if not found.
4. **Reference table lookup**: if the CSV provides an RT table number, searches for `M150_RT{table}_{code}`; creates a placeholder if missing.
5. **Free-text fallback**: creates a generic `owl:Thing` individual named after the property and value.

**Maintenance rule:** when adding a new object property whose values map to a specific class, add an entry to `_NAMED_ENTITY_PROPERTIES`. When adding a property with a fixed set of coded values that correspond to named individuals, add an entry to `_CODED_VALUE_INDIVIDUALS` (e.g. `hasOrientation`: `I` → `Clockwise`, `G` → `CounterClockwise`; `hasPipeSectionConnectingPipeStationingDirection`: `I` → `InFlowingDirection`, `G` → `AgainstFlowingDirection`).

### Property-type resilience

`_apply_mapping()` uses `isinstance(prop, owl.DatatypeProperty)` as the authority on whether to assign a literal value or resolve an OWL individual — the CSV type column is only a fallback for properties that don't exist in the ontology yet. This means the parser survives future `owl:ObjectProperty` → `owl:DatatypeProperty` refactors without crashing.

**Maintenance rule:** whenever a property is converted between types in the ontology, also move its name between the "Corresponding Ontology Object Property" and "Corresponding Ontology Data Property" columns in `ontoparser/mapping_DWA-to-m150onto.csv`, and add/remove it from `_DATATYPE_PROPERTIES` in `parser.py`. The test `tests/test_object_data_properties.py` enforces this: it checks both columns against the live RDF declarations.

### Known limitations and future work

- `hasInspectionDateTime` is a placeholder datatype property (`xsd:dateTime`). A future revision should replace it with a structured temporal individual using the OWL Time Ontology for richer temporal modelling.
- Properties `hasPipeSectionTopNodeDesignation`, `hasPipeSectionBottomNodeDesignation`, `hasPipeSectionEndPointDesignation`, and `hasMeasurementData` exist in the ontology under the hash-based IRI namespace (`#`) rather than the slash-based namespace (`/`). This causes them to serialize without the `m150:` prefix in output RDF. Fix by moving their declarations to use the slash namespace in `m150-onto.rdf`.
- Some DWA M 150 Reference Table codes are not yet present as individuals (e.g. RT300_L for line geometry, RT303_MNN for elevation datum, certain RT124 node structure component codes). The parser creates placeholder Reference individuals for these.

---

## XML Input Structure (DWA M 150 Type B)

```
DATA
├── FD  (format metadata — FD001 format code, FD002 type)
├── HG  (Haltungsgrunddaten)  ← HG001 = pipe ID
│   ├── GO  (Geometrieobjektdaten)
│   │   └── GP  (Geometriepunktdaten)
│   └── HI  (Haltungsinspektionsdaten) ← HI104 date, HI105 time
│       ├── HZ  (Haltungszustandsdaten) ← HZ001 station, HZ002 code
│       └── HM  (Messwertdaten)
├── KG  (Knotengrunddaten)  ← KG001 = node ID
│   ├── GO  (Geometrieobjektdaten)
│   │   └── GP  (Geometriepunktdaten)
│   ├── KI  (Knoteninspektionsdaten) ← KI104 date, KI105 time
│   │   └── KZ  (Knotenzustandsdaten) ← KZ001 station, KZ002 code
│   └── KA  (Knotenaufbaudaten)
└── RT  (reference table rows) ← RT001 table ID, RT002 code, RT004 value
```

---

## Migration Scripts (one-time, already executed)

The three scripts in `Scripts/` restructured the ontology from the original design:

1. **`1_reference_subclasses_to_individuals.py`** — converted Reference subclasses into individuals.
2. **`2_create_reference_object_properties.py`** — created `hasX` / `isXOf` object property pairs.
3. **`3_update_reference_table_individuals.py`** — populated Reference individuals from RT naming conventions (e.g. `M150_RT105_B` = Beton).

Do not re-run these scripts; they are idempotent but the changes are already committed.
