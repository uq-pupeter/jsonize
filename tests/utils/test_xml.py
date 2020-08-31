import unittest
from jsonize.utils.xml import XPath, XMLNode, XMLNodeType, XMLSequenceNode, XMLNodeTree, \
    get_short_namespace, find_namespaces, generate_node_xpaths
from jsonize.utils.json import JSONPath
from pathlib import Path
from lxml.etree import parse as xml_parse


class TestNamespaceSubstitution(unittest.TestCase):
    namespaces = {'gml': 'http://www.opengis.net/gml/3.2',
                  'adrmsg': 'http://www.eurocontrol.int/cfmu/b2b/ADRMessage',
                  'aixm': 'http://www.aixm.aero/schema/5.1',
                  'xlink': 'http://www.w3.org/1999/xlink'}

    def test_namespace_found(self):
        full_ns = 'http://www.opengis.net/gml/3.2'
        short_ns = 'gml'
        self.assertEqual(short_ns, get_short_namespace(full_ns, self.namespaces))

    def test_namespace_not_found(self):
        with self.assertRaises(KeyError):
            get_short_namespace('http://notfound.com', self.namespaces)

    def test_namespace_substitution(self):
        xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember[1]/aixm:Route/@{http://www.opengis.net/gml/3.2}id')
        short_xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember[1]/aixm:Route/@gml:id')
        with self.subTest():
            self.assertEqual(short_xpath, xpath.shorten_namespaces(self.namespaces, in_place=False))
        with self.subTest():
            xpath.shorten_namespaces(self.namespaces, in_place=True)
            self.assertEqual(short_xpath, xpath)


class TestXPathManipulations(unittest.TestCase):

    def test_index_removal(self):
        xpath = XPath('/root/element[10]/subelement/subsubelement[1]/@attribute')
        reference = XPath('/root/element/subelement/subsubelement/@attribute')
        with self.subTest():
            self.assertEqual(xpath.remove_indices(in_place=False), reference)
        with self.subTest():
            xpath.remove_indices(in_place=True)
            self.assertEqual(xpath, reference)

    def test_make_relative_path(self):
        with self.subTest():
            xpath = XPath('/root/element[10]/subelement/subsubelement[1]/@attribute')
            parent = XPath('/root/element[10]')
            reference = XPath('./subelement/subsubelement[1]/@attribute')
            with self.subTest():
                self.assertEqual(xpath.relative_to(parent, in_place=False), reference)
            with self.subTest():
                xpath.relative_to(parent, in_place=True)
                self.assertEqual(xpath, reference)

        with self.subTest():
            xpath = XPath('/root/element[10]/subelement/subsubelement[1]')
            parent = xpath
            reference = XPath('.')
            with self.subTest():
                self.assertEqual(xpath.relative_to(parent, in_place=False), reference)
            with self.subTest():
                xpath.relative_to(parent, in_place=True)
                self.assertEqual(xpath, reference)


class TestInferJsonPath(unittest.TestCase):

    def test_absolute_path(self):
        xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
        reference = JSONPath('$.adrmsg:ADRMessage.adrmsg:hasMember.aixm:Route.@gml:id')
        self.assertEqual(reference, xpath.to_json_path(attributes='@', with_namespaces=True))

    def test_relative_path(self):
        xpath = XPath('./adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
        reference = JSONPath('@.adrmsg:ADRMessage.adrmsg:hasMember.aixm:Route.@gml:id')
        self.assertEqual(reference, xpath.to_json_path(attributes='@', with_namespaces=True))

    def test_ignore_namespaces(self):
        xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
        reference = JSONPath('$.ADRMessage.hasMember.Route.@id')
        self.assertEqual(reference, xpath.to_json_path(attributes='@', with_namespaces=False))

    def test_change_attribute_tag(self):
        with self.subTest():
            xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
            reference = JSONPath('$.ADRMessage.hasMember.Route._id')
            self.assertEqual(reference, xpath.to_json_path(attributes='_', with_namespaces=False))

        with self.subTest():
            xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
            reference = JSONPath('$.ADRMessage.hasMember.Route.id')
            self.assertEqual(reference, xpath.to_json_path(attributes='', with_namespaces=False))

        with self.subTest():
            xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
            reference = JSONPath('$.adrmsg:ADRMessage.adrmsg:hasMember.aixm:Route.attrib_gml:id')
            self.assertEqual(reference, xpath.to_json_path(attributes='attrib_', with_namespaces=True))


class TestXPathRelations(unittest.TestCase):

    def test_descendance(self):
        with self.subTest():
            ancestor = XPath('/root/element')
            descendant = XPath('/root/element/subelement/leaf/@attribute')
            self.assertTrue(descendant.is_descendant_of(ancestor))

        with self.subTest():
            ancestor = XPath('/root/element')
            not_descendant = XPath('/root/otherElement/subelement/leaf')
            self.assertFalse(not_descendant.is_descendant_of(ancestor))

        with self.subTest():
            ancestor = XPath('/root/element')
            not_descendant = XPath('/root/elemental')
            self.assertFalse(not_descendant.is_descendant_of(ancestor))

    def test_is_leaf(self):
        all_nodes = [XMLNode('/root/element/@attrib', XMLNodeType.ATTRIBUTE),
                     XMLNode('/root/element/subelement/subsubelement', XMLNodeType.ELEMENT),
                     XMLNode('/root/anotherElement', XMLNodeType.ELEMENT),
                     XMLNode('/root/element', XMLNodeType.ELEMENT)]
        with self.subTest():
            self.assertTrue(XMLNode('/root/element/@attrib', XMLNodeType.ATTRIBUTE).is_leaf(all_nodes))
        with self.subTest():
            self.assertTrue(XMLNode('/root/element/subelement/subsubelement', XMLNodeType.ELEMENT).is_leaf(all_nodes))
        with self.subTest():
            self.assertTrue(XMLNode('/root/anotherElement', XMLNodeType.ELEMENT).is_leaf(all_nodes))
        with self.subTest():
            self.assertFalse(XMLNode('/root/element', XMLNodeType.ELEMENT).is_leaf(all_nodes))

    def test_is_attribute(self):
        attribute_node = XPath('/root/element/@attribute')
        ns_attribute_node = XPath('/ns:root/nss:element/@nss:attribute')
        element_node = XPath('root/element')
        with self.subTest():
            self.assertTrue(attribute_node.is_attribute())
        with self.subTest():
            self.assertTrue(ns_attribute_node.is_attribute())
        with self.subTest():
            self.assertFalse(element_node.is_attribute())

    def test_is_absolute(self):
        absolute_xpath = XPath('/root/element/subelement')
        relative_xpath = XPath('./element/@attribute')
        with self.subTest():
            self.assertTrue(absolute_xpath.is_absolute())
        with self.subTest():
            self.assertFalse(relative_xpath.is_absolute())

    def test_is_relative(self):
        absolute_xpath = XPath('/root/element/subelement')
        relative_xpath = XPath('./element/@attribute')
        with self.subTest():
            self.assertFalse(absolute_xpath.is_relative())
        with self.subTest():
            self.assertTrue(relative_xpath.is_relative())

    def test_attribute_name(self):
        attribute_xpath = XPath('./element/@attri')
        absolute_attribute_xpath = XPath('/ns:root/nss:element/@nss:attribute')
        element_xpath = XPath('/root/element/subelement')
        with self.subTest():
            self.assertEqual(attribute_xpath.attribute_name(), 'attri')
        with self.subTest():
            self.assertEqual(absolute_attribute_xpath.attribute_name(), 'nss:attribute')
        with self.subTest():
            with self.assertRaises(ValueError):
                element_xpath.attribute_name()

    def test_parent(self):
        absolute_attribute_xpath = XPath('/ns:root/nss:element/@nss:attribute')
        relative_element_xpath = XPath('./element/subelement')
        with self.subTest():
            self.assertEqual(absolute_attribute_xpath.parent(), XPath('/ns:root/nss:element'))
        with self.subTest():
            self.assertEqual(relative_element_xpath.parent(), XPath('./element'))

    def test_split(self):
        absolute_attribute_xpath = XPath('/ns:root/nss:element/@nss:attribute')
        relative_element_xpath = XPath('./element/subelement')
        with self.subTest():
            # TODO: Evaluate if the numbering convention is appropriate
            self.assertEqual(absolute_attribute_xpath.split(1), (XPath(''), XPath('./ns:root/nss:element/@nss:attribute')))
            self.assertEqual(absolute_attribute_xpath.split(2), (XPath('/ns:root'), XPath('./nss:element/@nss:attribute')))
        with self.subTest():
            self.assertEqual(relative_element_xpath.split(1), (XPath('.'), XPath('./element/subelement')))
            self.assertEqual(relative_element_xpath.split(2), (XPath('./element'), XPath('./subelement')))
        with self.subTest():
            with self.assertRaises(ValueError):
                relative_element_xpath.split(-1)


class TestJsonizeMapGeneration(unittest.TestCase):
    xml_attribute_node = XMLNode('/ns:root/nss:element/@nss:attrib', XMLNodeType.ATTRIBUTE)
    xml_value_node = XMLNode('/ns:root/nss:element/nss:subelement/ns:subsubelement', XMLNodeType.VALUE)
    xml_sequence_node = XMLSequenceNode('/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                        [XMLNode('./child', XMLNodeType.VALUE),
                                         XMLNode('./@nss:attrib', XMLNodeType.ATTRIBUTE)])
    xml_empty_sequence_node = XMLSequenceNode('/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                              [])
    xml_tree = XMLNodeTree([xml_attribute_node,
                            xml_value_node,
                            xml_sequence_node])

    def test_xml_attribute_jsonize(self):
        with self.subTest():
            self.assertEqual(self.xml_attribute_node.to_jsonize(attributes='@', with_namespaces=True),
                             {'from': {'path': '/ns:root/nss:element/@nss:attrib',
                                       'type': 'attribute'},
                              'to': {'path': '$.ns:root.nss:element.@nss:attrib',
                                     'type': 'infer'}})
        with self.subTest():
            self.assertEqual(self.xml_attribute_node.to_jsonize(attributes='', with_namespaces=True),
                             {'from': {'path': '/ns:root/nss:element/@nss:attrib',
                                       'type': 'attribute'},
                              'to': {'path': '$.ns:root.nss:element.nss:attrib',
                                     'type': 'infer'}})
        with self.subTest():
            self.assertEqual(self.xml_attribute_node.to_jsonize(attributes='', with_namespaces=False),
                             {'from': {'path': '/ns:root/nss:element/@nss:attrib',
                                       'type': 'attribute'},
                              'to': {'path': '$.root.element.attrib',
                                     'type': 'infer'}})

    def test_xml_value_jsonize(self):
        with self.subTest():
            self.assertEqual(self.xml_value_node.to_jsonize(attributes='@', with_namespaces=True),
                             {'from': {'path': '/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                       'type': 'value'},
                              'to': {'path': '$.ns:root.nss:element.nss:subelement.ns:subsubelement.value',
                                     'type': 'infer'}})
        with self.subTest():
            self.assertEqual(self.xml_value_node.to_jsonize(values='', with_namespaces=True),
                             {'from': {'path': '/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                       'type': 'value'},
                              'to': {'path': '$.ns:root.nss:element.nss:subelement.ns:subsubelement',
                                     'type': 'infer'}})

    def test_xml_sequence_jsonize(self):
        with self.subTest():
            self.assertEqual(self.xml_sequence_node.to_jsonize(values='', with_namespaces=True),
                             {'from': {'path': '/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                       'type': 'sequence'},
                              'to': {'path': '$.ns:root.nss:element.nss:subelement.ns:subsubelement',
                                     'type': 'array'},
                              'itemMappings': [
                                  {'from': {'path': './child',
                                            'type': 'value'},
                                   'to': {'path': '@.child',
                                          'type': 'infer'}
                                   },
                                  {'from': {'path': './@nss:attrib',
                                            'type': 'attribute'},
                                   'to': {'path': '@.nss:attrib',
                                          'type': 'infer'}
                                   }
                              ]
                              }
                             )

        with self.subTest():
            self.assertEqual(self.xml_empty_sequence_node.to_jsonize(values='', with_namespaces=True),
                             {'from': {'path': '/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                       'type': 'sequence'},
                              'to': {'path': '$.ns:root.nss:element.nss:subelement.ns:subsubelement',
                                     'type': 'array'},
                              'itemMappings': [
                                  {'from': {'path': '.',
                                            'type': 'value'},
                                   'to': {'path': '@',
                                          'type': 'infer'}
                                   }
                              ]
                              })

        with self.subTest():
            self.assertEqual(self.xml_empty_sequence_node.to_jsonize(values='value', attributes='_', with_namespaces=False),
                             {'from': {'path': '/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                       'type': 'sequence'},
                              'to': {'path': '$.root.element.subelement.subsubelement',
                                     'type': 'array'},
                              'itemMappings': [
                                  {'from': {'path': '.',
                                            'type': 'value'},
                                   'to': {'path': '@.value',
                                          'type': 'infer'}
                                   }
                              ]
                              })

    def test_xml_tree_jsonize(self):
        with self.subTest():
            self.assertEqual(self.xml_tree.to_jsonize('value', attributes='@', with_namespaces=True),
                             [
                                 {'from': {'path': '/ns:root/nss:element/@nss:attrib',
                                           'type': 'attribute'},
                                  'to': {'path': '$.ns:root.nss:element.@nss:attrib',
                                         'type': 'infer'}
                                  },
                                 {'from': {'path': '/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                           'type': 'value'},
                                  'to': {'path': '$.ns:root.nss:element.nss:subelement.ns:subsubelement.value',
                                         'type': 'infer'}
                                  },
                                 {'from': {'path': '/ns:root/nss:element/nss:subelement/ns:subsubelement',
                                           'type': 'sequence'},
                                  'to': {'path': '$.ns:root.nss:element.nss:subelement.ns:subsubelement',
                                         'type': 'array'},
                                  'itemMappings': [
                                      {'from': {'path': './child',
                                                'type': 'value'},
                                       'to': {'path': '@.child.value',
                                              'type': 'infer'}
                                       },
                                      {'from': {'path': './@nss:attrib',
                                                'type': 'attribute'},
                                       'to': {'path': '@.@nss:attrib',
                                              'type': 'infer'}
                                       }
                                  ]
                                  }
                             ]
                             )


class TestXMLNodeManipulations(unittest.TestCase):
    xml_node = XMLNode('/root/element', XMLNodeType.ELEMENT)
    deep_xml_sequence = XMLSequenceNode('/root/element/subelement/sequence',
                                        sub_nodes=[XMLNode('./@attribute', XMLNodeType.ATTRIBUTE),
                                                   XMLNode('./value', XMLNodeType.VALUE)])
    deep_attribute = XMLNode('/root/element/subelement/@attrib', XMLNodeType.ATTRIBUTE)

    def test_sequence_relative_to(self):
        with self.subTest():
            self.assertEqual(self.deep_xml_sequence.relative_to(self.xml_node, in_place=False),
                             XMLSequenceNode('./subelement/sequence',
                                             sub_nodes=[XMLNode('./@attribute', XMLNodeType.ATTRIBUTE),
                                                        XMLNode('./value', XMLNodeType.VALUE)])
                             )
        with self.subTest():
            self.deep_xml_sequence.relative_to(self.xml_node, in_place=True)
            self.assertEqual(self.deep_xml_sequence,
                             XMLSequenceNode('./subelement/sequence',
                                             sub_nodes=[XMLNode('./@attribute', XMLNodeType.ATTRIBUTE),
                                                        XMLNode('./value', XMLNodeType.VALUE)])
                             )

    def test_node_relative_to(self):
        with self.subTest():
            self.assertEqual(self.deep_attribute.relative_to(self.xml_node, in_place=False),
                             XMLNode('./subelement/@attrib', XMLNodeType.ATTRIBUTE)
                             )

        with self.subTest():
            self.deep_attribute.relative_to(self.xml_node, in_place=True)
            self.assertEqual(self.deep_attribute,
                             XMLNode('./subelement/@attrib', XMLNodeType.ATTRIBUTE)
                             )


class TestFindNamespaces(unittest.TestCase):

    def test_exist_namespaces(self):
        xml_tree = xml_parse(str(Path('../samples/sample_namespaced.xml')))
        xml_namespaces = {'message': 'http://www.aixm.aero/schema/5.1.1/message', 'gts': 'http://www.isotc211.org/2005/gts',
                          'gco': 'http://www.isotc211.org/2005/gco', 'xsd': 'http://www.w3.org/2001/XMLSchema',
                          'gml': 'http://www.opengis.net/gml/3.2', 'gss': 'http://www.isotc211.org/2005/gss',
                          'aixm': 'http://www.aixm.aero/schema/5.1.1', 'gsr': 'http://www.isotc211.org/2005/gsr',
                          'gmd': 'http://www.isotc211.org/2005/gmd', 'xlink': 'http://www.w3.org/1999/xlink',
                          'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        self.assertEqual(find_namespaces(xml_tree), xml_namespaces)

    def test_no_namespaces(self):
        xml_tree = xml_parse(str(Path('../samples/sample_no_namespace.xml')))
        xml_namespaces = {}
        self.assertEqual(find_namespaces(xml_tree), xml_namespaces)


class TestXPathGeneration(unittest.TestCase):

    def test_node_xpaths(self):
        xml_tree = xml_parse(str(Path('../samples/sample_no_namespace.xml')))
        xpath_set = {XPath('/catalog/book[1]'),
                     XPath('/catalog/book[1]/@id'), XPath('/catalog/book[1]/author'), XPath('/catalog/book[1]/title'), XPath('/catalog/book[1]/genre'),
                     XPath('/catalog/book[1]/price'), XPath('/catalog/book[1]/publish_date'), XPath('/catalog/book[1]/description'),
                     XPath('/catalog/book[2]'),
                     XPath('/catalog/book[2]/@id'), XPath('/catalog/book[2]/author'), XPath('/catalog/book[2]/title'), XPath('/catalog/book[2]/genre'),
                     XPath('/catalog/book[2]/price'), XPath('/catalog/book[2]/publish_date'), XPath('/catalog/book[2]/description')}
        with self.subTest():
            self.assertCountEqual(xpath_set, generate_node_xpaths(xml_tree))
        with self.subTest():
            self.assertSetEqual(xpath_set, set(generate_node_xpaths(xml_tree)))



if __name__ == '__main__':
    unittest.main()
