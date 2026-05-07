# M150-Onto Structure Changes

## Context
The ontology update is focused on correcting the structure of `M150-Onto` so that `Reference` subclasses are treated as individuals rather than as direct class memberships for `PipeSection` and similar asset instances.

## Why this change was needed
The reasoner was misclassifying `PipeSection` individuals when the data property `hasMaterial` had values like `"Concrete"`.

### What was happening
- A `PipeSection` instance with `hasMaterial = "Concrete"` was being inferred as an instance of the class `Concrete`.
- This caused the pipeline asset to be treated as if it were the material itself.

### Why this is illogical
- **Category Error:** A `PipeSection` is a physical infrastructure asset. `Concrete` is a construction material.
- **Correct relationship:** A pipe section may be made of or composed of concrete, but it is not an instance of the `Concrete` class.
- **Reasoning Distortion:** The incorrect inference mixes infrastructure components with material concepts, which breaks the taxonomy and makes spatial analysis and asset management queries incorrect or unreliable.

## What was changed
- Created Python scripts to automate the ontology restructuring.
- Converted `Reference` subclasses into individuals where appropriate.
- Added object properties to represent material and other reference relationships explicitly.
- Ensured new properties follow the naming convention `hasX` / `isXOf` and are set up as inverses.
- Updated `M150-Onto.rdf` to reflect the major ontology rehaul.

## Outcome
- `PipeSection` now relates to material individuals through object properties instead of using `hasMaterial` as a datatype value that triggers class membership inference.
- The ontology now better preserves the distinction between physical assets and reference/material concepts.
- Future reasoning and querying will be more semantically stable and aligned with the intended domain model.

## Notes
- This file documents the structural ontology changes only.
- It does not describe any `OntoParser` parsing or data-mapping changes.
