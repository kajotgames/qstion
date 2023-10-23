import unittest
from qstion import parser as p


class ParserTest(unittest.TestCase):

    def test_single_argument(self):
        qs = p.QsParser.parse('http://localhost:5000/?a=b')
        self.assertEqual(qs.args, {'a': 'b'})

    def test_multiple_arguments(self):
        qs = p.QsParser.parse('http://localhost:5000/?a=b&c=d')
        self.assertEqual(qs.args, {'a': 'b', 'c': 'd'})

    def test_nested_single_argument(self):
        qs = p.QsParser.parse('http://localhost:5000/?a[b]=c')
        self.assertEqual(qs.args, {'a': {'b': 'c'}})

    def test_double_nested_single_argument(self):
        qs = p.QsParser.parse('http://localhost:5000/?a[b][c]=d')
        self.assertEqual(qs.args, {'a': {'b': {'c': 'd'}}})

    def test_multiple_nested(self):
        qs = p.QsParser.parse('http://localhost:5000/?a[b]=c&a[d]=e')
        self.assertEqual(qs.args, {'a': {'b': 'c', 'd': 'e'}})

    def test_multiple_nested_double(self):
        qs = p.QsParser.parse('http://localhost:5000/?a[b][c]=d&a[b][e]=f')
        self.assertEqual(qs.args, {'a': {'b': {'c': 'd', 'e': 'f'}}})

    def test_partially_nested(self):
        qs = p.QsParser.parse('http://localhost:5000/?a[b]=c&a[b][d]=e')
        print(qs._max_depth)
        self.assertEqual(qs.args, {'a': {'b': {'d': 'e', 'c': True}}})

    def test_max_depth(self):
        qs = p.QsParser.parse(
            'http://localhost:5000/?a[b][c][d][e][f][g][h][i]=j', depth=5)
        self.assertEqual(
            qs.args, {'a': {'b': {'c': {'d': {'e': {'f': {'[g][h][i]': 'j'}}}}}}})

    def test_min_depth(self):
        qs = p.QsParser.parse(
            'http://localhost:5000/?a[b][c][d][e][f][g][h][i]=j', depth=1)
        self.assertEqual(qs.args, {'a': {'b': {'[c][d][e][f][g][h][i]': 'j'}}})

    def test_empty_val(self):
        qs = p.QsParser.parse('http://localhost:5000/?a[b]=')
        self.assertEqual(qs.args, {'a': {'b': ''}})

    # NOTE NOT SUPPORTED yet
    # def test_empty_key(self):
    #     qs = p.QsParser.from_url('http://localhost:5000/?=x')
    #     self.assertEqual(qs.args, {'': 'x'})


if __name__ == '__main__':
    unittest.main()
