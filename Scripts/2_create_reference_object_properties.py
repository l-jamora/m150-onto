from pathlib import Path
import owlready2 as owl
import types

# Base IRI for the ontology
BASIC_OBJECT_IRI = "http://www.semanticweb.org/jluis/ontologies/2025/2/m150-onto#"


def create_object_property(onto, name):
    with onto:
        return types.new_class(
            name,
            (owl.ObjectProperty, owl.FunctionalProperty, owl.AsymmetricProperty, owl.IrreflexiveProperty),
            {}
        )

INPUT_ONTOLOGY = Path(__file__).parent / "m150-onto-reference-individuals.rdf"
OUTPUT_ONTOLOGY = Path(__file__).parent / "merged_m150-onto-with-reference-object-properties.rdf"

owl.onto_path.append(str(INPUT_ONTOLOGY.parent.resolve()))
print(f"Loading ontology from {INPUT_ONTOLOGY}")
onto = owl.get_ontology(str(INPUT_ONTOLOGY.resolve())).load()
print("Ontology loaded")

reference_cls = (
    onto.search_one(label="Reference")
    or onto.search_one(iri=f"{BASIC_OBJECT_IRI}Reference")
    or onto.search_one(iri=f"{onto.base_iri}Reference")
)
if reference_cls is None:
    raise ValueError("Reference class not found in ontology")

subclasses = [cls for cls in reference_cls.descendants() if cls is not reference_cls]
if not subclasses:
    print("No Reference subclasses found.")

created = 0
for ref_cls in sorted(subclasses, key=lambda cls: cls.name):
    forward_name = f"has{ref_cls.name}"
    inverse_name = f"is{ref_cls.name}Of"
    forward_iri = f"{onto.base_iri}{forward_name}"
    inverse_iri = f"{onto.base_iri}{inverse_name}"

    forward_prop = onto.search_one(iri=forward_iri)
    inverse_prop = onto.search_one(iri=inverse_iri)

    if forward_prop is None:
        forward_prop = create_object_property(onto, forward_name)
        print(f"Created object property: {forward_name}")
    else:
        print(f"Found existing object property: {forward_name}")

    if inverse_prop is None:
        inverse_prop = create_object_property(onto, inverse_name)
        print(f"Created inverse object property: {inverse_name}")
    else:
        print(f"Found existing inverse object property: {inverse_name}")

    forward_prop.domain = [owl.Thing]
    forward_prop.range = [ref_cls]
    inverse_prop.domain = [ref_cls]
    inverse_prop.range = [owl.Thing]

    forward_prop.inverse_property = inverse_prop
    inverse_prop.inverse_property = forward_prop

    created += 1

print(f"Processed {created} Reference subclass object-property pairs.")
print(f"Saving updated ontology to {OUTPUT_ONTOLOGY}")
onto.save(file=str(OUTPUT_ONTOLOGY), format="rdfxml")
print("Save complete")
