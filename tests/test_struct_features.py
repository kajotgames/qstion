import unittest
import sys

sys.path.append(".")


class TestStructuralFeatures(unittest.TestCase):

    def test_array_simplifying(self):
        import src.qstion as qs

        # set up simple filter with correct simple array inside
        data = {"foo": ["bar", "baz"]}
        parsed_root = qs.parser.QsParser.load_filter_from_dict(data)

        # verify that the filter has the correct structure
        self.assertEqual(parsed_root.children[0].key, "foo")
        # value should be list of nested Node objects
        self.assertIsInstance(parsed_root.children[0].value, list)
        # Nodes should have key indexing their position in the list and value being the string
        self.assertEqual(parsed_root.children[0].value[0].key, 0)
        self.assertEqual(parsed_root.children[0].value[0].value, "bar")
        self.assertEqual(parsed_root.children[0].value[1].key, 1)
        self.assertEqual(parsed_root.children[0].value[1].value, "baz")

        # simplifying arrays in root should transform these nested nodes into simple array
        parsed_root.simplify_arrays()
        # verify that the filter has the correct structure
        self.assertEqual(parsed_root.children[0].key, "foo")
        # value should be list of strings
        self.assertIsInstance(parsed_root.children[0].value, list)
        # strings should be the same as before
        self.assertEqual(parsed_root.children[0].value[0], "bar")
        self.assertEqual(parsed_root.children[0].value[1], "baz")

        # test with more complex structure
        data = {"foo": ["bar", {"baz": "qux"}, "quux"]}
        # this kind of array cannot be simplified since it contains a dictionary
        parsed_root = qs.parser.QsParser.load_filter_from_dict(data)
        parsed_root.simplify_arrays()
        # verify that the filter has the correct structure
        self.assertEqual(parsed_root.children[0].key, "foo")
        # value should be list of nested Node objects
        self.assertIsInstance(parsed_root.children[0].value, list)
        # Nodes should have key indexing their position in the list and value being the string
        self.assertEqual(parsed_root.children[0].value[0].key, 0)
        self.assertEqual(parsed_root.children[0].value[0].value, "bar")
        self.assertEqual(parsed_root.children[0].value[1].key, 1)
        self.assertIsInstance(parsed_root.children[0].value[1].value, list)
        self.assertEqual(parsed_root.children[0].value[1].value[0].key, "baz")
        self.assertEqual(parsed_root.children[0].value[1].value[0].value, "qux")
        self.assertEqual(parsed_root.children[0].value[2].key, 2)
        self.assertEqual(parsed_root.children[0].value[2].value, "quux")

        # test with providing different order of keys
        query_string = "foo[1]=bar&foo[2]=baz&foo[0]=qux"
        parsed_root = qs.parser.parse(query_string, parse_arrays=True, return_as_obj=True)
        parsed_root.simplify_arrays()
        # verify that the filter has the correct structure
        self.assertEqual(parsed_root.children[0].key, "foo")
        # value should be list of strings
        self.assertIsInstance(parsed_root.children[0].value, list)
        # strings should be the same as before but in correct order
        self.assertEqual(parsed_root.children[0].value[0], "qux")
        self.assertEqual(parsed_root.children[0].value[1], "bar")
        self.assertEqual(parsed_root.children[0].value[2], "baz")

    def test_representation_after_simplifying(self):
        import src.qstion as qs

        # set up simple filter with correct simple array inside
        data = {"foo": ["bar", "baz"]}
        parsed_root = qs.parser.QsParser.load_filter_from_dict(data)

        # verify that the filter has the correct structure
        self.assertEqual(parsed_root.children[0].key, "foo")
        # value should be list of nested Node objects
        self.assertIsInstance(parsed_root.children[0].value, list)
        # Nodes should have key indexing their position in the list and value being the string
        self.assertEqual(parsed_root.children[0].value[0].key, 0)
        self.assertEqual(parsed_root.children[0].value[0].value, "bar")
        self.assertEqual(parsed_root.children[0].value[1].key, 1)
        self.assertEqual(parsed_root.children[0].value[1].value, "baz")

        # try to represent
        self.assertIsInstance(parsed_root._repr(), str)

        # simplifying arrays in root should transform these nested nodes into simple array
        parsed_root.simplify_arrays()
        # should be able to represent even after simplifying
        self.assertIsInstance(parsed_root._repr(), str)

    def test_type_parsing(self):
        """
        This test is to verify whether integer like-strings are reconstructed as quoted
        since with usage of `parse_primitive` we would not be able to tell if user wanted to
        provide a string or an integer.
        """
        import src.qstion as qs
        import src.qstion._struct_core as core

        # set up simple filter with correct simple array inside
        controll_string = 'foo="1"'  # force string type
        parsed_root = qs.parse(controll_string, return_as_obj=True)
        # verify that the filter has the correct structure

        match parsed_root:
            case core.QsRoot(
                parameter_limit=_,
                children=[
                    core.QsNode(
                        auto_set_key=_,
                        key="foo",
                        value="1",
                    )
                ],
            ):
                pass
            case _:
                self.fail("Parsing failed")

        # now stringify the parsed root
        stringified = qs.stringify(parsed_root, encode=False)
        self.assertEqual(stringified, controll_string)

        # try to dump the parsed root to dict - should have quotes around the value
        dumped = parsed_root.to_dict()
        self.assertEqual(dumped, {"foo": '"1"'})

    def test_qsroot_pop(self):
        """
        This test targets method `pop` from object `QsRoot` - should work equivalently as dict.pop()
        """
        import src.qstion as qs
        from src.qstion._struct_core import QsRoot, QsNode

        # set up controll filter
        controll = qs.parse(
            qs.stringify({"a": "x", "b": {"c": "d"}, "e": ["f", "g", "h"]}), parse_arrays=True, return_as_obj=True
        )
        b_element = controll.pop("b")
        match controll:
            case QsRoot(
                parameter_limit=_,
                children=[
                    QsNode(
                        auto_set_key=_,
                        key="a",
                        value="x",
                    ),
                    QsNode(auto_set_key=_, key="e", value=[*_]),
                ],
            ):
                pass
            case _:
                self.fail("Parsing failed")

        match b_element:
            case QsNode(
                auto_set_key=_,
                key="b",
                value=[
                    QsNode(
                        auto_set_key=_,
                        key="c",
                        value="d",
                    )
                ],
            ):
                pass
            case _:
                self.fail("Parsing failed")


if __name__ == "__main__":
    unittest.main()
