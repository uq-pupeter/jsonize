# Jsonize

## Introduction
Jsonize provides tools to work with and transform XML and JSON documents and map them to highly-tunable JSON representations. Jsonize differentiates itself 
from most converters through its ability to define finely tunable mappings that enable the user to control exactly how the output representation
looks like. Jsonize solves many of the common
problems that plague similar conversion tools:

- Forced conventions on how XML attributes and elements are mapped: Jsonize allows to define how XML attributes are treated.
- Inability to cast the input values of an XML node into appropriate JSON types. Jsonize allows casting the input value into the chosen JSON basetype or inferring the best option.
- Inability to apply any transformations or data manipulation: Jsonize allows to define custom transformations applied to each input value.
- Inability to select which nodes of the XML are to be mapped: Jsonize allows to pick and choose the specific input nodes that will be mapped, which can greatly speed working with huge input documents.
- Inability to create JSON arrays as there is no corresponding data structure in XML: Jsonize allows creating JSON arrays from XML sequences.

Jsonize works around these problems by providing fine-grained control of the conversion, working with individual XML or JSON nodes mapped into JSON nodes. This allows the user to
work like a surgeon selecting which nodes in an XML or JSON file are mapped to JSON and how.

## Installation

The library can be installed using pip:

```shell script
pip install git+https://github.com/eurocontrol-swim/jsonize
```

Particular versions or branches can be selected using the usual pip notation for git repositories. For example, to use the `dev` branch:

```shell script
pip install git+https://github.com/eurocontrol-swim/jsonize@dev
```

Or to select a particular version by tag:

```shell script
pip install git+https://github.com/eurocontrol-swim/jsonize@v0.0.2-alpha
```


## Usage

The conversion is centered around the notion of a Jsonize mapping which defines exactly which input nodes are to be mapped and how. 
There are two ways to define the Jsonize mapping:

- Using a statically defined JSON file
- Importing the library into your project and creating the mapping as code

Both allow the same flexibility and the choice between using one or the other is a matter of preference or convenience.

### Static mapping using a JSON file

A Jsonize static mapping is defined using a JSON file that follows the [Jsonize Schema](https://github.com/eurocontrol-swim/jsonize/blob/master/jsonize/schema/jsonize-map.schema.json) 
and consists of an array of node mappings, represented in the JSON Schema with the `NodeMap` object.

A simple `NodeMap` object that maps an XML attribute into a JSON value takes the following form:

```json
{
    "from": {
      "path": "./element/@attribute",
      "type": "attribute"
    },
    "to": {
      "path": "$.element.attribute",
      "type": "string"
    }
}
```

A simple `NodeMap` object that maps a JSON node into a different JSON node takes the following form:

```json
{
    "from": {
      "path": "$.path.to.value",
      "type": "number"
    },
    "to": {
      "path": "$.another.path.to.value",
      "type": "string"
    }
}
```

Notice how the this `NodeMap` is casting an input with type `number` input an output with type `string`. 

The `from` attribute specifies the node we are interested to map, it contains two sub-attributes:
- `from.path`: specifies the path (XPath or JSONPath) if the input we want to map
- `from.type`: specifies the node type of the node we want to map. For XML input it can take one of the following values `attribute`, `sequence`, `value`. For a JSON input it can take one of the following values `string`, `number`, `array`, `boolean`.

The `to` attribute specifies where we want to map it, it contains two sub-attributes:
- `to.path`: specifies a JSONPath where we want it mapped
- `to.type`: identifies the JSON type into which the input value will be casted (one of `string`, `number`, `array`, `boolean`, `infer`). The `infer` value will
attempt to guess the right basetype to cast it to.

By defining multiple `NodeMap` we select exactly which elements or attributes of the XML we are interested in and where they 
are mapped into JSON.

There are two optional attributes in a `NodeMap` that have some special purpose:
 
 - `itemMappings`: Specifies an array of mappings that is to be applied to the `from` node, allowing us to build recursive mappings. 
 This has its use when the `type` of the input XML node is a `sequence`. Using `itemMappings` we can specify a 
 number of `NodeMap` that will be applied to each element of an XML sequence to form each item in a JSON array.

 - `transformation`: Allows specifying by name a `Transformation` containing a Python function that we want to apply to the input node value before mapping it to JSON. 
 Any Python code can be invoked as long as it's wrapped in a function that takes a single parameter. It can be used for string manipulation, type casting, getting values from external sources (e.g., DB, API query...). Your imagination is the limit.
 
 Once our JSON file containing the Jsonize mapping is defined we can simply invoke the function `xml_document_to_json_document` or `json_document_to_json_document` passing the appropriate
 parameters and it will do the work for us. An example can be found in the [example folder](https://github.com/eurocontrol-swim/jsonize/blob/master/jsonize/example/). 
 This example is chosen to highlight various useful features of Jsonize: 
 
 - How to map XML attributes
 - How to build JSON arrays from XML sequences
 - How to use the `itemMappings` attribute to build each item in a JSON array
 - How to invoke a `Transformation` to clean up some text
 
 #### Automatic generation of Jsonize mapping (XML)
 
 Manually generating a Jsonize mapping can be tiresome, especially for large XMLs. To avoid this pain the `infer_jsonize_map` helper function  will generate a Jsonize
 mapping for you. You can control a few conventions of the mapping via its parameters (check the documentation of the function for a detailed explanation):
 
 - value_tag
 - attribute_tag
 - keep_namespaces
 
 This function will include all the nodes (elements and attributes) in the input XML document to a Jsonize mapping. You can then manually alter or fine-tune the
 result to fit your needs.
 
 Disclaimer: This is a CPU intensive function, it requires traversing all the XML in order to figure out its structure and map it to a dictionary-like structure that
 can be serialized into JSON. Processing large XML files is SLOW! If your XML contains large sequences of repeated elements you can greatly speed up the process by
 truncating the sequence to just a few (at least 2). For instance, the example found in the
  [example folder](https://github.com/eurocontrol-swim/jsonize/blob/master/jsonize/example/) can be truncated to contain only 2 `book` elements. 
 The `infer_jsonize_map` will learn everything it needs to know with 2 examples and then it can generalize the mapping to arbitrarily large files.


 ### Programmatic mapping
 
 The same Jsonize mapping can be built writing Python code, in fact, the JSON file containing the Jsonize mapping is parsed and internally converted into Python classes.
 A Jsonize mapping is simply an `Iterable[XMLNodeToJSONNode]`. The following example builds the equivalent `XMLNodeToJSONNode` object
  of the `NodeMap` in the example shown above:
 
 ```python
from jsonize import XMLNodeToJSONNode, XMLNodeType, XMLNode, JSONNodeType, JSONNode

node_map = XMLNodeToJSONNode(from_xml_node=XMLNode(xpath='./element/@attribute', node_type=XMLNodeType['attribute']), 
                              to_json_node=JSONNode(json_path='$.element.attribute', node_type=JSONNodeType['string']))
```

## TODO

The following features are missing and could be added in future releases:

- *Object recursivity*: In the same way the `itemMappings` is used to define a recursive map of the items in an array, a similar functionality could be added
to recursive mappings for XML complexTypes.
- *Infer namespaces from XML files*: A basic functionality is included to find the namespaces of an XML, that looks into the XML root element. Unfortunately
XML files can contain XML namespace definitions anywhere in the document. The function could be enlarged to find them anywhere in the document, since this process
is computationally intensive a truncation strategy could be considered (e.g. look into the 100 first XML nodes and then stop.)
- *Blacklisting*: `infer_jsonize_map` could take blacklisting instructions (e.g. by pattern matching name via regex) and ignore XML nodes that
match the pattern. This would give a powerful way to automatically generate Jsonize mappings that do not contain stuff we are not interested in.