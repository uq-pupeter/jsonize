from __future__ import annotations
from enum import Enum
from typing import Tuple


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

    def __str__(self) -> str:
        return self.raw_xpath

    def __repr__(self) -> str:
        return self.raw_xpath