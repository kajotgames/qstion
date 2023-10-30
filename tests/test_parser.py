
import unittest
import sys
sys.path.append(".")
import src.qstion as qs

class ParserTest(unittest.TestCase):

    def test_basic_parse_objects(self):
        # tests based on README of qs in npm: https://www.npmjs.com/package/qs?activeTab=readme
        obj = qs.parse('a=c')
        self.assertDictEqual(obj, {'a': 'c'})

        # TODO not yet implemented
        # stringified = qs.stringify(obj)
        # self.assertEqual(stringified, 'a=c')

        self.assertDictEqual(qs.parse('foo[bar]=baz'), {'foo': {'bar': 'baz'}})

        # plain objects not supported -> unknown data type

        # uri encoded strings
        self.assertDictEqual(qs.parse('a%5Bb%5D=c'), {'a': {'b': 'c'}})

        # double nested
        self.assertDictEqual(
            qs.parse('foo[bar][baz]=foobarbaz'),
            {'foo': {'bar': {'baz': 'foobarbaz'}}})

        # default depth nesting -> 5
        self.assertDictEqual(
            qs.parse('a[b][c][d][e][f][g][h][i]=j'),
            {'a': {'b': {'c': {'d': {'e': {'f': {'[g][h][i]': 'j'}}}}}}})

        # overriding depth nesting -> 1
        self.assertDictEqual(
            qs.parse('a[b][c][d][e][f][g][h][i]=j', depth=1),
            {'a': {'b': {'[c][d][e][f][g][h][i]': 'j'}}})

        # parameter limited
        self.assertDictEqual(
            qs.parse('a=b&c=d', parameter_limit=1),
            {'a': 'b'})

        # parameter limited but multiple values
        self.assertDictEqual(
            qs.parse('a=b&a=c', parameter_limit=1),
            {'a': ['b', 'c']})

        # parameter limited but multiple values after reaching limit
        self.assertDictEqual(
            qs.parse('a=b&b=c&a=d', parameter_limit=1),
            {'a': ['b', 'd']})

        # TODO ignore prefix not supported yet

        # optional delimiter
        self.assertDictEqual(
            qs.parse('a=b;c=d', delimiter=';'),
            {'a': 'b', 'c': 'd'})

        # regular expression delimiter
        self.assertDictEqual(
            qs.parse('a=b;c=d,e=f', delimiter=r'[;,]'),
            {'a': 'b', 'c': 'd', 'e': 'f'})

        # dot notation
        self.assertDictEqual(
            qs.parse('a.b=c', allow_dots=True),
            {'a': {'b': 'c'}})

        # using old charset
        self.assertDictEqual(
            qs.parse('a=%A7', charset='iso-8859-1'),
            {'a': '§'})

        # TODO implement charsetSentinel

        # interpretNumericEntities &#...; syntax to the actual character
        self.assertDictEqual(
            qs.parse('a=%26%239786%3B',
                     interpret_numeric_entities=True, charset='iso-8859-1'),
            {'a': '☺'})

    def test_advanced_parse_objects(self):
        # two separate nested objects
        self.assertDictEqual(
            qs.parse('a[b]=c&d[e]=f'),
            {'a': {'b': 'c'}, 'd': {'e': 'f'}})

        # common base key for nested objects
        self.assertDictEqual(
            qs.parse('a[b]=c&a[d]=e'),
            {'a': {'b': 'c', 'd': 'e'}})

        # common nested key for nested objects
        self.assertDictEqual(
            qs.parse('a[b][c]=d&a[b][e]=f'),
            {'a': {'b': {'c': 'd', 'e': 'f'}}})

        # non equal nesting after creating basic object
        self.assertDictEqual(
            qs.parse('a[b]=c&a[b][d]=e'),
            {'a': {'b': {'d': 'e', 'c': True}}})

        # non equal basic object after nesting
        self.assertDictEqual(
            qs.parse('a[b][c]=d&a[b]=e'),
            {'a': {'b': {'c': 'd', 'e': True}}})

        # multiple values for same nested key
        self.assertDictEqual(
            qs.parse('a[b]=c&a[b]=d'),
            {'a': {'b': ['c', 'd']}})

        # multiple values for same nested key with different nesting
        self.assertDictEqual(
            qs.parse('a[b]=c&a[b]=f&a[b][d]=e'),
            {'a': {'b': {str(['c', 'f']): True, 'd': 'e'}}})

        # three elements for same nested key
        self.assertDictEqual(
            qs.parse('a[b]=c&a[b]=f&a[b]=e'),
            {'a': {'b': ['c', 'f', 'e']}})

    def test_basic_parse_arrays(self):
        # NOTE
        # since python list would by default not support sparse indexes, dictionary is used instead
        # however, notation is still strictly checked so array notation is accepted
        # and array-like dictionaries should only contain integer keys (unless notation was broken and
        # notation is combined - with basic objects - in which case the notation is ignored)
        # basic
        self.assertDictEqual(
            qs.parse('a[]=b&a[]=c', parse_arrays=True),
            {'a': {0: 'b', 1: 'c'}})

        # with indexes
        self.assertDictEqual(
            qs.parse('a[1]=c&a[0]=b', parse_arrays=True),
            {'a': {0: 'b', 1: 'c'}})

        # with indexes in sparse order
        # NOTE that order is not important in python dictionary
        self.assertDictEqual(
            qs.parse('a[1]=c&a[3]=b', parse_arrays=True),
            {'a': {1: 'c', 3: 'b'}})

        # sparse arrays such as [,,a,b] are not supported

        # array with empty string
        self.assertDictEqual(
            qs.parse('a[]=&a[]=b', parse_arrays=True, allow_empty=True),
            {'a': {0: '', 1: 'b'}})

        # also with index
        self.assertDictEqual(
            qs.parse('a[0]=b&a[1]=&a[2]=c',
                     parse_arrays=True, allow_empty=True),
            {'a': {0: 'b', 1: '', 2: 'c'}})

        # overflowing max array length
        self.assertDictEqual(
            qs.parse('a[100]=b', parse_arrays=True),
            {'a': {'100': 'b'}})

        # overriding max array length
        self.assertDictEqual(
            qs.parse('a[1]=b', parse_arrays=True, array_limit=0),
            {'a': {'1': 'b'}})

        # NOTE: disabling parsing arrays and trying to parse array
        # notation is such case: a[]=b will not result in {'a': {'0': 'b'}}
        # but rather {'a': {'': 'b'}} -> only if empty string is allowed
        # else is considered unparsable and used urllib.parse_qs instead
        self.assertDictEqual(
            qs.parse('a[]=b', parse_arrays=False, allow_empty=True),
            {'a': {'': 'b'}})

        self.assertDictEqual(
            qs.parse('a[]=b', parse_arrays=False, allow_empty=False),
            {'a[]': ['b']})

        # If you mix notations, qs will merge the two items into an object:
        self.assertDictEqual(
            qs.parse('a[]=b&a[c]=d', parse_arrays=True),
            {'a': {'0': 'b', 'c': 'd'}})

        # You can also create arrays of objects:
        self.assertDictEqual(
            qs.parse('a[][b]=c', parse_arrays=True),
            {'a': {0: {'b': 'c'}}})

        # Some people use comma to join array, qs can parse it:
        self.assertDictEqual(
            qs.parse('a=b,c', comma=True),
            {'a': ['b', 'c']})

    # TODO add tests for primitive/scalar values


if __name__ == '__main__':
    unittest.main()
