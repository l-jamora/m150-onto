# Changelog

All notable changes to M150-Onto are documented here. This project follows [Semantic Versioning](https://semver.org).

---

## [0.3.4] — 2026-06-24

### Ontology (`m150-onto.rdf`)

#### Added
- `Person` and `Organization` superclasses for individuals representing people and companies
- `Role` superclass with named individuals `Client`, `Company`, `Inspector`, `SiteManager`, `Reporter`, `Assessor`
- Object properties `hasClient`, `hasCompany`, `hasInspector`, `hasSiteManagement`, `hasReporter`, `hasAssessor` (sub-properties of `hasInspectionData`)
- Object property `hasRole` linking `Person`/`Organization` individuals to their `Role`

### OntoParser (`ontoparser/`)

#### Added
- `_ROLE_ENTITY_PROPERTIES` dict: maps `hasClient`, `hasCompany`, `hasInspector`, `hasSiteManagement`, `hasReporter`, `hasAssessor` to `(entity class, Role individual)` pairs; creates a typed `Person` or `Organization` individual and asserts `hasRole` on it
- HI001/KI001, HI111/KI111, HI112/KI112, HI113/KI113, HI203/KI203, HZ203/KZ203, HI205/KI205 are now fully resolved to typed individuals instead of falling through to the `owl:Thing` free-text fallback

---

## [0.3.3] — 2026-06-24

### Ontology (`m150-onto.rdf`)

#### Added
- `Orientation` subclass under `Directionality`; named individuals `Clockwise` (GP102=`I`) and `CounterClockwise` (GP102=`G`) (issue #19)
- `CameraSystem`, `VideoFile`, `Photo`, `AmbientPhoto`, `DigitalPhoto` classes; individuals created per HI/KI006, HI/KI116, HZ/KZ009, KI118, KI122 values (issue #22)

#### Changed
- Node structure properties converted from `owl:ObjectProperty` to `owl:DatatypeProperty`: `hasNodeStructureHeight`, `hasNodeStructureLength`, `hasNodeStructureQuantity`, `hasNodeStructureWidth`
- Geometry properties converted to `owl:DatatypeProperty`: `hasEasting`, `hasNorthing`, `hasEastCoordinate`, `hasNorthCoordinate`, `hasHeight`, `hasGeometryObjectDesignation`, `hasGeometryPointDesignation` (issue #29)
- Measurement properties converted to `owl:DatatypeProperty`: `hasMeasurementStation`, `hasMeasurementValue`, `hasMeasurementUnit` (issue #29)

#### Fixed
- Ranges removed from several data properties temporarily due to float value conversion issue in the parser (issues #27, #30)

### OntoParser (`ontoparser/`)

#### Added
- `_NAMED_ENTITY_PROPERTIES` dict: maps object property names to their target ontology class, enabling typed individual creation for SpatialEntity/InformationEntity and media properties (e.g. `hasStreetName` → `Street`, `hasCameraSystemUsed` → `CameraSystem`, `hasImageName` → `Photo`)
- `_CODED_VALUE_INDIVIDUALS` dict: resolves coded XML values to pre-existing named individuals — HG008 (`hasPipeSectionConnectingPipeStationingDirection`): `I` → `InFlowingDirection`, `G` → `AgainstFlowingDirection`; HI101 (`hasPipeSectionInspectionDirection`): same; GP102 (`hasOrientation`): `I` → `Clockwise`, `G` → `CounterClockwise`

#### Fixed
- `_DATATYPE_PROPERTIES` frozenset extended to cover all newly converted `owl:DatatypeProperty` declarations: node structure, geometry, and measurement properties, plus sync with v0.3.1/v0.3.2 declarations
- CSV mapping: `hasPipeSectionConnectingPipePositioning` (HG009), all geometry (GO001, GP001, GP003–GP007), and all measurement (HM001–HM003) entries moved from object property column to data property column; GP102 (`hasOrientation`) remains in object property column

---

## [0.3.2] — 2026-06-18

### Ontology (`m150-onto.rdf`)

#### Added
- `SpatialEntity` class with subclasses `Street`, `District`, `TreatmentPlant` (issues #20, #26)
- `InformationEntity` class with subclasses `StreetCode`, `DistrictCode`, `MunicipalityCode`, `AreaCode`, `CatchmentAreaCode` (issue #26)
- `Directionality` class with subclass `FlowingDirection`; named individuals `InFlowingDirection` and `AgainstFlowingDirection` (issues #19, #26)
- Object properties `hasStreetName`, `hasStreetCode`, `hasDistrictName`, `hasDistrictCode`, `hasMunicipalityCode`, `hasAreaCode`, `hasCatchmentAreaCode`, `hasTreatmentPlantNumber` (sub-properties of `hasBasicData`)

#### Changed
- HG/KG basic data properties refactored from `owl:ObjectProperty` to `owl:DatatypeProperty`: `hasDesignation`, `hasAlternativeDesignation`, `hasYearOfConstruction`, `hasDepth`, `hasPipeSectionConnectingPipeStationing`, `hasPipeSectionConnectingPipePositioning`, `hasPipeSectionPipelineDesignation`, `hasPipeSectionProfileWidth/Height`, `hasPipeSectionLength/Gradient`, `hasPipeSectionPipeLength`, `hasPipeSectionSelfSupportingLining`, `hasPipeSectionWallThickness`, `hasNodeManholeLength/Width`, `hasNodeCoverWidth/Length`, `isNodeCoverBolted`, `hasNodeChannelWidth/Length`, `hasNodeNumberOfClimbingIrons`

---

## [0.3.1] — 2026-06-10

### Ontology (`m150-onto.rdf`)

#### Added
- Ranges added to all new data properties per DWA-M 150 standard (DWA-M 149-2/149-3 specific elements excluded)

#### Changed
- Inspection properties converted from `owl:ObjectProperty` to `owl:DatatypeProperty` (issue #23): `hasProjectNumber`, `hasInspectionNumber`, `hasProcessingNote`, `hasTemperature`, `hasWaterLevel`, maximum/evaluation/condition class properties, `hasRehabilitationRequirementNumber`, `hasAssessmentClass`, `hasPriority`, `hasNodeInspectionOperationalSafety`, `hasNodeInspectionCorrectCone`
- Condition properties converted to `owl:DatatypeProperty`: `hasConditionCode`, characterization/quantification fields, `hasLinearDamage`, positional and video counter fields, long-text fields, condition class fields, `hasPipeSectionConditionStation/Lining`, `hasNodeConditionDepth/ManholeArea`
- Super-properties renamed to resolve OWL punning issues (issue #24): super data properties separated from super object properties

### OntoParser (`ontoparser/`)

#### Changed
- Test `tests/test_object_data_properties.py` extended to validate both object and data property CSV columns against live RDF declarations
- CSV mapping: obsolete FD/RT element entries removed

---

## [0.3.0] — 2026-06-03

### Ontology (`m150-onto.rdf`)

#### Removed
- Super-property `hasFormatData` and its sub-properties (issue #16)
- Super-property `hasReferenceTableData` and its sub-properties (issue #15)

#### Changed
- Metamodel rework finalized; ontology structure aligned with M150-Onto metamodel spreadsheet

---

## [0.2.0] — 2026-05-27

Resolves the reasoner inference flaw from v0.1.0: `PipeSection` individuals were being classified as instances of their material class (e.g. inferred as `Concrete`) because `hasMaterial` held a string value. This release converts all `Reference` subclasses to named individuals and introduces typed object properties for all reference data, eliminating the category error.

### Ontology (`m150-onto.rdf`)

#### Added
- `Reference` subclasses (`Material`, `SewerType`, `Shape`, etc.) converted to named individuals via `Scripts/1_reference_subclasses_to_individuals.py`
- Object property pairs (`hasX` / `isXOf`) generated for all Reference-related properties via `Scripts/2_create_reference_object_properties.py`
- Reference individuals populated from DWA-M 150 reference table naming convention (e.g. `M150_RT105_B` = Beton/Concrete) via `Scripts/3_update_reference_table_individuals.py`
- Object property hierarchy restructured with super-properties (`hasBasicData`, `hasPipeSectionBasicData`, `hasNodeBasicData`, etc.) per the M150-Onto metamodel spreadsheet
- `hasPipeSectionTopNodeDesignation`, `hasPipeSectionBottomNodeDesignation`, `hasPipeSectionEndPointDesignation` for HG003, HG004, HG005
- `Scripts/4_add_property_characteristics.py`: idempotent bulk assignment of `owl:FunctionalProperty`, `owl:AsymmetricProperty`, `owl:IrreflexiveProperty` to all applicable object properties
- Date/datetime properties (`hasInspectionDateTime`, `hasReportDate`, `hasAssessmentDate`, `hasClassificationDate`) converted to `owl:DatatypeProperty`

#### Changed
- Individual Ontologies sub-folder removed; all definitions consolidated into single root `m150-onto.rdf`
- Base IRI consolidated to slash (`/`) namespace

### OntoParser (`ontoparser/`)

#### Added
- Initial implementation of `ontoparser/parser.py`: declarative CSV-driven parsing of HG, KG, HI, KI, HZ, KZ, GO, GP, KA, FD, RT XML elements
- `ontoparser/mapping_DWA-to-m150onto.csv`: DWA element code → OWL property mapping
- `tests/test_object_data_properties.py`: validates CSV object property column against live RDF declarations
- `CLAUDE.md` agent context file

---

## [0.1.0] — 2025-08-08

Initial working version of M150-Onto. Contains a known logical flaw: the OWL reasoner infers that `PipeSection` individuals are instances of their material class (e.g. classified as `Concrete`) because `hasMaterial` is modelled as a plain datatype assertion. This is resolved in v0.2.0.

### Added
- Core ontology class hierarchy: `Component` (`PipeSection`, `Node`), `Report` (`Inspection`, `Condition`), `Reference`, `Geometry` (`Object`, `Point`)
- Ontology documentation annotations (DCMI, VANN, Bibo metadata) following Widoco best practices
- Experimental OntoParser prototype: pipe section, inspection, measurement, condition, geometry, and node structure parsing
- `NodeStructureComponent` class; KA records as separate `NodeStructureData` individuals
- Geometry Object and Point individual creation for both pipe sections and nodes

---

## [0.0.1] — 2025-04-01

### Added
- Initial commit: base ontology structure and project scaffolding
