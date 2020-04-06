# Jsonize

## Introduction
Jsonize provides tools to convert an XML document into a JSON representation. Unlike most converters it allows to define a 
finely tuned mapping that enables the user to control exactly how the output representation looks like, avoiding the usual problems of XML to JSON 
conversion tools:

- Forced conventions on how XML attributes and elements are mapped
- Inability to cast the input values of an XML node into appropriate JSON types
- Inability to apply any transformations or data manipulation
- Inability to select which nodes of the XML are to be mapped
- Inability to create JSON arrays as there is no corresponding data structure in XML

Jsonize works around these problems by providing fine-grained control of the conversion, working with individual XML nodes mapped into JSON nodes. This allows the user to
work like a surgeon selecting which elements or attributes of an XML file are mapped to JSON and how.

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
pip install git+https://github.com/eurocontrol-swim/jsonize@v0.0.1-alpha
```


## Usage

The conversion is centered around the notion of a Jsonize mapping which defines exactly which XML nodes are to be mapped and how. 
There are two ways to define the Jsonize mapping:

- Using a statically defined JSON file
- Importing the library into your project and creating the mapping as code

Both allow the same flexibility and the choice between using one or the other is a matter of preference or convenience.

### Static mapping using a JSON file

A Jsonize static mapping is defined using a JSON file that follows the [Jsonize Schema](https://github.com/eurocontrol-swim/jsonize/blob/master/jsonize/schema/jsonize-map.schema.json) 
and consists of an array of XML node to JSON node mappings, represented in the JSON Schema with the `NodeMap` object.

A simple `NodeMap` object takes the following form:

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

The `from` attribute specifies the XML Node we are interested to map with the attribute `from.path` using an XPath and the `to` attribute specifies where we want to map it
into using JSONPath via `to.path`. The `from.type` attribute is used to identify the type of XML node (i.e. `element`, `attribute`, `sequence`, `complexType`), 
although this information can be inferred in some cases from the XPath expression this is not always the case and thus has to be provided. The `to.type` specifies the JSON
type into which the input value will be casted. By defining multiple `NodeMap` we select exactly which elements or attributes of the XML we are interested in and where they 
are mapped into JSON.

There are two optional attributes in a `NodeMap` that have some special purpose:
 
 - `itemMappings`: Specifies an array of mappings that is to be applied to the `from` node, allowing us to build recursive mappings. 
 This has its use when the `type` of the XML node is either a `sequence` or `complexType`. Using `itemMappings` we can specify a number of `NodeMap` 
 that will be applied to each element of an XML sequence to form each item in a JSON array or to an XML ComplexType to form the JSON object.

 - `transformation`: Allows to specify by name a `Transformation` containing a Python function that we want to apply to the input node value before mapping it to JSON. 
 Any Python code can be invoked as long as it's wrapped in a function that takes a single parameter. It can be used for string manipulation, type casting...
 
 Once our JSON file containing the Jsonize mapping is defined we can simply invoke the function `xml_document_to_json` passing the appropriate
 parameters and it will do the work for us. An example can be found in the [example folder](https://github.com/eurocontrol-swim/jsonize/blob/master/jsonize/example/). 
 This example is chosen to highlight various useful features of Jsonize: 
 
 - How to map XML attributes
 - How to build JSON arrays from XML sequences
 - How to use the `itemMappings` attribute to build each item in a JSON array
 - How to invoke a `Transformation` to clean up some text
 
 
 ### Programmatic mapping
 
 The same Jsonize mapping can be built writing Python code, in fact, the JSON file containing the Jsonize mapping is parsed and internally converted into Python classes.
 A Jsonize mapping is simply an `Iterable[XMLNodeToJSONNode]`. The following example builds the equivalent `XMLNodeToJSONNode` object
  of the `NodeMap` in the example shown above:
 
 ```python
from jsonize import XMLNodeToJSONNode, XMLNodeType, XMLNode, JSONNodeType, JSONNode

node_map = XMLNodeToJSONNode(from_xml_node=XMLNode(xpath='./element/@attribute', node_type=XMLNodeType['attribute']), 
                              to_json_node=JSONNode(json_path='$.element.attribute', node_type=JSONNodeType['string']))
```

