# M150-Onto

**Version 0.3.3**

An OWL ontology modelling the DWA M 150 standard for sewer infrastructure. It represents sewer network assets (pipe sections, nodes), their inspection reports, and condition findings as OWL individuals, enabling structured querying and OWL reasoning over sewer data.

## Repository layout

```
m150-onto.rdf          # Root ontology — all class and property definitions
ontoparser/            # XML → OWL parser (owlready2)
Scripts/               # One-time migration and maintenance scripts
xml/                   # Example DWA M 150 Type B XML input files
xsd/                   # XML schema definitions
dwa/                   # DWA M 150 standard PDF documentation
docs/                  # Additional documentation
```

## Ontology design

Key design decisions are documented in [docs/ontology-structure-changes.md](docs/ontology-structure-changes.md). In brief:

- `Reference` subclasses (Material, SewerType, etc.) are **individuals**, not classes, to prevent reasoners from inferring that a pipe section *is* a material.
- `SpatialEntity` subclasses (`Street`, `District`, `TreatmentPlant`) and `InformationEntity` subclasses (`StreetCode`, `DistrictCode`, `MunicipalityCode`, `AreaCode`, `CatchmentAreaCode`) are also individuals, created dynamically when parsing location/code data from XML.
- `Directionality` individuals (`InFlowingDirection`, `AgainstFlowingDirection`) are pre-defined named individuals used to encode direction codes in sewer connectivity data.
- Most `hasX` object properties are declared `owl:FunctionalProperty`, `owl:AsymmetricProperty`, and `owl:IrreflexiveProperty`, reflecting their one-to-one, directed, non-self-referential nature. Some exceptions are made for object properties such as super-object properties `hasBasicData`.
- Network topology properties (`flowsTo`, `flowsFrom`, `connectedWith`) and inspection linkage properties (`inspects`, `inspectedIn`, `isChildOf`, `isParentOf`, `renders`, `renderedBy`) are intentionally exempt from the functional constraint.

## Parsing XML data

The `ontoparser` package reads a DWA M 150 Type B XML file and populates the ontology with individuals. See [ontoparser/README.md](ontoparser/README.md) for usage.

## Scripts

| Script | Purpose |
|--------|---------|
| `Scripts/1_reference_subclasses_to_individuals.py` | Converted Reference subclasses to individuals |
| `Scripts/2_create_reference_object_properties.py` | Created `hasX` / `isXOf` object property pairs |
| `Scripts/3_update_reference_table_individuals.py` | Populated Reference individuals from RT naming conventions |
| `Scripts/4_add_property_characteristics.py` | Adds Functional/Asymmetric/Irreflexive to all applicable object properties |

Scripts 1–3 are one-time migrations already applied to `m150-onto.rdf`. Script 4 is idempotent and can be re-run after adding new object properties.
