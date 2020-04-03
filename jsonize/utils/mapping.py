from __future__ import annotations
from json import load
from pathlib import Path
from xml.etree import ElementTree as etree
from jsonize.utils.xml import XMLNode, XMLNodeType, XPath
from jsonize.utils.json import JSONNode, JSONNodeType, JSONPath, write_item_in_path
from typing import Dict, List, Optional, Callable, Iterable


class Transformation:
    """
    Class containing a named definition of a transformation that is applied onto the value of an XML Node
    before mapping it into a JSON Node.
    """
    def __init__(self, name: str, transformation: Callable):
        self.name = name
        self.transformation = transformation

    def __call__(self, input):
        return self.transformation(input)


class XMLNodeToJSONNode:
    """
    Class defining the mapping from an XMLNode to a JSONNode. A mapping is defined by providing the input XMLNode, the output JSONNode and an optional transform
    function that is to be applied to the input.
    When the input XMLNode is an XML sequence it accepts an item_mappings parameter that defines how each element of the sequence is to be mapped into an item
    in the JSON array.
    :param from_xml_node: The input XML Node, defined by an XPath and the type of XML node ('element', 'attribute', 'sequence').
    :param to_json_node: The output JSON node to which the input is to be mapped, defined by a JSONPath and and the its type ('string', 'integer', 'number',
    'array', 'boolean').
    :param transform: An optional function that takes only one value as input and produces one value as output, it is used to transform the input before writing
    it to the JSON serializable dictionary. It can be used for string manipulation, unit conversion, type casting, etc...
    :param item_mappings: An iterable of XMLNodeToJSONNode that defines how each item of a JSON array is to be built from each element in an XML sequence.
    """

    def __init__(self, from_xml_node: XMLNode, to_json_node: JSONNode, transform: Optional[Callable] = None,
                 item_mappings: Optional[Iterable[XMLNodeToJSONNode]] = None):
        self.from_xml_node = from_xml_node
        self.to_json_node = to_json_node
        self.transform = transform
        if item_mappings is None:
            item_mappings = []
        self.item_mappings = item_mappings

    def map(self, xml_etree: etree.ElementTree, json: Dict, xml_namespaces: Dict = None) -> Dict:
        """
        Maps the XMLNode from xml_etree into the given json serializable dictionary.
        :param xml_etree: An XML ElementTree from which the input XMLNode is to be taken. If the XMLNode is not found in the xml_etree it will be defaulted to
        None.
        :param json: The JSON serializable dictionary onto which the input is to be mapped.
        :param xml_namespaces: A dictionary defining the XML namespaces used in the xml_etree, if they are used they must be provided to find the XMLNode via
        its XPath expression.
        :return: The JSON serializable dictionary with the input XMLNode mapped.
        """
        if self.from_xml_node.node_type == XMLNodeType['value']:
            xml_element = xml_etree.find(self.from_xml_node.path, xml_namespaces)
            try:
                input_value = xml_element.text
            except AttributeError:
                input_value = None
        elif self.from_xml_node.node_type == XMLNodeType['attribute']:
            attribute_path = XPath(self.from_xml_node.path)
            parent_element_path = attribute_path.parent()
            attribute_name = attribute_path.attribute_name()
            if ':' in attribute_name:
                ns_separator_loc = attribute_name.find(':')
                short_ns = attribute_name[:ns_separator_loc]
                expanded_ns = xml_namespaces[short_ns]
                attribute_name = '{' + expanded_ns + '}' + attribute_name[ns_separator_loc + 1:]
            parent_element = xml_etree.find(str(parent_element_path), xml_namespaces)
            try:
                input_value = parent_element.attrib[attribute_name]
            except (KeyError, AttributeError):
                input_value = None
        elif self.from_xml_node.node_type == XMLNodeType['sequence']:
            if not self.item_mappings:
                raise ValueError("An item_mapping must be provided for an XML node of type 'sequence'.")
            input_value = xml_etree.findall(self.from_xml_node.path, xml_namespaces)
        else:
            raise NotImplementedError(f"Mapping not implemented for: {self.from_xml_node.node_type}")

        if self.transform:
            input_value = self.transform(input_value)
        if input_value is None:
            return json

        if self.to_json_node.node_type == JSONNodeType['string']:
            return write_item_in_path(input_value, JSONPath(self.to_json_node.path), json)
        if self.to_json_node.node_type == JSONNodeType['integer']:
            try:
                return write_item_in_path(int(input_value), JSONPath(self.to_json_node.path), json)
            except ValueError as e:
                raise ValueError(f'The node at {self.from_xml_node.path} is not castable into int', e.args[0])
        if self.to_json_node.node_type == JSONNodeType['number']:
            try:
                return write_item_in_path(float(input_value), JSONPath(self.to_json_node.path), json)
            except ValueError as e:
                raise ValueError(f'The node at {self.from_xml_node.path} is not castable into float', e.args[0])
        if self.to_json_node.node_type == JSONNodeType['boolean']:
            if input_value == 'true':
                value = True
            elif input_value == 'false':
                value = False
            else:
                raise ValueError(f'The node at {self.from_xml_node.path} with value {input_value} is not castable into a boolean. '
                                 f'Only "true" and "false" are valid XML boolean values.')
            return write_item_in_path(value, JSONPath(self.to_json_node.path), json)
        if self.to_json_node.node_type == JSONNodeType['array']:
            items = []
            for element in input_value:
                item = {}
                for mapping in self.item_mappings:
                    item = mapping.map(element, item, xml_namespaces)
                items.append(item)
            return write_item_in_path(items, JSONPath(self.to_json_node.path), json)
        if self.to_json_node.node_type == JSONNodeType['object']:
            item = {}
            for mapping in self.item_mappings:
                item = mapping.map(input_value, json, xml_namespaces)
            return write_item_in_path(item, JSONPath(self.to_json_node.path), json)


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


def xml_document_to_json(xml_document: Path,
                         jsonize_map_document: Optional[Path]=None, jsonize_map: Optional[Iterable[XMLNodeToJSONNode]]=None,
                         xml_namespaces: Dict = None, json: Optional[Dict] = None,
                         transformations: Optional[Iterable[Transformation]]=None) -> Dict:
    """
    Transforms an XML document into a JSON serializable dictionary.
    :param jsonize_map: An iterable of XMLNodeToJSONNode defining the mappings from each node in the XML document to the JSON file.
    :param xml_document: A Path to the XML document that is to be converted.
    :param xml_namespaces: A dictionary defining the XML namespaces with namespace shortname as keys and the full namespace name as values.
    :param json: An input dictionary into which the XML document is to be mapped. Defaults to an empty dictionary if none given.
    :return: A JSON serializable dictionary containing the items defined in the mappings extracted from the xml_document.
    """
    if transformations is None:
        transformations = []

    if not jsonize_map:
        try:
            assert jsonize_map_document is not None
        except AssertionError:
            raise ValueError('Jsonize map missing. Must be provided either via the parameter "jsonize_map_document" or "jsonize_map".')
        with jsonize_map_document.open('r') as jsonize_map_file:
            jsonize_map = parse(load(jsonize_map_file), transformations)

    if not json:
        json = {}

    result = json
    xml_etree = etree.parse(str(xml_document))
    for mapping in jsonize_map:
        result = mapping.map(xml_etree, result, xml_namespaces=xml_namespaces)
    return result