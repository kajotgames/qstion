import unittest
import sys
sys.path.append(".")


class StringifyTest(unittest.TestCase):

    def test_basic_stringify_objects(self):
        import src.qstion as qs

        self.assertEqual(
            qs.stringify({'a': 'b'}),
            'a=b')

        # basic nested
        self.assertEqual(
            qs.stringify({'a': {'b': 'c'}}),
            'a%5Bb%5D=c')

        # encoding option
        self.assertEqual(
            qs.stringify({'a': {'b': 'c'}}, encode=False),
            'a[b]=c')

        # encoding values only
        self.assertEqual(
            qs.stringify(
                {'a': 'b', 'c': ['d', 'e=f'], 'f': [['g'], ['h']]},
                encode_values_only=True, encode=False
            ),
            'a=b&c[0]=d&c[1]=e%3Df&f[0][0]=g&f[1][0]=h'
        )

        # When arrays are stringified, by default they are given explicit indices:
        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']}, encode=False),
            'a[0]=b&a[1]=c&a[2]=d')

        # Options for indices is not available, use array_format option instead:
        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']},
                         array_format='indices', encode=False),
            'a[0]=b&a[1]=c&a[2]=d')

        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']},
                         array_format='brackets', encode=False),
            'a[]=b&a[]=c&a[]=d')

        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']},
                         array_format='repeat', encode=False),
            'a=b&a=c&a=d')

        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']},
                         array_format='comma', encode=False),
            'a=b,c,d')

        # When objects are stringified, by default they use bracket notation:
        self.assertEqual(
            qs.stringify({'a': {'b': {'c': 'd', 'e': 'f'}}}, encode=False),
            'a[b][c]=d&a[b][e]=f')

        # You may override this to use dot notation by setting the allowDots option to true:
        self.assertEqual(
            qs.stringify({'a': {'b': {'c': 'd', 'e': 'f'}}},
                         allow_dots=True, encode=False),
            'a.b.c=d&a.b.e=f')

        # Empty strings and null values will omit the value, but the equals sign (=) remains in place:
        self.assertEqual(
            qs.stringify({'a': ''}, encode=False), 'a=')

    def test_advanced_stringify_objects(self):
        import src.qstion as qs

        # Key with no values (such as an empty object or array) will return nothing:

        self.assertEqual(
            qs.stringify({'a': []}, encode=False), '')

        self.assertEqual(
            qs.stringify({'a': {}}, encode=False), '')

        self.assertEqual(
            qs.stringify({'a': [{}]}, encode=False), '')

        self.assertEqual(
            qs.stringify({'a': {'b': {}}}, encode=False), '')

        self.assertEqual(
            qs.stringify({'a': {'b': []}}, encode=False), '')

        # Properties that are set to `undefined` will be omitted entirely
        # NOTE undefined is not available in python -> handled as null -> None

        self.assertEqual(
            qs.stringify({'a': None}, encode=False), '')

        # The delimiter may be overridden with stringify as well:

        self.assertEqual(
            qs.stringify({'a': 'b', 'c': 'd'}, delimiter=';'),
            'a=b;c=d')

        # You may use the sort option to affect the order of parameter keys -> only functions as bool option:

        self.assertEqual(
            qs.stringify({'a': 'c', 'z': 'y', 'b': 'f'}, sort=True),
            'a=c&b=f&z=y')

        # also implemented reverse sort

        self.assertEqual(
            qs.stringify({'a': 'c', 'z': 'y', 'b': 'f'},
                         sort=True, sort_reverse=True),
            'z=y&b=f&a=c')

        # NOTE passing functions as filter is not available, use list as value
        self.assertEqual(
            qs.stringify({'a': 'b', 'c': 'd', 'e': 'f'},
                         filter=['a', 'e'], encode=False),
            'a=b&e=f')

        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd'], 'e': 'f'},
                         filter=['a', 0, 2], encode=False),
            'a[0]=b&a[2]=d')

        # If you're communicating with legacy systems, you can switch to iso-8859-1 using the charset option:
        self.assertEqual(
            qs.stringify({'æ': 'æ'}, charset='iso-8859-1'),
            '%E6=%E6')

        # Characters that don't exist in iso-8859-1 will be converted to numeric entities, similar to what browsers do:

        self.assertEqual(
            qs.stringify({'a': '☺'}, charset='iso-8859-1'),
            'a=%26%239786%3B')

        # You can use the charsetSentinel option to announce the character by including an utf8=✓ parameter with the proper encoding if the checkmark

        self.assertEqual(
            qs.stringify({'a': '☺'}, charset_sentinel=True),
            'utf8=%E2%9C%93&a=%E2%98%BA')

        self.assertEqual(
            qs.stringify({'a': 'æ'}, charset='iso-8859-1',
                         charset_sentinel=True),
            'utf8=%26%2310003%3B&a=%E6'
        )

        # Dealing with special character sets : visit https://docs.python.org/3/library/codecs.html#standard-encodings

        # array format as brackets for array with shifted index
        self.assertEqual(
            qs.stringify({'a': {1: 'b', 2: 'c'}},
                         array_format='brackets', encode=False),
            'a[]=b&a[]=c'
        )

        # use comma as delimiter
        self.assertEqual(
            qs.stringify({'a': {1: 'b', 2: 'c'}},
                         array_format='comma', encode=False),
            'a=b,c'
        )

        # test unkown options for array_format
        self.assertRaises(ValueError, qs.stringify,
                          {'a': {1: 'b', 2: 'c'}}, array_format='unknown')

        # test bracket notation on basic object
        self.assertEqual(
            qs.stringify({'a': {'b': 'c'}},
                         array_format='brackets', encode=False),
            'a[b]=c'
        )

        # test bracket notation on deeper nesting
        self.assertEqual(
            qs.stringify({'a': {'b': {'c': 'd'}}},
                         array_format='brackets', encode=False),
            'a[b][c]=d'
        )

        # use comma delimiter in nested objects
        self.assertEqual(
            qs.stringify({'a': {'b': ['c', 'd']}},
                         array_format='comma', encode=False),
            'a[b]=c,d'
        )

        # use repeat on nested objects
        self.assertEqual(
            qs.stringify({'a': {'b': {1: 'c',2: 'd'}}}, array_format='repeat', encode=False),
            'a[b]=c&a[b]=d'
        )


if __name__ == "__main__":
    unittest.main()
