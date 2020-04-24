from __future__ import annotations
from enum import Enum
from typing import Tuple, Dict, Iterable, Union, List
from .json import JSONPath
from xml.etree import ElementTree
import re


class XMLNodeType(Enum):
    value = 1
    sequence = 2
    attribute = 3


class XMLNode():
    """
    A class representing a XML node, defined by its XPath and an XMLNodeType.
    :param xpath: The XPath of the XML node.
    :param node_type: The XMLNodeType of the XML node.
    """
    def __init__(self, xpath: Union[str, XPath], node_type: XMLNodeType):
        self.path = XPath(str(xpath))
        self.node_type = node_type

    def __repr__(self):
        return f'XML {self.node_type.name} at {self.path}'

    def __eq__(self, other):
        return other and other.path == self.path and other.node_type == self.node_type

    def __hash__(self):
        return hash((self.path, self.node_type.value))

    def relative_to(self, ancestor: XMLNode, in_place: bool = True) -> Union[None, XMLNode]:
        """
        Makes the XMLNode's XPath relative to a given ancestor.
        :param ancestor: An XMLNode to which we want to make the current one relative to.
        :param in_place: If True the current instance will be updated (returns None). If False, a new one will be created with the result
        of the relative path (returns an XMLNode instance with the relative XPath).
        :return: None or a new instance of XMLNode with the relative path, as defined by the in_place parameter.
        """
        if in_place:
            self.path.relative_to(ancestor=ancestor.path, in_place=in_place)
            return None
        else:
            return self.__class__(str(self.path.relative_to(ancestor=ancestor.path, in_place=False)), self.node_type)

    def is_descendant(self, ancestor: XMLNode) -> bool:
        """
        Determines if the current XMLNode is a descendant of a given ancestor.
        :param ancestor: XMLNode of which we want to determine if the current one is a descendant.
        :return: True if the node is a descendant of ancestor, False otherwise.
        """
        return self.path.is_descendant(ancestor.path)

    def is_leaf(self, tree: Iterable[XMLNode]) -> bool:
        """
        Determines if the current XMLNode is a leaf with respect to an iterable of XMLNode defining the tree it belongs to.
        Determining if a particular node is a leaf can only be done in comparison with the entire XMl tree, hence in the tree
        parameter we must pass an iterable of all the XMLNodes of the XML.
        :param tree: An iterable of XMLNode containing each node of the XML tree.
        :return: True if the current node is not an ancestor of any of the XMLNode in the tree, False otherwise.
        """
        if self.node_type == XMLNodeType['attribute']:
            return True
        else:
            return not any([parent_node.is_descendant(self) for parent_node in tree])

    def to_jsonize(self, attributes: str = '', namespaces: str = 'preserve') -> Dict:
        """
        Infers a Jsonize mapping from the XMLNode. It does so by creating a direct translation of the XPath into JSONPath
        that can be fine-tuned via the 'attributes' and 'namespaces' parameters.
        The JSON type is set to 'infer' which make Jsonize attempt to find the best JSON type for the input data.
        :param attributes: Defines the tag that will precede an XML attribute name in JSONPath. It defaults to an empty
        string, resulting in no difference in the representation of XML elements and attributes into JSON. Can be used to define your own convention.
        E.g. the following XPath '/element/subelement/@attribute will be transformed as follows:
                '': $.element.subelement.attribute
                '_': $.element.subelement._attribute
                '@': $.element.subelement.@attribute
        :param namespaces: Defines how XML namespaces will be handled. It can take the values 'preserve' and 'ignore'. It defaults to 'preserve',
        resulting in shortened namespaces being kept in the JSONPath. The value 'ignore' will drop them in the conversion to JSONPath.
        E.g. the following XPath '/ns:element/nss:subelement will be transformed as follows:
                'preserve': $.ns:element.nss:subelement
                'ignore': $.element.subelement
        The value 'ignore' should be used with caution as it may result in name collisions.
        :return: A dictionary containing the Jsonize mapping of the XMLNode.
        """
        jsonize = {'from': {'path': str(self.path),
                            'type': self.node_type.name},
                   'to': {'path': str(self.path.to_json_path(attributes=attributes, namespaces=namespaces)),
                          'type': 'infer'}}
        return jsonize


class XMLSequenceNode(XMLNode):
    """
    Specialization of an XMLNode to a sequence of XML nodes.
    :param xpath: The XPath of the XML node.
    :param node_type: The XMLNodeType of the XML node.
    :param sub_nodes: An iterable of XML nodes that are contained in each item of the XML sequence.
    """
    def __init__(self, xpath: Union[str, XPath], node_type: XMLNodeType, sub_nodes: Iterable[XMLNode]):
        super().__init__(xpath=xpath, node_type=node_type)
        if not self.node_type == XMLNodeType['sequence']:
            raise ValueError('Incorrect node_type, an XMLNodeType "sequence" is expected.')
        self.sub_nodes = [node.relative_to(self) for node in sub_nodes]

    def relative_to(self, ancestor: XMLNode, in_place: bool = True) -> Union[None, XMLNode]:
        """
        Makes the XMLNode's XPath relative to a given ancestor.
        :param ancestor: An XMLNode to which we want to make the current one relative to.
        :param in_place: If True the current instance will be updated (returns None). If False, a new one will be created with the result
        of the relative path (returns an XMLNode instance with the relative XPath).
        :return: None or a new instance of XMLNode with the relative path, as defined by the in_place parameter.
        """
        if in_place:
            self.path.relative_to(ancestor=ancestor.path, in_place=in_place)
            return None
        else:
            return self.__class__(str(self.path.relative_to(ancestor=ancestor.path, in_place=False)), self.node_type, self.sub_nodes)

    def to_jsonize(self, attributes: str = '', namespaces: str = 'preserve'):
        """
        Infers a Jsonize mapping from the XMLSequenceNode. It does so by creating a direct translation of the XPath into JSONPath
        that can be fine-tuned via the 'attributes' and 'namespaces' parameters.
        The JSON type is set to 'array' as it's the natural match of an XMLSequence.
        :param attributes: Defines the tag that will precede an XML attribute name in JSONPath. It defaults to an empty
        string, resulting in no difference in the representation of XML elements and attributes into JSON. Can be used to define your own convention.
        E.g. the following XPath '/element/subelement/@attribute will be transformed as follows:
                '': $.element.subelement.attribute
                '_': $.element.subelement._attribute
                '@': $.element.subelement.@attribute
        :param namespaces: Defines how XML namespaces will be handled. It can take the values 'preserve' and 'ignore'. It defaults to 'preserve',
        resulting in shortened namespaces being kept in the JSONPath. The value 'ignore' will drop them in the conversion to JSONPath.
        E.g. the following XPath '/ns:element/nss:subelement will be transformed as follows:
                'preserve': $.ns:element.nss:subelement
                'ignore': $.element.subelement
        The value 'ignore' should be used with caution as it may result in name collisions.
        :return: A dictionary containing the Jsonize mapping of the XMLNode.
        """
        jsonize = {'from': {'path': str(self.path),
                            'type': self.node_type.name},
                   'to': {'path': str(self.path.to_json_path(attributes=attributes, namespaces=namespaces)),
                          'type': 'array'}
                   }
        if self.sub_nodes:
            jsonize['itemMappings'] = [sub_node.to_jsonize(attributes=attributes, namespaces=namespaces) for sub_node in self.sub_nodes]
        else:
            # If there are no sub_nodes then we create a single sub_node pointing to the value of each XML element in the sequence.
            jsonize['itemMappings'] = [
                {'from': {'path': '.',
                          'type': XMLNodeType['value']},
                 'to': {'path': '@',
                        'type': 'infer'}
                 }
            ]
        return jsonize


class XPath():
    """
    Class representing an XPath.
    :param xpath: The string representation of the xpath.
    """

    def __init__(self, xpath: str):
        self.raw_xpath = xpath

    def _xpath_structure(self):
        xpath_structure = self.raw_xpath.split('/')
        return xpath_structure

    def is_absolute(self) -> bool:
        """
        :return: Boolean indicating if the XPath is absolute.
        """
        return self.raw_xpath[0] == '/'

    def is_relative(self) -> bool:
        """
        :return: Boolean indicating if the XPath is relative.
        """
        return '.' in self._xpath_structure()[0]

    def is_attribute(self) -> bool:
        """
        :return: Boolean indicating if the XPath refers to an attribute node.
        """
        return self._xpath_structure()[-1][0] == '@'

    def is_descendant(self, ancestor: XPath) -> bool:
        """
        Determines if the current XPath is a descendant of a given ancestor.
        :param ancestor: XPath of a node of which we want to determine if the current one is a descendant.
        :return: True if the node is a descendant of ancestor, False otherwise.
        """
        if ancestor.raw_xpath in self.raw_xpath and not self == ancestor:
            return True
        else:
            return False

    def attribute_name(self) -> str:
        """
        :return: Name of the attribute node.
        :raises ValueError: If the XPath does not refer to an attribute node.
        """
        if not self.is_attribute():
            raise ValueError('The given xpath does not refer to an attribute.')
        return self._xpath_structure()[-1][1:]

    def parent(self) -> XPath:
        """
        :return: An XPath representation of the parent element.
        """
        return XPath('/'.join(self._xpath_structure()[:-1]))

    def split(self, at: int) -> Tuple[XPath, XPath]:
        """
        Produces an absolute and a relative Xpath by splitting the current one at the given index location.
        :param at: Index position where to split the XPath.
        :return: Tuple of XPath, the first one being the absolute path before the split at location
        and the second one the relative XPath after the split location.
        """
        return XPath('/'.join(self._xpath_structure()[:at])), XPath('/'.join(['.'] + self._xpath_structure()[at:]))

    def to_json_path(self, attributes: str = '', namespaces: str = 'preserve') -> JSONPath:
        """
        Infers a JSONPath representation for the XPath.
        :param attributes: Defines the tag that will precede an XML attribute name in JSONPath. It defaults to an empty
        string, resulting in no difference in the representation of XML elements and attributes into JSON. Can be used to define your own convention.
        E.g. the following XPath '/element/subelement/@attribute will be transformed as follows:
                '': $.element.subelement.attribute
                '_': $.element.subelement._attribute
                '@': $.element.subelement.@attribute
        :param namespaces: Defines how XML namespaces will be handled. It can take the values 'preserve' and 'ignore'. It defaults to 'preserve',
        resulting in shortened namespaces being kept in the JSONPath. The value 'ignore' will drop them in the conversion to JSONPath.
        E.g. the following XPath '/ns:element/nss:subelement will be transformed as follows:
                'preserve': $.ns:element.nss:subelement
                'ignore': $.element.subelement
        The value 'ignore' should be used with caution as it may result in name collisions.
        :return: A JSONPath representation of the XPath.
        """
        if namespaces == 'ignore':
            json_path = re.sub(r'[a-zA-Z]+:', '', self.raw_xpath)
        else:
            json_path = self.raw_xpath
        json_path = re.sub(r'/@', '/' + attributes, json_path)
        json_path = re.sub(r'^\./', '@/', json_path)
        json_path = re.sub(r'^/', '$/', json_path)
        json_path = re.sub(r'/', '.', json_path)
        return JSONPath(json_path)

    def relative_to(self, ancestor: XPath, in_place: bool = True) -> Union[None, XPath]:
        """
        Makes the XPath relative to a given ancestor.
        :param ancestor: An XPath to which we want to make the current one relative to.
        :param in_place: If True the current instance will be updated (returns None). If False, a new one will be created with the result
        of the relative path (returns an XPath instance with the relative XPath).
        :return: None or a new instance of XPath with the relative path, as defined by the in_place parameter.
        """
        if in_place:
            self.raw_xpath = re.sub(r'^{}'.format(re.escape(str(ancestor))), '.', self.raw_xpath)
            return None
        else:
            return XPath(re.sub(r'^{}'.format(re.escape(str(ancestor))), '.', self.raw_xpath))

    def shorten_namespaces(self, xml_namespaces: Dict[str, str], in_place: bool = True) -> Union[None, XPath]:
        if in_place:
            self.raw_xpath = re.sub(r'\{([^\}]+)\}', lambda x: get_short_namespace(x.group(1), xml_namespaces) + ':', self.raw_xpath)
            return None
        else:
            return XPath(re.sub(r'\{([^\}]+)\}', lambda x: get_short_namespace(x.group(1), xml_namespaces) + ':', self.raw_xpath))

    def remove_indices(self, in_place: bool = True) -> Union[None, XPath]:
        """
        Removes the XPath indices that are present in elements part of an XML sequence. i.e. '/element/subelement[2]/subsubelement[10]' becomes
        '/element/subelement/subsubelement'.
        :param in_place: If True the current instance will be updated (returns None). If False, a new one will be created with the result
        of the relative path (returns an XPath instance with the XPath without indices).
        :return: None or a new instance of XPath with the new XPath with indices removed, as defined by the in_place parameter.
        """
        if in_place:
            self.raw_xpath = re.sub(r'\[[0-9]+\]', '', self.raw_xpath)
            return None
        else:
            return XPath(re.sub(r'\[[0-9]+\]', '', self.raw_xpath))

    def _infer_node_type(self) -> XMLNodeType:
        """
        Attempts to infer the type of XML node from the XPath.
        A number of assumptions are needed for this inference to work. In particular:
            - Must be used on leaf nodes, XPath doesn't distinguish between the XML value inside and element and the element itself.
            In Jsonize we are interested in the values present at leaves, so whenever we identify an element we will assume it represents the value of a leaf.
            - Indices of sequences must have not been removed, as they will be used to determine that the element is part of a sequence.
        Because of these assumptions this method should be used with care, knowing what you are doing or under the supervision of an adult.
        It's made private, as to not be exposed in the public interface of the class. If needed, use judiciously.
        :return: XMLNodeType that is inferred from the XPath.
        """
        structured_path = self._xpath_structure()
        if '@' in structured_path[-1]:
            type = XMLNodeType['attribute']
        elif re.search(r'\[[0-9]+\]', structured_path[-1]):
            type = XMLNodeType['sequence']
        else:
            type = XMLNodeType['value']
        return type

    def __str__(self) -> str:
        return self.raw_xpath

    def __repr__(self) -> str:
        return self.raw_xpath

    def __hash__(self):
        return hash(self.raw_xpath)

    def __eq__(self, other: XPath):
        if isinstance(other, XPath):
            return other.raw_xpath == self.raw_xpath
        else:
            return False


class XMLNodeTree():
    """
    A representation of an XML node tree, organized around sequences and leaves. The whole XML structure is expressed
    as XML leaf nodes and XML sequences, if any, serve as branch points in the tree.
    This mimics the Jsonize mapping structure and is used to infer the Jsonize mapping of a given XML.
    :param nodes: An iterable of XMLNode.
    """
    def __init__(self, nodes: Iterable[XMLNode] = None):
        if nodes is not None:
            self.nodes = nodes
        else:
            self.nodes = []

    def to_jsonize(self, attributes: str = '', namespaces: str = 'preserve'):
        jsonize = [node.to_jsonize(attributes=attributes, namespaces=namespaces) for node in self.nodes]
        return jsonize


def get_short_namespace(full_ns: str, xml_namespaces: Dict[str, str]) -> str:
    for key, value in xml_namespaces.items():
        if full_ns == value:
            return key
    raise KeyError('The namespace is not found in "xml_namespaces".', full_ns)


def generate_node_xpaths(root: ElementTree, xml_namespaces: Dict[str, str] = None) -> Iterable[XPath]:
    all_elements = root.iterfind('//*')  # type: Iterable[ElementTree]
    for element in all_elements:
        element_path = root.getpath(element)
        attribs = (element_path + '/@' + attrib_name for attrib_name, _ in element.attrib.items())
        yield XPath(element_path).shorten_namespaces(xml_namespaces, in_place=False)
        for attrib in attribs:
            yield XPath(attrib).shorten_namespaces(xml_namespaces, in_place=False)


def generate_nodes(tree: ElementTree, xml_namespaces: Dict[str, str] = None) -> Iterable[XMLNode]:
    root = tree.getroot()
    root_xpath = XPath(tree.getpath(root))
    for xpath in generate_node_xpaths(tree, xml_namespaces):
        relative_xpath = xpath.relative_to(root_xpath, in_place=False)
        cleaned_xpath = relative_xpath.remove_indices(in_place=False)
        yield XMLNode(xpath=cleaned_xpath, node_type=xpath._infer_node_type())


def build_sequence_tree(sequence_nodes: List[XMLNode], leaf_nodes: List[Union[XMLNode, XMLSequenceNode]]) -> Tuple[List[XMLNode], List[XMLNode]]:
    if not sequence_nodes:
        return sequence_nodes, leaf_nodes

    trimmed_sequence_indices = []
    trimmed_leaf_indices = []
    deepest_sequences = []
    for i, node in enumerate(sequence_nodes):
        if node.is_leaf(sequence_nodes):
            sequence_node_leaves = []
            for ix, leaf in enumerate(leaf_nodes):
                if leaf.is_descendant(node):
                    sequence_node_leaves.append(leaf)
                    trimmed_leaf_indices.append(ix)
            trimmed_sequence_indices.append(i)
            sequence = XMLSequenceNode(node.path, XMLNodeType['sequence'], sub_nodes=sequence_node_leaves)  # type: XMLSequenceNode
            deepest_sequences.append(sequence)

    trimmed_sequence_nodes = [node for i, node in enumerate(sequence_nodes) if i not in trimmed_sequence_indices]
    trimmed_leaf_nodes = [node for i, node in enumerate(leaf_nodes) if i not in trimmed_leaf_indices]
    return build_sequence_tree(trimmed_sequence_nodes, trimmed_leaf_nodes + deepest_sequences)


def build_node_tree(tree: ElementTree, xml_namespaces: Dict[str, str] = None) -> XMLNodeTree:
    root_xpath = XPath(tree.getpath(tree.getroot()))
    all_nodes = set(generate_nodes(tree, xml_namespaces))
    sequence_node_xpaths = set(node_xpath.remove_indices(in_place=True).relative_to(root_xpath)
                               for node_xpath in generate_node_xpaths(tree, xml_namespaces)
                               if node_xpath._infer_node_type() == XMLNodeType['sequence'])
    leaves = list(node for node in all_nodes if node.is_leaf(all_nodes) and node.node_type != XMLNodeType['sequence'])
    sequences = []
    for sequence_xpath in sequence_node_xpaths:
        sequence = XMLNode(sequence_xpath, XMLNodeType['sequence'])
        sequences.append(sequence)

    return XMLNodeTree(nodes=build_sequence_tree(sequences, leaves)[1])
