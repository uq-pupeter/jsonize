from __future__ import annotations
import xml.etree.ElementTree as etree
from jsonize.xml.utils import XMLNode, XMLNodeType, XPath
from pathlib import Path
from jsonize.json.utils import JSONNode, JSONNodeType, JSONPath, write_item_in_path
from typing import Optional, Callable, Dict, Iterable


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
            xml_sequence = xml_etree.findall(self.from_xml_node.path, xml_namespaces)
            input_value = []
            for xml_element in xml_sequence:
                item = {}
                for mapping in self.item_mappings:
                    item = mapping.map(xml_element, item, xml_namespaces)
                input_value.append(item)
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
            return write_item_in_path(input_value, JSONPath(self.to_json_node.path), json)


def xml_document_to_json(mappings: Iterable[XMLNodeToJSONNode], xml_document: Path, xml_namespaces: Dict = None, json: Optional[Dict] = None) -> Dict:
    """
    Transforms an XML document into a JSON serializable dictionary.
    :param mappings: An iterable of XMLNodeToJSONNode defining the mappings from each node in the XML document to the JSON file.
    :param xml_document: A Path to the XML document that is to be converted.
    :param xml_namespaces: A dictionary defining the XML namespaces with namespace shortname as keys and the full namespace name as values.
    :param json: An input dictionary into which the XML document is to be mapped. Defaults to an empty dictionary if none given.
    :return: A JSON serializable dictionary containing the items defined in the mappings extracted from the xml_document.
    """
    if not json:
        json = {}
    result = json
    xml_etree = etree.parse(str(xml_document))
    for mapping in mappings:
        result = mapping.map(xml_etree, result, xml_namespaces=xml_namespaces)
    return result
