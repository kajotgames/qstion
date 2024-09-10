import unittest
import sys

sys.path.append(".")


class StringifyTest(unittest.TestCase):

    def test_stringify_default(self):
        import src.qstion as qs

        self.assertEqual(qs.stringify({"a": "b"}), "a=b")
        self.assertEqual(qs.stringify({"a": {"b": "c"}}), "a%5Bb%5D=c")

    def test_stringify_encode(self):
        import src.qstion as qs

        self.assertEqual(qs.stringify({"a": {"b": "c"}}), "a%5Bb%5D=c")
        self.assertEqual(qs.stringify({"a": {"b": "c"}}, encode=False), "a[b]=c")

    def test_stringify_encode_values_only(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"a": "b", "c": ["d", "e=f"], "f": [["g"], ["h"]]}, encode=False, encode_values_only=True),
            "a=b&c[0]=d&c[1]=e%3Df&f[0][0]=g&f[1][0]=h",
        )
        self.assertEqual(
            qs.stringify({"a": "b", "c": ["d", "e=f"], "f": [["g"], ["h"]]}),
            "a=b&c%5B0%5D=d&c%5B1%5D=e%3Df&f%5B0%5D%5B0%5D=g&f%5B1%5D%5B0%5D=h",
        )
        # just for verifying the default value
        self.assertEqual(
            qs.stringify({"a": "b", "c": ["d", "e=f"], "f": [["g"], ["h"]]}, encode=False, encode_values_only=False),
            "a=b&c[0]=d&c[1]=e=f&f[0][0]=g&f[1][0]=h",
        )
        # NOTE using custom encoder/decoder not yet supported

    def test_array_format(self):
        # array format can be one of: indices, brackets, repeat or comma
        import src.qstion as qs

        # indices
        self.assertEqual(
            qs.stringify({"a": ["b", "c"]}, array_format="indices", encode=False),
            "a[0]=b&a[1]=c",
        )
        # brackets
        self.assertEqual(
            qs.stringify({"a": ["b", "c"]}, array_format="brackets", encode=False),
            "a=[b,c]",
        )
        # repeat
        self.assertEqual(
            qs.stringify({"a": ["b", "c"]}, array_format="repeat", encode=False),
            "a=b&a=c",
        )
        # comma
        self.assertEqual(
            qs.stringify({"a": ["b", "c"]}, array_format="comma", encode=False),
            "a=b,c",
        )

    def test_notation(self):
        # notation can be one of: brackets or dot (defaults to brackets)
        import src.qstion as qs

        # brackets
        self.assertEqual(
            qs.stringify({"a": {"b": "c"}}, encode=False),
            "a[b]=c",
        )
        # dot
        self.assertEqual(
            qs.stringify({"a": {"b": "c"}}, allow_dots=True, encode=False),
            "a.b=c",
        )

    def test_encode_dot_in_keys(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"name.obj": {"first": "John", "last": "Doe"}}, allow_dots=True, encode_dot_in_keys=True),
            "name%252Eobj.first=John&name%252Eobj.last=Doe",
        )

    def test_empty_arrays(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"a": []}, encode=False, allow_empty_arrays=True),
            "a[]",
        )

    def test_empty_string_as_value(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"a": ""}, encode=False),
            "a=",
        )

    def test_key_with_no_values(self):
        # Key with no values (such as an empty object or array) will return nothing
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"a": []}, encode=False),
            "",
        )
        self.assertEqual(
            qs.stringify({"a": {}}, encode=False),
            "",
        )
        self.assertEqual(
            qs.stringify({"a": [{}]}, encode=False),
            "",
        )
        self.assertEqual(
            qs.stringify({"a": {"b": []}}, encode=False),
            "",
        )
        self.assertEqual(
            qs.stringify({"a": {"b": {}}}, encode=False),
            "",
        )

    def test_null_values(self):
        # Different from original qs implemetation, `None` values are represented as `null` instead of empty string
        # NOTE does not support strict null handling
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"a": None}, encode=False),
            "a=null",
        )

    def test_overriding_delimiter(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"a": "b", "c": "d"}, delimiter=";"),
            "a=b;c=d",
        )

    def test_old_charset(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"æ": "æ"}, charset="iso-8859-1"),
            "%E6=%E6",
        )
        # characters that are not in iso-8859-1 will be html- escaped
        self.assertEqual(
            qs.stringify({"a": "☺"}, charset="iso-8859-1"),
            "a=%26%239786%3B",
        )

    def test_charset_sentinel(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({"a": "☺"}, charset_sentinel=True),
            "utf8=%E2%9C%93&a=%E2%98%BA",
        )
        # iso sentinel
        self.assertEqual(
            qs.stringify({"a": "æ"}, charset_sentinel=True, charset="iso-8859-1"),
            "utf8=%26%2310003%3B&a=%E6",
        )

    def test_space_encoding(self):
        import src.qstion as qs

        # RFC3986 used as default option and encodes ' ' to %20 which is backward compatible.
        # In the same time, output can be stringified as per RFC1738 with ' ' equal to '+'.

        self.assertEqual(
            qs.stringify({"a": "b c"}),
            "a=b%20c",
        )


if __name__ == "__main__":
    unittest.main()
