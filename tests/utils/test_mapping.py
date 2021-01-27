from jsonize.utils.mapping import *
import unittest


class TestInferPathType(unittest.TestCase):
    absolute_xpath = '/element/subelement/@ns:attrib'
    relative_xpath = './element/subelement/@ns:attrib'
    absolute_jsonpath = '$.attribute.subattribute'
    relative_jsonpath = '@.attribute.subattribute'
    invalid_path = 'badpath.subnode/bad'

    def test_invalid_path(self):
        with self.assertRaises(ValueError):
            infer_path_type(self.invalid_path)

    def test_jsonpath(self):
        with self.subTest():
            self.assertEqual(infer_path_type(self.absolute_jsonpath), JSONPath(self.absolute_jsonpath))

        with self.subTest():
            self.assertEqual(infer_path_type(self.relative_jsonpath), JSONPath(self.relative_jsonpath))

    def test_xpath(self):
        with self.subTest():
            self.assertEqual(infer_path_type(self.absolute_xpath), XPath(self.absolute_xpath))

        with self.subTest():
            self.assertEqual(infer_path_type(self.relative_xpath), XPath(self.relative_xpath))


if __name__ == '__main__':
    unittest.main()
