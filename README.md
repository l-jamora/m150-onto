# M150-Onto

**Version 0.5.0**

An OWL ontology modelling the DWA M 150 standard for sewer infrastructure. It represents sewer network assets (pipe sections, nodes), their inspection reports, and condition findings as OWL individuals, enabling structured querying and OWL reasoning over sewer data.

## Repository layout

```
m150-onto.rdf          # Root ontology — all class and property definitions
ontoparser/            # XML → OWL parser (owlready2)
chatbot/               # Natural-language-to-SPARQL chatbot over the parsed data
tests/                 # pytest suite
Scripts/               # One-time migration and maintenance scripts
catalog-v001.xml       # Protégé import catalog
CHANGELOG.md           # Release history
xml/                   # Example DWA M 150 Type B XML input files (local only)
xsd/                   # XML schema definitions (local only)
dwa/                   # DWA M 150 standard PDF documentation (local only)
docs/                  # Additional documentation
```

The `xml/`, `xsd/` and `dwa/` folders are not distributed in the repository (DWA M 150 material is copyrighted and some XML files are partner data); place your own copies there locally.

## Ontology design

Key design decisions are documented in [docs/ontology-structure-changes.md](docs/ontology-structure-changes.md). In brief:

- `Reference` subclasses (Material, SewerType, etc.) are **individuals**, not classes, to prevent reasoners from inferring that a pipe section *is* a material.
- `SpatialEntity` subclasses (`Street`, `District`, `TreatmentPlant`) and `InformationEntity` subclasses (`StreetCode`, `DistrictCode`, `MunicipalityCode`, `AreaCode`, `CatchmentAreaCode`) are also individuals, created dynamically when parsing location/code data from XML.
- `Directionality` individuals (`InFlowingDirection`, `AgainstFlowingDirection`) are pre-defined named individuals used to encode direction codes in sewer connectivity data.
- Inspection data is modelled with `InspectionReport` and `ConditionReport` (a `ConditionReport` is a child of an `InspectionReport`). All IRIs are hash-based (`https://l-jamora.github.io/m150-onto#`).
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

## Chatbot

The [`chatbot/`](chatbot/) package is a local natural-language chatbot over the parsed data: it translates a plain-language question into SPARQL and answers from the query results. See [chatbot/README.md](chatbot/README.md) for setup and usage.

## Related

- [SDCO](https://github.com/l-jamora/sdco) — Sewer Damage Classification Ontology for DIN EN 13508-2, which imports M150-Onto.
- [Explainer page](https://l-jamora.github.io/sdco/) walking through both M150-Onto and SDCO.
- [Ontology documentation](https://l-jamora.github.io/m150-onto/).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

The ontology, documentation and data are licensed under CC BY 4.0 ([`LICENSE`](LICENSE)). The Python code (`ontoparser`, `chatbot`, `Scripts`, `tests`) is licensed under the MIT License ([`LICENSE-CODE`](LICENSE-CODE)).
