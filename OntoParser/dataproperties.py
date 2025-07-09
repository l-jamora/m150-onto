# Mapping of XML keys to ontology data properties with their IRIs

# Base IRI for the ontology
BASIC_DATA_IRI = "http://www.semanticweb.org/jluis/ontologies/2025/2/m150-onto-basicdata#"

DATA_PROPERTY_MAPPINGS = {

    ### NODE BASIC DATA PROPERTIES ###

    "node_designation": {
        "iri": f"{BASIC_DATA_IRI}hasDesignation",
        "name": "hasDesignation"
    },
    "node_alt_designation": {
        "iri": f"{BASIC_DATA_IRI}hasAlternativeDesignation",
        "name": "hasAlternativeDesignation"
    },
    "node_street_code": {
        "iri": f"{BASIC_DATA_IRI}hasStreetCode",
        "name": "hasStreetCode"
    },
    "node_street_name": {
        "iri": f"{BASIC_DATA_IRI}hasStreetName",
        "name": "hasStreetName"
    },
    "node_district_code": {
        "iri": f"{BASIC_DATA_IRI}hasDistrictCode",
        "name": "hasDistrictCode"
    },
    "node_district_name": {
        "iri": f"{BASIC_DATA_IRI}hasDistrictName",
        "name": "hasDistrictName"
    },
    "node_municipality_code": {
        "iri": f"{BASIC_DATA_IRI}hasMunicipalityCode",
        "name": "hasMunicipalityCode"
    },
    "node_area_code": {
        "iri": f"{BASIC_DATA_IRI}hasAreaCode",
        "name": "hasAreaCode"
    },
    "node_catchment_area_code": {
        "iri": f"{BASIC_DATA_IRI}hasCatchmentAreaCode",
        "name": "hasCatchmentAreaCode"
    },
    "node_treatment_plant_number": {
        "iri": f"{BASIC_DATA_IRI}hasTreatmentPlantNumber",
        "name": "hasTreatmentPlantNumber"
    },
    "node_depth": {
        "iri": f"{BASIC_DATA_IRI}hasDepth",
        "name": "hasDepth"
    },
    "node_sewer_type": {
        "iri": f"{BASIC_DATA_IRI}hasSewerType",
        "name": "hasSewerType"
    },
    "node_sewer_usage": {
        "iri": f"{BASIC_DATA_IRI}hasSewerUsage",
        "name": "hasSewerUsage"
    },
    "node_year_construction": {
        "iri": f"{BASIC_DATA_IRI}hasYearOfConstruction",
        "name": "hasYearOfConstruction"
    },
    "node_material": {
        "iri": f"{BASIC_DATA_IRI}hasMaterial",
        "name": "hasMaterial"
    },
    "node_type": {
        "iri": f"{BASIC_DATA_IRI}hasNodeType",
        "name": "hasNodeType"
    },
    "node_structure_type": {
        "iri": f"{BASIC_DATA_IRI}hasNodeStructureType",
        "name": "hasNodeStructureType"
    },
    "node_shaft_shape": {
        "iri": f"{BASIC_DATA_IRI}hasNodeShaftShape",
        "name": "hasNodeShaftShape"
    },
    "node_shaft_length": {
        "iri": f"{BASIC_DATA_IRI}hasNodeShaftLength",
        "name": "hasNodeShaftLength"
    },
    "node_shaft_width": {
        "iri": f"{BASIC_DATA_IRI}hasNodeShaftWidth",
        "name": "hasNodeShaftWidth"
    },
    "node_cover_shape": {
        "iri": f"{BASIC_DATA_IRI}hasNodeCoverShape",
        "name": "hasNodeCoverShape"
    },
    "node_cover_material": {
        "iri": f"{BASIC_DATA_IRI}hasNodeCoverMaterial",
        "name": "hasNodeCoverMaterial"
    },
    "node_cover_class": {
        "iri": f"{BASIC_DATA_IRI}hasNodeCoverClass",
        "name": "hasNodeCoverClass"
    },
    "node_cover_width": {
        "iri": f"{BASIC_DATA_IRI}hasNodeCoverWidth",
        "name": "hasNodeCoverWidth"
    },
    "node_cover_length": {
        "iri": f"{BASIC_DATA_IRI}hasNodeCoverLength",
        "name": "hasNodeCoverLength"
    },
    "node_cover_bolted": {
        "iri": f"{BASIC_DATA_IRI}isNodeCoverBolted",
        "name": "isNodeCoverBolted"
    },
    "node_channel_shape": {
        "iri": f"{BASIC_DATA_IRI}hasNodeChannelShape",
        "name": "hasNodeChannelShape"
    },
    "node_channel_material": {
        "iri": f"{BASIC_DATA_IRI}hasNodeChannelMaterial",
        "name": "hasNodeChannelMaterial"
    },
    "node_channel_width": {
        "iri": f"{BASIC_DATA_IRI}hasNodeChannelWidth",
        "name": "hasNodeChannelWidth"
    },
    "node_channel_length": {
        "iri": f"{BASIC_DATA_IRI}hasNodeChannelLength",
        "name": "hasNodeChannelLength"
    },
    "node_bench_material": {
        "iri": f"{BASIC_DATA_IRI}hasNodeBenchMaterial",
        "name": "hasNodeBenchMaterial"
    },
    "node_internal_protection": {
        "iri": f"{BASIC_DATA_IRI}hasNodeInternalProtection",
        "name": "hasNodeInternalProtection"
    },
    "node_internal_protection_material": {
        "iri": f"{BASIC_DATA_IRI}hasNodeInternalProtectionMaterial",
        "name": "hasNodeInternalProtectionMaterial"
    },
    "node_climbing_aid": {
        "iri": f"{BASIC_DATA_IRI}hasNodeClimbingAid",
        "name": "hasNodeClimbingAid"
    },
    "node_number_climbing_irons": {
        "iri": f"{BASIC_DATA_IRI}hasNodeNumberOfClimbingIrons",
        "name": "hasNodeNumberOfClimbingIrons"
    },
    "node_climbing_aid_material": {
        "iri": f"{BASIC_DATA_IRI}hasNodeClimbingAidMaterial",
        "name": "hasNodeClimbingAidMaterial"
    },
    "node_measurement_technology": {
        "iri": f"{BASIC_DATA_IRI}hasNodeMeasurementTechnology",
        "name": "hasNodeMeasurementTechnology"
    },
    "node_functional_status": {
        "iri": f"{BASIC_DATA_IRI}hasFunctionalStatus",
        "name": "hasFunctionalStatus"
    },
    "node_ownership": {
        "iri": f"{BASIC_DATA_IRI}hasOwnership",
        "name": "hasOwnership"
    },
    "node_water_protection_zone": {
        "iri": f"{BASIC_DATA_IRI}hasWaterProtectionZone",
        "name": "hasWaterProtectionZone"
    },
    "node_traffic_area": {
        "iri": f"{BASIC_DATA_IRI}hasTrafficArea",
        "name": "hasTrafficArea"
    },
    "node_groundwater_level": {
        "iri": f"{BASIC_DATA_IRI}hasGroundwaterLevel",
        "name": "hasGroundwaterLevel"
    },
    "node_flood_area": {
        "iri": f"{BASIC_DATA_IRI}hasFloodArea",
        "name": "hasFloodArea"
    },
    "node_data_status": {
        "iri": f"{BASIC_DATA_IRI}hasDataStatus",
        "name": "hasDataStatus"
    },
    "node_flooding_frequency": {
        "iri": f"{BASIC_DATA_IRI}hasFloodingFrequency",
        "name": "hasFloodingFrequency"
    },
    "node_soil_group": {
        "iri": f"{BASIC_DATA_IRI}hasSoilGroup",
        "name": "hasSoilGroup"
    },

    ### PIPE SECTION BASIC DATA PROPERTIES ###
    ## Excel Rows 3-54: Shared Data Properties with KG
    "pipe_section_designation": {
        "iri": f"{BASIC_DATA_IRI}hasDesignation",
        "name": "hasDesignation"
    },
    "pipe_section_alt_designation": {
        "iri": f"{BASIC_DATA_IRI}hasAlternativeDesignation",
        "name": "hasAlternativeDesignation"
    },
    "pipe_section_street_code": {
        "iri": f"{BASIC_DATA_IRI}hasStreetCode",
        "name": "hasStreetCode"
    },
    "pipe_section_street_name": {
        "iri": f"{BASIC_DATA_IRI}hasStreetName",
        "name": "hasStreetName"
    },
    "pipe_section_district_code": {
        "iri": f"{BASIC_DATA_IRI}hasDistrictCode",
        "name": "hasDistrictCode"
    },
    "pipe_section_district_name": {
        "iri": f"{BASIC_DATA_IRI}hasDistrictName",
        "name": "hasDistrictName"
    },
    "pipe_section_municipality_code": {
        "iri": f"{BASIC_DATA_IRI}hasMunicipalityCode",
        "name": "hasMunicipalityCode"
    },
    "pipe_section_area_code": {
        "iri": f"{BASIC_DATA_IRI}hasAreaCode",
        "name": "hasAreaCode"
    },
    "pipe_section_catchment_area_code": {
        "iri": f"{BASIC_DATA_IRI}hasCatchmentAreaCode",
        "name": "hasCatchmentAreaCode"
    },
    "pipe_section_treatment_plant_number": {
        "iri": f"{BASIC_DATA_IRI}hasTreatmentPlantNumber",
        "name": "hasTreatmentPlantNumber"
    },
    "pipe_section_sewer_type": {
        "iri": f"{BASIC_DATA_IRI}hasSewerType",
        "name": "hasSewerType"
    },
    "pipe_section_sewer_usage": {
        "iri": f"{BASIC_DATA_IRI}hasSewerUsage",
        "name": "hasSewerUsage"
    },
    "pipe_section_year_construction": {
        "iri": f"{BASIC_DATA_IRI}hasYearOfConstruction",
        "name": "hasYearOfConstruction"
    },
    "pipe_section_material": {
        "iri": f"{BASIC_DATA_IRI}hasMaterial",
        "name": "hasMaterial"
    },

    "pipe_section_depth": {
        "iri": f"{BASIC_DATA_IRI}hasDepth",
        "name": "hasDepth"
    }, 

    "pipe_section_functional_status": {
        "iri": f"{BASIC_DATA_IRI}hasFunctionalStatus",
        "name": "hasFunctionalStatus"
    },
    "pipe_section_owner": {
        "iri": f"{BASIC_DATA_IRI}hasOwner",
        "name": "hasOwner"
    },
    "pipe_section_water_protection_zone": {
        "iri": f"{BASIC_DATA_IRI}hasWaterProtectionZone",
        "name": "hasWaterProtectionZone"
    },
    "pipe_section_traffic_area": {
        "iri": f"{BASIC_DATA_IRI}hasTrafficArea",
        "name": "hasTrafficArea"
    },
    "pipe_section_groundwater_level": {
        "iri": f"{BASIC_DATA_IRI}hasGroundwaterLevel",
        "name": "hasGroundwaterLevel"
    },
    "pipe_section_flood_area": {
        "iri": f"{BASIC_DATA_IRI}hasFloodArea",
        "name": "hasFloodArea"
    },
    "pipe_section_data_status": {
        "iri": f"{BASIC_DATA_IRI}hasDataStatus",
        "name": "hasDataStatus"
    },
    "pipe_section_flooding_frequency": {
        "iri": f"{BASIC_DATA_IRI}hasFloodingFrequency",
        "name": "hasFloodingFrequency"
    },
    "pipe_section_soil_group": {
        "iri": f"{BASIC_DATA_IRI}hasSoilGroup",
        "name": "hasSoilGroup"
    },
    "pipe_section_document": {
        "iri": f"{BASIC_DATA_IRI}hasDocument",
        "name": "hasDocument"
    },
    "pipe_section_remarks": {
        "iri": f"{BASIC_DATA_IRI}hasRemarks",
        "name": "hasRemarks"
    },

    ### PIPE SECTION SPECIFIC: BASIC DATA PROPERTIES ###
    ## Excel Rows 57-82: Pipe Section Specific: Basic Data
    "pipe_section_profile_type": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionProfileType",
        "name": "hasPipeSectionProfileType"
    },
    "pipe_section_profile_width": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionProfileWidth",
        "name": "hasPipeSectionProfileWidth"
    },
    "pipe_section_profile_height": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionProfileHeight",
        "name": "hasPipeSectionProfileHeight"
    },
    "pipe_section_profile_lining": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionProfileLining",
        "name": "hasPipeSectionProfileLining"
    },
    "pipe_section_profile_lining_material": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionProfileLiningMaterial",
        "name": "hasPipeSectionProfileLiningMaterial"
    },
    "pipe_section_length": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionLength",
        "name": "hasPipeSectionLength"
    },
    "pipe_section_gradient": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionGradient",
        "name": "hasPipeSectionGradient"
    },

    "pipe_section_object_type": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionObjectType",
        "name": "hasPipeSectionObjectType"
    },
    "pipe_section_connecting_pipe_stationing": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionConnectingPipeStationing",
        "name": "hasPipeSectionConnectingPipeStationing"
    },
    "pipe_section_connecting_pipe_stationing_direction": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionConnectingPipeStationingDirection",
        "name": "hasPipeSectionConnectingPipeStationingDirection"
    },
    "pipe_section_connecting_pipe_positioning": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionConnectingPipePositioning",
        "name": "hasPipeSectionConnectingPipePositioning"
    },
    "pipe_section_end_point_type": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionEndPointType",
        "name": "hasPipeSectionEndPointType"
    },
    "pipe_section_pipeline_designation": {
        "iri": f"{BASIC_DATA_IRI}isChildOf",
        "name": "isChildOf"
    },
    "pipe_section_type": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionType",
        "name": "hasPipeSectionType"
    },
    "pipe_section_pipe_length": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionPipeLength",
        "name": "hasPipeSectionPipeLength"
    },
    "pipe_section_status_profile_detail": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionStatusProfileDetail",
        "name": "hasPipeSectionStatusProfileDetail"
    },
    "pipe_section_self_supporting_lining": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionSelfSupportingLining",
        "name": "hasPipeSectionSelfSupportingLining"
    },
    "pipe_section_wall_thickness": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionWallThickness",
        "name": "hasPipeSectionWallThickness"
    },
    "pipe_section_bedding_type": {
        "iri": f"{BASIC_DATA_IRI}hasPipeSectionBeddingType",
        "name": "hasPipeSectionBeddingType"
    },

}

# List of keys that should be converted to float
NUMERIC_KEYS = [
    "node_depth",
    "schacht_laenge",
    "schacht_breite",
    "profil_breite",
    "profil_hoehe",
    "rohr_laenge",
    "neigung"
]