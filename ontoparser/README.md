# M150-Onto Parser

This package parses DWA-M 150 Type B XML files into the M150-Onto ontology.

## Purpose

- Parse `HG` (Haltungsgrunddaten) as `PipeSection` individuals
- Parse `KG` (Knotengrunddaten) as `Node` individuals
- Parse `HI` (Haltungsinspektionsdaten) as `Inspection` individuals linked to `PipeSection`
- Parse `KI` (Knoteninspektionsdaten) as `Inspection` individuals linked to `Node`
- Parse `HZ` and `KZ` condition rows as `Condition` individuals linked to their inspections

## Usage

From the repository root:

```bash
python -m ontoparser.parser \
  --input xml/DWA\ M\ 150\ Beispiel\ 04_2010\ Typ\ B\ .xml \
  --ontology m150-onto.rdf \
  --output m150-onto-parsed.rdf
```

### Output

The parser writes a new RDF/XML ontology file containing the newly created individuals and relationships.

## Naming conventions

Internally, generated individuals use safe entity names, while the visible label is built using expected DWA-M 150 templates such as:

- `PipeSection[HG001]`
- `Node[KG001]`
- `Inspection[HG001]_[HI104]_[HI105]`
- `Condition[HG001]_[HZ001]_[HZ002]`

If the example XML does not include `HI003` or `KI003`, the parser falls back to the inspection date/time values.
