from __future__ import annotations
from enum import Enum
from typing import Tuple


class XMLNodeType(Enum):
    value = 1
    sequence = 2
    attribute = 3


class XMLNode():
    def __init__(self, xpath: str, node_type: XMLNodeType):
        self.path = xpath
        self.node_type = node_type


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