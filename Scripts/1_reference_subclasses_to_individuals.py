import argparse
import re
from pathlib import Path

import owlready2 as owl
from rdflib import Graph, Namespace


def safe_entity_name(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_") or "Unnamed"


def load_ontology(path: Path) -> owl.Ontology:
    owl.onto_path.append(str(path.parent))
    ontology = owl.get_ontology(str(path.resolve())).load()
    return ontology


def find_reference_class(onto: owl.Ontology, reference_iri: str) -> owl.ThingClass:
    reference_cls = onto.search_one(iri=reference_iri)
    if reference_cls is None:
        raise ValueError(f"Reference class not found by IRI: {reference_iri}")
    return reference_cls


def direct_reference_children(reference_cls: owl.ThingClass) -> list[owl.ThingClass]:
    return list(reference_cls.subclasses())


def get_parent_class(cls: owl.ThingClass) -> owl.ThingClass | None:
    candidates = [
        anc
        for anc in cls.ancestors()
        if isinstance(anc, owl.ThingClass) and anc is not cls and anc.name != "Thing"
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda c: len(list(c.ancestors())))


def class_descendants(reference_child: owl.ThingClass) -> list[owl.ThingClass]:
    return [
        cls
        for cls in reference_child.descendants()
        if isinstance(cls, owl.ThingClass) and cls is not reference_child
    ]


def create_individual_for_class(reference_child: owl.ThingClass, cls: owl.ThingClass, existing_names: set[str]) -> tuple[str, owl.ThingClass] | None:
    reference_name = safe_entity_name(reference_child.name)
    child_name = safe_entity_name(cls.name)
    individual_name = f"DWA-M150_{reference_name}_{child_name}"

    if individual_name in existing_names:
        return None

    instance = reference_child(individual_name)
    if hasattr(cls, "label") and cls.label:
        instance.label = list(cls.label)
    if hasattr(cls, "comment") and cls.comment:
        instance.comment = list(cls.comment)

    existing_names.add(individual_name)
    return individual_name, instance


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert subclasses under Reference into individuals and remove those classes."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("m150-onto.rdf"),
        help="Input ontology file to read (default: m150-onto.rdf)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("m150-onto-reference-individuals.rdf"),
        help="Output ontology file to write (default: m150-onto-reference-individuals.rdf)",
    )
    parser.add_argument(
        "--reference-iri",
        default="https://l-jamora.github.io/m150-onto/Reference",
        help="IRI of the Reference class in the ontology",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned changes without saving the ontology",
    )
    args = parser.parse_args()

    ontology_path = args.input.resolve()
    if not ontology_path.exists():
        raise FileNotFoundError(f"Input ontology file not found: {ontology_path}")

    print(f"Loading ontology: {ontology_path}")
    onto = load_ontology(ontology_path)
    reference_cls = find_reference_class(onto, args.reference_iri)
    reference_children = direct_reference_children(reference_cls)
    print(f"Found Reference class with {len(reference_children)} direct subclasses.")

    existing_names = {ind.name for ind in onto.individuals()}
    created_individuals: list[tuple[str, owl.ThingClass]] = []
    classes_to_destroy: list[owl.ThingClass] = []

    for ref_child in reference_children:
        descendants = class_descendants(ref_child)
        print(f"- Reference subclass {ref_child.name} has {len(descendants)} descendant classes to replace.")
        for cls in sorted(descendants, key=lambda c: len(list(c.ancestors())), reverse=True):
            created = create_individual_for_class(ref_child, cls, existing_names)
            if created is not None:
                individual_name, instance = created
                created_individuals.append((individual_name, cls))
                print(f"  Created individual {individual_name} for class {cls.name}")
            else:
                if cls.name:
                    print(f"  Skipped creating individual for existing or invalid class {cls.name}")
            classes_to_destroy.append(cls)

    if not created_individuals:
        print("No new individuals were created. No classes will be deleted.")
    else:
        print(f"Prepared {len(created_individuals)} new individuals.")

    if args.dry_run:
        print("Dry run enabled: no ontology file will be written.")
        return

    with onto:
        for cls in classes_to_destroy:
            if cls.name:
                print(f"Destroying class {cls.name}")
            owl.destroy_entity(cls)

    output_path = args.output.resolve()
    onto.save(file=str(output_path), format="rdfxml")
    print(f"Saved updated ontology to: {output_path}")


if __name__ == "__main__":
    main()
