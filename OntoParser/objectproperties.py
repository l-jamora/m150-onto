# Mapping of XML keys to ontology object properties with their IRIs

# Base IRI for the ontology
BASIC_OBJECT_IRI = "http://www.semanticweb.org/jluis/ontologies/2025/2/m150-onto#"

OBJECT_PROPERTY_MAPPINGS = {
"connected_with": {
        "iri": f"{BASIC_OBJECT_IRI}connectedWith",
        "name": "connectedWith",
        "domain": f"{BASIC_OBJECT_IRI}Component",
        "range": f"{BASIC_OBJECT_IRI}Component",
    },
    "flows_from": {
        "iri": f"{BASIC_OBJECT_IRI}flowsFrom",
        "name": "flowsFrom",
        "domain": f"{BASIC_OBJECT_IRI}Component",
        "range": f"{BASIC_OBJECT_IRI}Component",
        "inverse": f"{BASIC_OBJECT_IRI}flowsTo",
        "superproperty": f"{BASIC_OBJECT_IRI}connectedWith",
        "label_de": "fließtVon"
    },
    "flows_to": {
        "iri": f"{BASIC_OBJECT_IRI}flowsTo",
        "name": "flowsTo",
        "domain": f"{BASIC_OBJECT_IRI}Component",
        "range": f"{BASIC_OBJECT_IRI}Component",
        "inverse": f"{BASIC_OBJECT_IRI}flowsFrom",
        "superproperty": f"{BASIC_OBJECT_IRI}connectedWith"
    },
    "inspected_in": {
        "iri": f"{BASIC_OBJECT_IRI}inspectedIn",
        "name": "inspectedIn",
        "domain": f"{BASIC_OBJECT_IRI}Component",
        "range": f"{BASIC_OBJECT_IRI}Report",
        "inverse": f"{BASIC_OBJECT_IRI}inspects"
    },
    "inspects": {
        "iri": f"{BASIC_OBJECT_IRI}inspects",
        "name": "inspects",
        "domain": f"{BASIC_OBJECT_IRI}Report",
        "range": f"{BASIC_OBJECT_IRI}Component",
        "inverse": f"{BASIC_OBJECT_IRI}inspectedIn",
        "superproperty": "http://www.w3.org/2002/07/owl#topObjectProperty"
    },
    "is_child_of": {
        "iri": f"{BASIC_OBJECT_IRI}isChildOf",
        "name": "isChildOf",
        "inverse": f"{BASIC_OBJECT_IRI}isParentOf"
        # No domain/range defined in your snippet
    },
    "is_parent_of": {
        "iri": f"{BASIC_OBJECT_IRI}isParentOf",
        "name": "isParentOf",
        "inverse": f"{BASIC_OBJECT_IRI}isChildOf"
        # No domain/range defined in your snippet
    },
    "rendered_by": {
        "iri": f"{BASIC_OBJECT_IRI}renderedBy",
        "name": "renderedBy",
        "domain": f"{BASIC_OBJECT_IRI}Component",
        "range": f"{BASIC_OBJECT_IRI}Geometry",
        "inverse": f"{BASIC_OBJECT_IRI}renders"
    },
    "renders": {
        "iri": f"{BASIC_OBJECT_IRI}renders",
        "name": "renders",
        "domain": f"{BASIC_OBJECT_IRI}Geometry",
        "range": f"{BASIC_OBJECT_IRI}Component",
        "inverse": f"{BASIC_OBJECT_IRI}renderedBy",
        "superproperty": "http://www.w3.org/2002/07/owl#topObjectProperty"
    }
}