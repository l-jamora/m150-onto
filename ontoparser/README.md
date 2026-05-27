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
  --input "xml/DWA M 150 Beispiel 04_2010 Typ B .xml" \
  [--ontology m150-onto.rdf] \
  [--output m150-onto-parsed.rdf] \
  [--dry-run]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | *(required)* | Path to the DWA M 150 Type B XML file |
| `--ontology` | `m150-onto.rdf` | Base ontology to load individuals into |
| `--output` | `m150-onto-parsed.rdf` | Output RDF/XML file path |
| `--dry-run` | off | Parse and report without writing any output |

## Naming conventions

All generated individuals are prefixed with `Beispiel_`. Labels (human-readable, no prefix) follow DWA-M 150 field templates:

| Individual | Label pattern |
|-----------|---------------|
| `PipeSection` | `PipeSection[HG001]` |
| `Node` | `Node[KG001]` |
| `Inspection` | `Inspection[HG001]_[HI104]_[HI105]` |
| `Condition` | `Condition[HG001]_[HZ001]_[HZ002]` |

If `HI003` / `KI003` is absent from the XML, the parser falls back to the inspection date and time fields.
