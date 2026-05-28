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
└── Geometry
    └── Object
        └── Point
```

**Key design decision:** `Reference` subclasses (Material, SewerType, etc.) are **individuals**, not classes. A `PipeSection` relates to material via object property `hasMaterial`, not via datatype or class membership. This prevents the reasoner from inferring that a pipe section *is* a material.

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

`_get_property(name)` looks up the property in the ontology by IRI; if not found it creates a new `ObjectProperty` (or `DatatypeProperty` for `hasInspectionDateTime`).

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
