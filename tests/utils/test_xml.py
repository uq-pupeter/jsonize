import unittest
from jsonize.utils.xml import XPath, XMLNode, XMLNodeType, get_short_namespace
from jsonize.utils.json import JSONPath


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
        self.assertEqual(reference, xpath.to_json_path(attributes='@', namespaces='preserve'))

    def test_relative_path(self):
        xpath = XPath('./adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
        reference = JSONPath('@.adrmsg:ADRMessage.adrmsg:hasMember.aixm:Route.@gml:id')
        self.assertEqual(reference, xpath.to_json_path(attributes='@', namespaces='preserve'))

    def test_ignore_namespaces(self):
        xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
        reference = JSONPath('$.ADRMessage.hasMember.Route.@id')
        self.assertEqual(reference, xpath.to_json_path(attributes='@', namespaces='ignore'))

    def test_change_attribute_tag(self):
        with self.subTest():
            xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
            reference = JSONPath('$.ADRMessage.hasMember.Route._id')
            self.assertEqual(reference, xpath.to_json_path(attributes='_', namespaces='ignore'))

        with self.subTest():
            xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
            reference = JSONPath('$.ADRMessage.hasMember.Route.id')
            self.assertEqual(reference, xpath.to_json_path(attributes='', namespaces='ignore'))

        with self.subTest():
            xpath = XPath('/adrmsg:ADRMessage/adrmsg:hasMember/aixm:Route/@gml:id')
            reference = JSONPath('$.adrmsg:ADRMessage.adrmsg:hasMember.aixm:Route.attrib_gml:id')
            self.assertEqual(reference, xpath.to_json_path(attributes='attrib_', namespaces='preserve'))


class TestXPathRelations(unittest.TestCase):

    def test_descendance(self):
        with self.subTest():
            ancestor = XPath('/root/element')
            descendant = XPath('/root/element/subelement/leaf/@attribute')
            self.assertTrue(descendant.is_descendant(ancestor))

        with self.subTest():
            ancestor = XPath('/root/element')
            not_descendant = XPath('/root/otherElement/subelement/leaf')
            self.assertFalse(not_descendant.is_descendant(ancestor))

    def test_is_leaf(self):
        all_nodes = [XMLNode('/root/element/@attrib', XMLNodeType['attribute']),
                     XMLNode('/root/element/subelement/subsubelement', XMLNodeType['element']),
                     XMLNode('/root/anotherElement', XMLNodeType['element']),
                     XMLNode('/root/element', XMLNodeType['element'])]
        with self.subTest():
            self.assertTrue(XMLNode('/root/element/@attrib', XMLNodeType['attribute']).is_leaf(all_nodes))
        with self.subTest():
            self.assertTrue(XMLNode('/root/element/subelement/subsubelement', XMLNodeType['element']).is_leaf(all_nodes))
        with self.subTest():
            self.assertTrue(XMLNode('/root/anotherElement', XMLNodeType['element']).is_leaf(all_nodes))
        with self.subTest():
            self.assertFalse(XMLNode('/root/element', XMLNodeType['element']).is_leaf(all_nodes))

if __name__ == '__main__':
    unittest.main()
