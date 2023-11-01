import unittest
import sys
sys.path.append(".")


class ParserTest(unittest.TestCase):

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
            qs.stringify({'a': ['b', 'c', 'd']}),
            'a[0]=b&a[1]=c&a[2]=d')

        # Options for indices is not available, use array_format option instead:
        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']}, array_format='indices'),
            'a[0]=b&a[1]=c&a[2]=d')

        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']}, array_format='brackets'),
            'a[]=b&a[]=c&a[]=d')

        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']}, array_format='repeat'),
            'a=b&a=c&a=d')

        self.assertEqual(
            qs.stringify({'a': ['b', 'c', 'd']}, array_format='comma'),
            'a=b,c,d')

if __name__ == "__main__":
    unittest.main()