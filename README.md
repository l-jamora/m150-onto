# M150-Onto

**M150-Onto** is an OWL ontology for sewage infrastructure data based on the German advisory leaflet **DWA-M 150**. It provides a semantic framework for modeling sewer system assets (pipe sections, manholes, nodes), their geometric properties, inspection data, condition assessments, and standardized reference vocabularies. The ontology enables semantic data integration, automated reasoning over network topology and asset relationships, and expressive SPARQL queries for infrastructure analysis and management.

> Built in Protégé as part of academic research to bridge gaps in existing ontologies for sewer systems.

## Table of Contents

* [Key features](#key-features)
* [Getting started](#getting-started)

  * [Prerequisites](#prerequisites)
  * [Install / open](#install--open)
  * [Naming Conventions for Individuals](#naming-conventions-for-individuals)
* [Ontology overview](#ontology-overview)

  * [Taxonomies of M150-Onto](#taxonomies-of-m150-onto)

    * [1. Component Taxonomy](#1-component-taxonomy)
    * [2. Geometry Taxonomy](#2-geometry-taxonomy)
    * [3. Report Taxonomy](#3-report-taxonomy)
    * [4. Reference Taxonomy](#4-reference-taxonomy)
  * [Key object properties](#key-object-properties)
  * [Example data properties](#example-data-properties)
  * [Documentation & annotations](#documentation--annotations)
* [Example DL queries (Manchester syntax)](#example-dl-queries-manchester-syntax)
* [Applications](#applications)
* [Data & examples](#data--examples)
* [Metrics (current model)](#metrics-current-model)
* [Contributing](#contributing)
* [License](#license)
* [Citation](#citation)

## Key features

- **Complete DWA-M 150 coverage** of core elements as OWL classes, properties, and reference tables.
- **Reasoning-friendly network model**: infer connectivity via `flowsTo`/`flowsFrom` and transitive `connectedWith`.
- **Geometry linkage**: geometry objects/points render components; hierarchy via parent/child relations.
- **Inspections & conditions**: represent reports and standardized defect codes.
- **Reference taxonomy**: material, sewer use/type, coding systems, etc.
- **Ready for extensions**: subontology for **DIN EN 13508-2** codes; hooks for **GeoSPARQL** and related domain ontologies.

## Getting started

### Prerequisites
- **Protégé** (for editing, reasoning, and DL queries)

### Install / open

Download and open `m150-onto.rdf` in **Protégé**. Then:

1. **Import** individual M150-XML data as individuals in the ontology. Naming conventions listed below can be followed.
2. Set relevant object and data properties for each individual.
3. Start a reasoner (e.g., HermiT/Pellet) to see inferred relationships (e.g., `connectedWith`).
4. DL Query / SPARQL according to use case.

### Naming Conventions for Individuals

| Class          | Example Individual Name     | Explanation |
|----------------|-----------------------------|-------------|
| `PipeSection`  | `PipeSection_5084`          | Sewer pipe with designation `5084` |
| `Node`         | `Node_100`                  | Node with designation `100` |
| `GeoObject`    | `GeoObject_100-101`                  | Geometry object from `Node_100` to `Node_101` |
| `GeoPoint`    | `GeoPoint_100-101-1`                  | First Geometry Point for `Geoobject_100-101` |
| `Inspection`   | `Inspection_5084_2006-04-07`    | Inspection for `PipeSection_5084` made on April 7, 2006|
| `Condition`    | `Condition_0.0_BAB`      | Crack defect (code BAB) on `PipeSection_5084` at Station 0.0 |

## Ontology overview

### Taxonomies of M150-Onto

M150-Onto is structured around four main **taxonomies** that mirror the domains of the DWA-M 150 guideline. Together, they provide a semantic framework to describe sewer infrastructure, its physical properties, inspections, and standardized references. (See Taxonomies.png)

#### 1. Component Taxonomy
Represents the physical elements of a sewer system.

- **PipeSection** – edges connecting nodes; carry material, diameter, slope, installation date, etc.  
- **Node** – manholes, inspection chambers, junctions, treatment plants.  
- Subclasses and properties follow the DWA-M 150 element classification.  

➡️ Connected through `flowsTo` / `flowsFrom`.  
A transitive property `connectedWith` allows reasoning over entire networks.

#### 2. Geometry Taxonomy
Captures spatial representation and relationships.

- **Object** – a geometry entity (e.g., a pipe axis).  
- **Point** – coordinate points belonging to an object.  

➡️ Hierarchy expressed via `isParentOf` / `isChildOf`.  
➡️ Linked to components with `renders` / `renderedBy`.  
This enables geometry-based queries and potential GeoSPARQL integration.

#### 3. Report Taxonomy
Models inspections and condition assessments.

- **Inspection** – data from visual or technical checks.  
- **Condition** – findings reported in inspections (e.g., cracks, corrosion).  

➡️ Linked to components with `inspects` / `inspectedBy`.  
➡️ Hierarchies (e.g., conditions attached to inspections) represented via `isParentOf` / `isChildOf`.  

This allows filtering infrastructure by defects, inspection results, or condition codes.

#### 4. Reference Taxonomy
Provides controlled vocabularies and coding systems.

- **Material** (e.g., concrete, PVC, steel)  
- **SewerType** (e.g., combined, stormwater, wastewater)  
- **CodingSystem** (DWA-M 150 tables; expandable to DIN EN 13508-2, ISYBAU, ATU, etc.)
- ...

➡️ Ensures semantic consistency and supports **cross-standard mapping** via equivalence axioms.

### Key object properties

* `flowsTo` / `flowsFrom` → inferred transitive `connectedWith`
* `renders` / `renderedBy` (Geometry ↔ Component)
* `isChildOf` / `isParentOf` (hierarchies for geometry & reports)
* `inspects` / `inspectedBy` (Inspection ↔ Component)

### Example data properties

* `hasMaterial`, `hasDesignation`, `hasDistrictCode`, `hasProfileHeight`, …
* Datatypes and ranges follow DWA-M 150 element formats.

### Documentation & annotations

* Labels and comments on classes/properties; multilingual tags possible (e.g., `@de`).

## Example DL queries (Manchester syntax)

> Use Protégé’s **DL Query** tab.

**1) Combined sewers in district "18"**

```
Component and (hasDistrictCode value "18") and CombinedSewer
```

**2) Concrete pipe sections with crack defects (code BAB)**

```
PipeSection and (hasMaterial value "B") and
  (inspectedIn some (Inspection and
    (isParentOf some (Condition and (hasConditionCode value "BAB")))))
```

**3) Reports for pipe sections with specific condition code (e.g., BCD)**

```
Report and
  isChildOf some (Inspection and inspects some PipeSection) and
  hasConditionCode value "BCD"
```

## Applications

* **Inventory management** (materials, profiles, dimensions; network connectivity)
* **Condition monitoring** (standardized codes; trend analysis across inspections)
* **Maintenance planning** (filter by material/defect, cluster spatially)
* **Regulatory compliance** (inspection frequencies, standardized reporting)
* **Data integration** (combine GIS/BIM, link documents, unify coding systems)

## Example Data

* **Public sample data (DWA)** used to test M150-Onto:
  [http://www.dwa.de/rwzusatzfiles/M150.zip](http://www.dwa.de/rwzusatzfiles/M150.zip)

Consider using OntoParser to convert M150-XML data to M150-Onto individuals.

## Metrics (current model)

* \~**376 classes**, **10 object properties**, **186 data properties**
  (will evolve as extensions mature)

## Contributing

1. Fork the repo
2. Create a feature branch
3. Document new classes/properties with labels/comments
4. Add example data or DL/SPARQL queries
5. Open a PR with a short rationale

## License

This project is licensed under the MIT License – you are free to use, modify, and distribute it with proper attribution.

## Citation

TBD
