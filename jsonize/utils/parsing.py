from jsonize import XMLNodeToJSONNode, XMLNode, XMLNodeType, JSONNode, JSONNodeType, Transformation
from typing import Dict, List, Optional


def parse_node_map(node_map: Dict, transformations: List[Transformation]) -> XMLNodeToJSONNode:
    """
    Parses a serialized JSON (Python dictionary) defining a Jsonize node map and creates
    its corresponding XMLNodeToJSONNode mapping.
    :param node_map: A dictionary containing the serialized representation of a JSON NodeMap as specified in Jsonize Schema.
    :param transformations: A list of Transformation from which the
    :return:
    """
    from_xml_node = XMLNode(node_map['from']['path'], XMLNodeType[node_map['from']['type']])
    to_json_node = JSONNode(node_map['to']['path'], JSONNodeType[node_map['to']['type']])
    try:
        unparsed_item_mappings = node_map['itemMappings']
        item_mappings = [parse_node_map(item_mapping, transformations) for item_mapping in unparsed_item_mappings]  # type: Optional[List[XMLNodeToJSONNode]]
    except KeyError:
        item_mappings = None
    try:
        transformation_name = node_map['transformation']  # type: Optional[str]
    except KeyError:
        transformation_name = ''

    if transformation_name:
        try:
            transformation = [transf for transf in transformations if transf.name == transformation_name][0]
        except IndexError:
            raise ValueError(f'The transformation with name "{transformation_name}" cannot be found in the "transformations" parameter.')
    else:
        transformation = None

    parsed_node_map = XMLNodeToJSONNode(from_xml_node=from_xml_node,
                                        to_json_node=to_json_node,
                                        item_mappings=item_mappings,
                                        transform=transformation)
    return parsed_node_map


def parse(jsonize_map: List[Dict], transformations: Optional[List[Transformation]]=None) -> List[XMLNodeToJSONNode]:
    """
    Produces a list of XMLNodeToJSONNode mappings from the Python serialization of a Jsonize map.
    A Jsonize map is defined as an instance of jsonize-map.schema.json.
    :param jsonize_map: A Python serialized Jsonize map, for example, the output of json.load function when given the
    a Jsonize map defined in JSON.
    :param transformations: A list of Transformation that are used in the jsonize map.
    :return: A list of XMLNodeToJSONNode that defines the XML to JSON mapping.
    """
    if transformations is None:
        transformations = []
    node_mappings = [parse_node_map(mapping, transformations) for mapping in jsonize_map]
    return node_mappings