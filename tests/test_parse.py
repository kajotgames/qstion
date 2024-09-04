import unittest
import sys
import decimal

sys.path.append(".")


class ParserTest(unittest.TestCase):

    def test_basic_parse_objects(self):
        import src.qstion as qs

        # tests based on README of qs in npm: https://www.npmjs.com/package/qs?activeTab=readme
        # trivial query string
        self.assertDictEqual(qs.parse("foo=bar"), {"foo": "bar"})

        # single nested object
        self.assertDictEqual(qs.parse("a[b]=c"), {"a": {"b": "c"}})
        self.assertDictEqual(qs.parse("foo[bar]=baz"), {"foo": {"bar": "baz"}})

    def test_uri_encoding(self):
        import src.qstion as qs

        # test uri encoding
        self.assertDictEqual(qs.parse("a%5Bb%5D=c"), {"a": {"b": "c"}})
        self.assertDictEqual(qs.parse("a%5Bb%5D%5Bc%5D=d"), {"a": {"b": {"c": "d"}}})

    def test_object_depth(self):
        import src.qstion as qs

        # test object depth (default depth is 5)
        self.assertDictEqual(qs.parse("foo[bar][baz]=foobarbaz"), {"foo": {"bar": {"baz": "foobarbaz"}}})
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j"), {"a": {"b": {"c": {"d": {"e": {"f": {"[g][h][i]": "j"}}}}}}}
        )

        # override default depth
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=1), {"a": {"b": {"[c][d][e][f][g][h][i]": "j"}}}
        )
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=2), {"a": {"b": {"c": {"[d][e][f][g][h][i]": "j"}}}}
        )
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=3), {"a": {"b": {"c": {"d": {"[e][f][g][h][i]": "j"}}}}}
        )
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=4),
            {"a": {"b": {"c": {"d": {"e": {"[f][g][h][i]": "j"}}}}}},
        )
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=5),
            {"a": {"b": {"c": {"d": {"e": {"f": {"[g][h][i]": "j"}}}}}}},
        )
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=6),
            {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"[h][i]": "j"}}}}}}}},
        )

        # test strict depth
        self.assertDictEqual(
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=1, strict_depth=False),
            {"a": {"b": {"[c][d][e][f][g][h][i]": "j"}}},
        )
        # Going over depth should raise an error
        with self.assertRaises(qs.parser.Unparsable):
            qs.parse("a[b][c][d][e][f][g][h][i]=j", max_depth=1, strict_depth=True)

    def test_parameter_limit(self):
        import src.qstion as qs

        # default limit is 1000
        self.assertDictEqual(
            qs.parse("a=1&b=2&c=3&d=4&e=5&f=6&g=7&h=8&i=9&j=10"),
            {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5", "f": "6", "g": "7", "h": "8", "i": "9", "j": "10"},
        )
        # override to 2
        self.assertDictEqual(
            qs.parse("a=1&b=2&c=3&d=4&e=5&f=6&g=7&h=8&i=9&j=10", parameter_limit=2), {"a": "1", "b": "2"}
        )

    def test_custom_delimiter(self):
        import src.qstion as qs

        # delimiter can be either string or regex pattern
        self.assertDictEqual(qs.parse("a=b;c=d", delimiter=";"), {"a": "b", "c": "d"})
        self.assertDictEqual(qs.parse("a=b|c=d", delimiter=r"\|"), {"a": "b", "c": "d"})
        self.assertDictEqual(qs.parse("a=b_c=d", delimiter="_"), {"a": "b", "c": "d"})
        self.assertDictEqual(qs.parse("a=b|c=d", delimiter=r"[\|;]"), {"a": "b", "c": "d"})
        self.assertDictEqual(qs.parse("a=b;c=d", delimiter=r"[\|;]"), {"a": "b", "c": "d"})

    def test_dot_notation(self):
        import src.qstion as qs

        # allow dots
        self.assertDictEqual(qs.parse("a.b=c", allow_dots=True), {"a": {"b": "c"}})
        self.assertDictEqual(qs.parse("a.b.c=d", allow_dots=True), {"a": {"b": {"c": "d"}}})

        self.assertDictEqual(qs.parse("a.b=c", allow_dots=False), {"a.b": "c"})
        # combined syntax is forbidden
        with self.assertRaises(qs.parser.Unparsable):
            qs.parse("a[b].c=d", allow_dots=True)

        # dot notation with encoded dot in keys
        self.assertDictEqual(
            qs.parse("name%252Eobj.first=John&name%252Eobj.last=Doe", allow_dots=True, decode_dots_in_keys=True),
            {"name.obj": {"first": "John", "last": "Doe"}},
        )

        # decode dots in keys must be used with allow dots
        with self.assertRaises(qs.parser.ConfigurationError):
            qs.parse("name%252Eobj.first=John&name%252Eobj.last=Doe", decode_dots_in_keys=True)

    def test_arrays(self):
        import src.qstion as qs

        # basic array
        self.assertDictEqual(qs.parse("a[]=b", parse_arrays=True), {"a": ["b"]})
        self.assertDictEqual(qs.parse("a[]=b&a[]=c", parse_arrays=True), {"a": ["b", "c"]})

        # set indexes - must be if not set from 0, sparse arrays option must be enabled
        with self.assertRaises(qs.parser.Unparsable):
            qs.parse("a[1]=b", parse_arrays=True)
        # if using sparse arrays - result is Dictionary for clear indexing
        self.assertDictEqual(qs.parse("a[1]=b", parse_arrays=True, allow_sparse_arrays=True), {"a": {1: "b"}})
        self.assertDictEqual(qs.parse("a[1]=b&a[0]=c", parse_arrays=True), {"a": ["c", "b"]})

        # test nested arrays
        self.assertDictEqual(qs.parse("a[]=b&a[][c]=d", parse_arrays=True), {"a": ["b", {"c": "d"}]})
        # test mulidimensional arrays
        self.assertDictEqual(qs.parse("a[]=b&a[1][]=c&a[1][]=d", parse_arrays=True), {"a": ["b", ["c", "d"]]})

    def test_empty_arrays(self):
        import src.qstion as qs

        # empty arrays must be explicitly enabled
        with self.assertRaises(ValueError):
            qs.parse("a[]", parse_arrays=True)

        # empty arrays
        self.assertDictEqual(qs.parse("a[]", parse_arrays=True, allow_empty_arrays=True), {"a": []})

    def test_old_charset(self):
        import src.qstion as qs

        # old charset
        self.assertDictEqual(qs.parse("a=%A7", charset="iso-8859-1"), {"a": "§"})

    def test_charset_sentinel(self):
        import src.qstion as qs

        # charset sentinel - should be decoded as utf-8
        self.assertDictEqual(
            qs.parse("utf8=%E2%9C%93&a=%C3%B8", charset="iso-8859-1", charset_sentinel=True), {"a": "ø"}
        )

    def test_interpret_numeric_entities(self):
        import src.qstion as qs

        # interpret numeric entities
        self.assertDictEqual(qs.parse("a=%26%239786%3B"), {"a": "&#9786;"})
        self.assertDictEqual(qs.parse("a=%26%239786%3B", interpret_numeric_entities=True), {"a": "☺"})

    def test_sparse_arrays(self):
        import src.qstion as qs

        # sparse arrays - behavior differs from npm qs - sparse arrays must be explicitly enabled otherwise
        # error is raised if sparse arrays are detected,
        # also, sparse arrays are returned as dictionary with indexes as keys instead of list
        with self.assertRaises(qs.parser.Unparsable):
            qs.parse("a[1]=b", parse_arrays=True)

        self.assertDictEqual(qs.parse("a[1]=b", parse_arrays=True, allow_sparse_arrays=True), {"a": {1: "b"}})

        # if all indexes are provided, they dont have to be in correct order as long as they are consecutive
        self.assertDictEqual(
            qs.parse("a[5]=b&a[3]=c&a[1]=d&a[2]=e&a[4]=f&a[0]=g", parse_arrays=True),
            {"a": ["g", "d", "e", "c", "f", "b"]},
        )

        self.assertDictEqual(
            qs.parse("a[1]=b&a[15]=c", parse_arrays=True, allow_sparse_arrays=True), {"a": {1: "b", 15: "c"}}
        )

    def test_empty_string_as_array_value(self):
        import src.qstion as qs

        # empty string as array value
        self.assertDictEqual(qs.parse("a[]=", parse_arrays=True), {"a": [""]})

    def test_array_limit(self):
        import src.qstion as qs

        # array limit - default is 20, everything above is considered as object and whole array is converted to object
        self.assertDictEqual(qs.parse("a[]=1&a[]=2&a[]=3", parse_arrays=True), {"a": ["1", "2", "3"]})

        self.assertDictEqual(
            qs.parse("a[]=1&a[]=2&a[]=3&a[]=4", parse_arrays=True, array_limit=3),
            {"a": {"0": "1", "1": "2", "2": "3", "3": "4"}},
        )
        # over max limit by default
        self.assertDictEqual(qs.parse("a[100]=1", parse_arrays=True), {"a": {"100": "1"}})

    def test_parse_primitive(self):
        import src.qstion as qs

        # parse primitive - default is false
        # numbers are represented as decimal.Decimal
        self.assertDictEqual(qs.parse("a=1"), {"a": "1"})
        self.assertDictEqual(qs.parse("a=1", parse_primitive=True), {"a": decimal.Decimal(1)})

        # floats are represented as decimal.Decimal as well
        self.assertDictEqual(qs.parse("a=1.5"), {"a": "1.5"})
        self.assertDictEqual(qs.parse("a=1.5", parse_primitive=True), {"a": decimal.Decimal("1.5")})

        # booleas are accepted normally, with no strict case if primitive strict is false
        self.assertDictEqual(qs.parse("a=true"), {"a": "true"})
        self.assertDictEqual(qs.parse("a=true", parse_primitive=True), {"a": True})
        self.assertDictEqual(qs.parse("a=false"), {"a": "false"})
        self.assertDictEqual(qs.parse("a=false", parse_primitive=True), {"a": False})
        # use whatever case
        self.assertDictEqual(qs.parse("a=True", parse_primitive=True), {"a": True})
        self.assertDictEqual(qs.parse("a=False", parse_primitive=True), {"a": False})
        self.assertDictEqual(qs.parse("a=TRUE", parse_primitive=True), {"a": True})
        self.assertDictEqual(qs.parse("a=FALSE", parse_primitive=True), {"a": False})
        # when using primitive strict, only true/True and false/False are accepted
        self.assertDictEqual(qs.parse("a=true", parse_primitive=True, primitive_strict=True), {"a": True})
        self.assertDictEqual(qs.parse("a=false", parse_primitive=True, primitive_strict=True), {"a": False})
        self.assertDictEqual(qs.parse("a=True", parse_primitive=True, primitive_strict=True), {"a": True})
        self.assertDictEqual(qs.parse("a=False", parse_primitive=True, primitive_strict=True), {"a": False})
        # any other value is considered as string
        self.assertDictEqual(qs.parse("a=TRUE", parse_primitive=True, primitive_strict=True), {"a": "TRUE"})
        self.assertDictEqual(qs.parse("a=FALSE", parse_primitive=True, primitive_strict=True), {"a": "FALSE"})

        # null/None is accepted as well
        self.assertDictEqual(qs.parse("a=null"), {"a": "null"})
        self.assertDictEqual(qs.parse("a=null", parse_primitive=True), {"a": None})
        self.assertDictEqual(qs.parse("a=None"), {"a": "None"})
        self.assertDictEqual(qs.parse("a=None", parse_primitive=True), {"a": None})
        self.assertDictEqual(qs.parse("a=none"), {"a": "none"})
        self.assertDictEqual(qs.parse("a=none", parse_primitive=True), {"a": None})
        self.assertDictEqual(qs.parse("a=NONE", parse_primitive=True), {"a": None})
        self.assertDictEqual(qs.parse("a=NULL", parse_primitive=True), {"a": None})
        # same goes with strict primitive
        self.assertDictEqual(qs.parse("a=null", parse_primitive=True, primitive_strict=True), {"a": None})
        self.assertDictEqual(qs.parse("a=None", parse_primitive=True, primitive_strict=True), {"a": None})

    def test_comma_as_list(self):
        import src.qstion as qs

        # comma as list - default is false
        self.assertDictEqual(qs.parse("a=b,c"), {"a": "b,c"})
        self.assertDictEqual(qs.parse("a=b,c", comma=True), {"a": ["b", "c"]})

        # test combined syntax
        self.assertDictEqual(
            qs.parse("a=b,c&a[][d]=e,f&a[]=g", comma=True, parse_arrays=True), {"a": ["b", "c", {"d": ["e", "f"]}, "g"]}
        )

    def test_brackets_as_list(self):
        import src.qstion as qs

        # bracketed values as list - default is false
        self.assertDictEqual(qs.parse("a=[b,c]"), {"a": "[b,c]"})
        self.assertDictEqual(qs.parse("a=[b,c]", brackets=True), {"a": ["b", "c"]})
        # also works with quoted brackets
        self.assertDictEqual(qs.parse('a=["b","c"]', brackets=True), {"a": ["b", "c"]})
        self.assertDictEqual(qs.parse("a=[1,2]", brackets=True), {"a": ["1", "2"]})
        # also works with parse primitive
        self.assertDictEqual(qs.parse("a=[1,2]", brackets=True, parse_primitive=True), {"a": [1, 2]})
        # if parse primitive is enabled but user requires items as strings, using quotes is required
        self.assertDictEqual(qs.parse('a=["1","2"]', brackets=True, parse_primitive=True), {"a": ["1", "2"]})
        # NOTE: nesting brackets in value is not supported and will result as if separate values were provided
        # e.g.:
        self.assertDictEqual(qs.parse("a=[b,[c,d]]", brackets=True), {"a": ["b", "[c", "d]"]})

    def test_complex_query_strings(self):
        import src.qstion as qs

        # complex query strings
        self.assertDictEqual(
            qs.parse("a=b&c[0]=d&c[1]=e%3Df&f[0][0]=g&f[1][0]=h", parse_arrays=True),
            {"a": "b", "c": ["d", "e=f"], "f": [["g"], ["h"]]},
        )

        # NOTE arguments which are non-array and has no value such as query_string: `a` will not be parsed
        self.assertDictEqual(qs.parse("a&b[0]=c&b[1]=d", parse_arrays=True), {"b": ["c", "d"]})

        self.assertDictEqual(
            qs.parse("a=%82%B1%82%F1%82%C9%82%BF%82%CD%81I", charset="shift_jis"), {"a": "こんにちは！"}
        )


if __name__ == "__main__":
    unittest.main()
