from jsonize.utils.json import get_item_from_json_path, write_item_in_path, JSONPath
from copy import deepcopy
import unittest

test_json_path = JSONPath('$.key1.key2.key3')

test_json_path_2 = JSONPath('$.key2.key1.key3')
test_json_path_3 = JSONPath('$')

sample_dict_1 = {'key1': {'key2': {'key3': 42,
                                   'other_key': -35,
                                   'key4': {'key5': True,
                                            'key6': False}}}}

sample_dict_2 = {'key1': 42}

sample_dict_3 = {'key2': {'key1': {'key3': True}}}


class TestGetItemJSONPath(unittest.TestCase):

    def test_item_exists(self):
        with self.subTest():
            self.assertEqual(get_item_from_json_path(test_json_path, sample_dict_1),
                             42)
        with self.subTest():
            self.assertEqual(get_item_from_json_path(JSONPath('$.key1.key2.key4'), sample_dict_1),
                             {'key5': True, 'key6': False})

    def test_get_root(self):
        with self.subTest():
            self.assertEqual(get_item_from_json_path(JSONPath('$'), sample_dict_1), sample_dict_1)
        with self.subTest():
            self.assertEqual(get_item_from_json_path(JSONPath('$'), sample_dict_2), sample_dict_2)
        with self.subTest():
            self.assertEqual(get_item_from_json_path(JSONPath('$'), sample_dict_3), sample_dict_3)
        with self.subTest():
            self.assertEqual(get_item_from_json_path(JSONPath('@'), sample_dict_2), sample_dict_2)

    def test_item_doesnt_exist(self):
        with self.assertRaises(KeyError):
            get_item_from_json_path(JSONPath('$.key1.key2.another_key'), sample_dict_1)
        with self.assertRaises(KeyError):
            get_item_from_json_path(test_json_path_2, sample_dict_1)

    def test_item_not_suscriptable(self):
        with self.assertRaises(TypeError):
            get_item_from_json_path(test_json_path, sample_dict_2)

    def test_get_item_in_array(self):
        input_array = [0,1,2,3,4,5,6]
        self.assertEqual(get_item_from_json_path(JSONPath('$[3]'), input_array))


class TestWriteItemJSONPath(unittest.TestCase):

    def test_overwrite_item(self):
        with self.subTest():
            result = write_item_in_path({'key2': {'key3': 42,
                                                  'other_key': -35,
                                                  'key4': {'key5': True,
                                                           'key6': False}}},
                                        JSONPath('$.key1'), sample_dict_1)
            self.assertEqual(result, {'key1': {'key2': {'key3': 42,
                                                        'other_key': -35,
                                                        'key4': {'key5': True,
                                                                 'key6': False}}}})
        with self.subTest():
            result_2 = write_item_in_path(9, JSONPath('$.key1'), sample_dict_2)
            self.assertEqual(result_2, {'key1': 9})

    def test_write_new_item(self):
        with self.subTest():
            result = write_item_in_path('New value', JSONPath('$.new_key'), sample_dict_1)
            reference = sample_dict_1
            reference['new_key'] = 'New value'
            self.assertEqual(reference, result)

        with self.subTest():
            result_2 = write_item_in_path({'new_subkey': True}, JSONPath('$.key2.new_key'), sample_dict_3)
            reference_2 = sample_dict_3
            reference_2['key2']['new_key'] = {'new_subkey': True}
            self.assertEqual(result_2, reference_2)

    def test_write_new_item_in_new_path(self):
        result = write_item_in_path('New value', JSONPath('$.key2.key3'), sample_dict_2)
        reference = {'key1': 42,
                     'key2': {'key3': 'New value'}}
        self.assertEqual(reference, result)

    def test_write_deeply_nested_item_in_new_path(self):
        result = write_item_in_path('New Value', JSONPath('$.key1.key2.key3.key4.key5.key6'), sample_dict_3)
        reference = {'key2':
                         {'key1':
                              {'key3': True}
                          },
                     'key1':
                         {'key2':
                              {'key3':
                                   {'key4':
                                        {'key5':
                                             {'key6': 'New Value'}
                                         }
                                    }
                               }
                          }
                     }
        self.assertEqual(reference, result)

    def test_fail_write_item_conflicting_path(self):
        with self.assertRaises(TypeError):
            write_item_in_path('Failed write', JSONPath('$.key1.key2.key4.key5.bad_key'), sample_dict_1)

    def test_write_item_in_array(self):
        with self.subTest('write dictionary in array'):
            initial = {'key1': True,
                       'key2': {'key3': [{'key4': 42}]}}
            reference = {'key1': True,
                         'key2': {'key3': [{'key4': 42}, {'key5': 43}]}
                         }
            result = write_item_in_path({'key5': 43}, JSONPath('$.key2.key3'), deepcopy(initial))
            self.assertEqual(reference, result)
        with self.subTest('write item in array at root'):
            initial = []
            reference = [3]
            result = write_item_in_path(3, JSONPath('$'), initial)
            self.assertEqual(reference, result)
        with self.subTest('write item in array at relative root'):
            initial = []
            reference = [5]
            result = write_item_in_path(5, JSONPath('@'), initial)
            self.assertEqual(reference, result)
        with self.subTest('write item in array in nested location'):
            initial = {'key1': 1,
                       'key2': {'key3': [1, 1, 2, 3, 5],
                                'key4': 5}
                       }
            reference = {'key1': 1,
                         'key2': {'key3': [1, 1, 2, 3, 5, 8],
                                  'key4': 5}
                         }
            result = write_item_in_path(8, JSONPath('$.key2.key3'), initial)
            self.assertEqual(reference, result)


class TestJSONPath(unittest.TestCase):

    def test_split_absolute(self):
        absolute_path = JSONPath('$.key1.key2.key3.key4')
        split = absolute_path.split(2)
        reference = JSONPath('$.key1'), JSONPath('@.key2.key3.key4')
        self.assertTupleEqual(split, reference)

    def test_split_relative(self):
        relative_path = JSONPath('@.key1.key2.key3.key4')
        split = relative_path.split(-2)
        reference = JSONPath('@.key1.key2'), JSONPath('@.key3.key4')
        self.assertTupleEqual(split, reference)

    def test_split_root(self):
        absolute_path = JSONPath('$')
        split = absolute_path.split(-1)
        reference = JSONPath('$'), JSONPath('@')
        self.assertTupleEqual(split, reference)

    def test_fail_out_of_bound(self):
        absolute_path = JSONPath('$.key1.key2.key3.key4')
        with self.assertRaises(IndexError):
            split = absolute_path.split(6)

    def test_split_at_final_node(self):
        absolute_path = JSONPath('$.key1.key2.key3.key4')
        split = absolute_path.split(5)
        reference = absolute_path, JSONPath('@')
        self.assertTupleEqual(split, reference)

    def test_is_relative(self):
        with self.subTest():
            self.assertTrue(JSONPath('@.key1').is_relative())
        with self.subTest():
            self.assertFalse(JSONPath('$.key1.key2').is_relative())

    def test_is_absolute(self):
        with self.subTest():
            self.assertTrue(JSONPath('$.key1').is_absolute())
        with self.subTest():
            self.assertFalse(JSONPath('@.key1.key2').is_absolute())

    def test_append(self):
        reference = JSONPath('$.key1.key2.key3.key4')
        path = JSONPath('$.key1.key2')
        path.append(JSONPath('@.key3.key4'))
        self.assertEqual(reference, path)

    def test_fail_append(self):
        with self.assertRaises(ValueError):
            reference = JSONPath('$.key1.key2.key3.key4')
            self.assertEqual(reference, JSONPath('$.key1.key2').append(JSONPath('$.key3.key4')))


if __name__ == '__main__':
    unittest.main()
