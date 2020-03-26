from __future__ import annotations
from enum import Enum
from copy import deepcopy
from typing import Dict, Any, Union, List


class JSONPath():
    """
    Class representing a JSONPath using the dot notation.
    It supports absolute and relative paths, e.g.:
    '$.store.book.author' represents an absolute JSONPath
    '@.author.lastName' represent a relative JSONPath

    It does not support item access, slices, wildcards or parent operators.
    :param json_path: String representation of a JSONPath
    """

    def __init__(self, json_path: str):
        self.raw_json_path = json_path

    def json_path_structure(self):
        json_path_structure = self.raw_json_path.split('.')
        return json_path_structure

    def is_absolute(self):
        """
        :return: Boolean indicating if the JSONPath is an absolute JSONPath.
        """
        return self.raw_json_path[0] == '$'

    def is_relative(self):
        """
        :return: Boolean indicating if the JSONPath is relative.
        """
        return self.raw_json_path[0] == '@'

    def split(self, at: int) -> (JSONPath, JSONPath):
        """
        Produces an absolute and a relative JSONPath by splitting the current one at the given index location.
        :param at: Index position where to split the XPath.
        :return: Tuple of XPath, the first one being the absolute path before the split at location
        and the second one the relative XPath after the split location.
        """
        return JSONPath('.'.join(self.json_path_structure()[:at])), JSONPath('.'.join(['@'] + self.json_path_structure()[at:]))

    def append(self, relative_path: JSONPath) -> None:
        """
        Appends a relative JSONPath to the end.
        :param relative_path: Relative JSONPath to append.
        :return: Result of appending the relative JSONPath to the end.
        """
        assert relative_path.is_relative()

        self.raw_json_path = self.raw_json_path + relative_path.raw_json_path[1:]
        return None

    def __str__(self):
        return self.raw_json_path

    def __repr__(self):
        return self.raw_json_path

    def __eq__(self, other: JSONPath):
        return self.raw_json_path == other.raw_json_path


class JSONNodeType(Enum):
    """
    JSON base types.
    """
    string = 1
    integer = 2
    number = 3
    object = 4
    array = 5
    boolean = 6
    null = 7


class JSONNode():
    """
    Class representing a JSON node, defined by its JSONPath and its type
    :param json_path: The JSONPath of the node.
    :param node_type: A JSONNodeType enumeration specifying the type of the node.
    """
    def __init__(self, json_path: str, node_type: JSONNodeType):
        self.path = json_path
        self.node_type = node_type


def get_item_from_json_path(path: JSONPath, json: Union[Dict, List]) -> Any:
    """
    :param path: JSONPath of the item that is to be accessed.
    :param json: JSON serializable input from which to obtain the item.
    :raises KeyError: If the item at the given JSONPath does not exist.
    :raises TypeError: If an item along the JSONPath is not suscriptable.
    :return: Item at the given path from the input json.
    """
    current_item = json
    for key_pos, key in enumerate(path.json_path_structure()):
        try:
            if key == '$' or key == '@':
                pass
            else:
                current_item = current_item[key]
        except KeyError:
            raise KeyError('The following path does not exist', path.split(at=key_pos + 1)[0])
        except TypeError:
            raise TypeError('The following item is not a dictionary: ', path.split(at=key_pos + 1)[0])
    return current_item


def write_item_in_path(item: Any, in_path: JSONPath, json: Dict) -> Dict:
    """
    Attemps to write the given item at the JSONPath location. If an item already exists in the given JSONPath it will
    overwrite it.
    :param item: Item to write
    :param in_path: JSONPath specifying where to write the item.
    :param json: JSON serializable dictionary in which to write the item.
    :raises TypeError: If an item along is not an object and thus cannot contain child attributes.
    :return: A copy of the input json with the item written in the given JSONPath.
    """
    json_copy = deepcopy(json)
    parent_path, item_relative_path = in_path.split(-1)
    item_key = item_relative_path.json_path_structure()[-1]

    # If the JSONPath exists and points to a list we append the item to the list
    try:
        item_array = get_item_from_json_path(in_path, json_copy)
        item_array.append(item)
        return json_copy
    except (KeyError, TypeError, AttributeError):
        pass

    try:
        parent_item = get_item_from_json_path(parent_path, json_copy)
        print()
    except (KeyError, TypeError) as e:
        # If the parent item doesnt exist we iteratively create a path of empty items until we get to the parent
        error_at_path = e.args[1]  # type: JSONPath
        json_copy = write_item_in_path({}, error_at_path, json_copy)
        return write_item_in_path(item, in_path, json_copy)
    try:
        parent_item.update({item_key: item})
    except AttributeError:
        raise TypeError('Cannot write item in path, item not suscriptable: ', parent_path)
    return json_copy
