import unittest
import sys
sys.path.append(".")


class ParserTest(unittest.TestCase):

    def test_basic_parse_objects(self):
        import src.qstion as qs
        # tests based on README of qs in npm: https://www.npmjs.com/package/qs?activeTab=readme
        obj = qs.parse('a=c')
        self.assertDictEqual(obj, {'a': 'c'})

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

        # Some services add an initial utf8=✓ value to forms so that old Internet Explorer versions are more likely to submit the form as utf-8.
        # qs supports this mechanism via the charsetSentinel option.
        # If specified, the utf8 parameter will be omitted from the returned object.
        # It will be used to switch to iso-8859-1/utf-8 mode depending on how the checkmark is encoded.
        # Important: When you specify both the charset option and the charsetSentinel option,
        #  the charset will be overridden when the request contains a utf8 parameter from which the actual charset can be deduced.
        # In that sense the charset will behave as the default charset rather than the authoritative charset.\
        self.assertDictEqual(
            qs.parse('utf8=%E2%9C%93&a=%C3%B8',
                     charset_sentinel=True, charset='iso-8859-1'),
            {'a': 'ø'})

        self.assertDictEqual(
            qs.parse('utf8=%26%2310003%3B&a=%F8',
                     charset_sentinel=True, charset='utf-8'),
            {'a': 'ø'})

        # interpretNumericEntities &#...; syntax to the actual character
        self.assertDictEqual(
            qs.parse('a=%26%239786%3B',
                     interpret_numeric_entities=True, charset='iso-8859-1'),
            {'a': '☺'})

    def test_advanced_parse_objects(self):
        import src.qstion as qs

        # test parse from url
        self.assertDictEqual(
            qs.parse('http://example.com/?a=b', from_url=True),
            {'a': 'b'})

        # test unparsable qs
        self.assertDictEqual(
            qs.parse('this_is_unparsable'),
            {})

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

        # test array as string value
        self.assertDictEqual(
            qs.parse('a=[b,c]'),
            {'a': ['b', 'c']})

        # test very empty objects
        self.assertDictEqual(
            qs.parse('a[]=&b[]=', allow_empty=True),
            {'a': {'': ''}, 'b': {'': ''}})

        # test charset sentinel arg, but not as leading arg
        self.assertDictEqual(
            qs.parse('a=%A7&utf8=%26%2310003',
                     charset='utf-8', charset_sentinel=True),
            {'a': '§'}
        )

        # Special case : nesting to non-nested argument
        # NOTE: assuming that querystring 'a[b]=c&a[b][d]=e' parses into
        # {'a': {'b': {'d': 'e', 'c': True}}}
        # Handling of 'overloading' argument in such way: 'a[b]=c&a[b][c]=d'
        # will result in combining both True and 'd' into array
        self.assertDictEqual(
            qs.parse('a[b]=c&a[b][c]=d'),
            {'a': {'b': {'c': [True, 'd']}}})

        # test not allowing empty keys
        self.assertDictEqual(
            qs.parse('a[]=b&a[]=c&'),
            {'a[]': ['b', 'c']})

        # test dot notation with max depth
        self.assertDictEqual(
            qs.parse('a.b.c.d=e', allow_dots=True, depth=1),
            {'a': {'b': {'c.d': 'e'}}})

        # test exact depth
        self.assertDictEqual(
            qs.parse('a.b.c.d=e', allow_dots=True, depth=2),
            {'a': {'b': {'c': {'d': 'e'}}}})

        # test charset_sentinel option without utf8 present
        self.assertDictEqual(
            qs.parse('a=%A7', charset_sentinel=True, charset='iso-8859-1'),
            {'a': '§'})

        # test charset_sentinel option with utf8 present and '✓' encoded in unkown charset
        self.assertDictEqual(
            qs.parse('utf8=%2BJxM-&a=b', charset_sentinel=True),
            {'a': ['b'], 'utf8': ['+JxM-']}
        )

        # test unbalanced brackets - and thus unparsable by qstion
        self.assertDictEqual(
            qs.parse('a[b=c'),
            {'a[b': ['c']})

        # test balanced but nested brackets
        self.assertDictEqual(
            qs.parse('a[b[c]]=d'),
            {'a[b[c]]': ['d']})

        # test only closing brackets
        self.assertDictEqual(
            qs.parse('a[b]]]=d'),
            {'a[b]]]': ['d']})

        # test correct brackets but broken nested notation
        self.assertDictEqual(
            qs.parse('a[b][c]d=e'),
            {'a[b][c]d': ['e']})

    def test_basic_parse_arrays(self):
        import src.qstion as qs
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
            qs.parse('a[1]=b&a[15]=c', parse_arrays=True),
            {'a': {1: 'b', 15: 'c'}})

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

        # test double initialization of array with second index
        self.assertDictEqual(
            qs.parse('a[][1]=c', parse_arrays=True),
            {'a': {1: 'c'}})

        # test array notation on non array arguments
        self.assertDictEqual(
            qs.parse('a=c', parse_arrays=True),
            {'a': 'c'})

        # test over parameter limit in array notation
        self.assertDictEqual(
            qs.parse('a[0]=b&a[1]=c&b[]=x',
                     parameter_limit=1, parse_arrays=True),
            {'a': {0: 'b', 1: 'c'}})

    def test_basic_primitive_values(self):
        import src.qstion as qs
        # test some basic string values
        self.assertDictEqual(
            qs.parse('a=b'),
            {'a': 'b'})

        # with allowed primitive values, nothing should change
        self.assertDictEqual(
            qs.parse('a=b', parse_primitive=True),
            {'a': 'b'})

        # test with integer value
        self.assertDictEqual(
            qs.parse('a=1'),
            {'a': '1'})

        # with allowed primitive values, parsed should be integer
        self.assertDictEqual(
            qs.parse('a=1', parse_primitive=True),
            {'a': 1})

        # test with float value
        self.assertDictEqual(
            qs.parse('a=1.1'),
            {'a': '1.1'})

        # with allowed primitive values, parsed should be float
        self.assertDictEqual(
            qs.parse('a=1.1', parse_primitive=True),
            {'a': 1.1})

        # test with boolean value
        self.assertDictEqual(
            qs.parse('a=true&b=false'),
            {'a': 'true', 'b': 'false'})

        # with allowed primitive values, parsed should be boolean
        self.assertDictEqual(
            qs.parse('a=true&b=false', parse_primitive=True),
            {'a': True, 'b': False})

        # test with null value
        self.assertDictEqual(
            qs.parse('a=null&b=NULL&c=Null&d=None'),
            {'a': 'null', 'b': 'NULL', 'c': 'Null', 'd': 'None'})

        # with allowed primitive values, parsed should be None
        self.assertDictEqual(
            qs.parse('a=null&b=None', parse_primitive=True),
            {'a': None, 'b': None})

        # test array of primitive values
        self.assertDictEqual(
            qs.parse('a[]=1&a[]=2&a[]=3', parse_arrays=True),
            {'a': {0: '1', 1: '2', 2: '3'}})

        # with allowed primitive values, parsed should be array of integers
        self.assertDictEqual(
            qs.parse('a[]=1&a[]=2&a[]=3', parse_arrays=True,
                     parse_primitive=True),
            {'a': {0: 1, 1: 2, 2: 3}})

        # test classic array of primitive values
        self.assertDictEqual(
            qs.parse('a=[1,2,3]'),
            {'a': ['1', '2', '3']})

        # with allowed primitive values, parsed should be array of integers
        self.assertDictEqual(
            qs.parse('a=[1,2,3]', parse_primitive=True),
            {'a': [1, 2, 3]})

        # test classic array of primitive values with mixed types
        self.assertDictEqual(
            qs.parse('a=[1,a,true,Null]'),
            {'a': ['1', 'a', 'true', 'Null']})

        # with allowed primitive values, parsed should be array of primitives with mixed types
        self.assertDictEqual(
            qs.parse('a=[1,a,true,null]', parse_primitive=True),
            {'a': [1, 'a', True, None]})

        # test primitive values with non-strict keywords for bool and null
        self.assertDictEqual(
            qs.parse('a=True&b=False&c=none', parse_primitive=True),
            {'a': 'True', 'b': 'False', 'c': 'none'})

        # test primitive values with non-strict option
        self.assertDictEqual(
            qs.parse('a=True&b=False&c=NULL',
                     parse_primitive=True, primitive_strict=False),
            {'a': True, 'b': False, 'c': None})


if __name__ == '__main__':
    unittest.main()
