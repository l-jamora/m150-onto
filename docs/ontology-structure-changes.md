# M150-Onto Structure Changes

## Reference subclasses → individuals

### Why this change was needed

The reasoner was misclassifying `PipeSection` individuals when `hasMaterial` held a string value like `"Concrete"`.

- A `PipeSection` instance with `hasMaterial = "Concrete"` was being inferred as an instance of the class `Concrete`.
- This is a category error: a pipe section is a physical infrastructure asset, not an instance of a material concept.
- The incorrect inference broke taxonomy queries and spatial analysis.

### What was changed

- `Reference` subclasses (Material, SewerType, Shape, etc.) were converted to **individuals** using `Scripts/1_reference_subclasses_to_individuals.py`.
- Object property pairs (`hasX` / `isXOf`) were created to replace datatype assertions, using `Scripts/2_create_reference_object_properties.py`.
- Reference individuals were populated from RT naming conventions (e.g. `M150_RT105_B` = Beton/Concrete) using `Scripts/3_update_reference_table_individuals.py`.

### Outcome

`PipeSection` now relates to material individuals via object properties (`hasMaterial`, `hasSewerType`, etc.) rather than datatype values. The reasoner can no longer conflate a pipe section with its material.

---

## Object property characteristics

All `hasX` object properties are declared with three OWL characteristics:

| Characteristic | Rationale |
|---|---|
| `owl:FunctionalProperty` | Each asset has at most one value for these properties (e.g. one material, one sewer type) |
| `owl:AsymmetricProperty` | The relationship is directed; if X hasY, Y cannot hasX |
| `owl:IrreflexiveProperty` | No individual can relate to itself via these properties |

Nine properties are intentionally exempt:

| Property | Reason for exemption |
|---|---|
| `flowsTo`, `flowsFrom` | A node can flow to/from multiple nodes (not functional) |
| `connectedWith` | Symmetric network topology (declared `TransitiveProperty` instead) |
| `inspects`, `inspectedIn` | An inspection may cover multiple components |
| `isChildOf`, `isParentOf` | A condition or inspection may have multiple parents/children |
| `renders`, `renderedBy` | A geometry object may render multiple components |

Characteristics were applied in bulk via `Scripts/4_add_property_characteristics.py`, which is idempotent and should be re-run after adding new object properties.
