from .base import QS, QsNode
import urllib.parse as up
import typing as t


class QsStringifier(QS):
    _delimiter: str

    def __init__(self, depth: int = 5, parameter_limit: int = 1000, allow_dots: bool = False, allow_sparse: bool = False, array_limit: int = 20, parse_arrays: bool = False, allow_empty: bool = False, comma: bool = False, delimiter: str = '&'):
        super().__init__(depth, parameter_limit, allow_dots,
                         allow_sparse, array_limit, parse_arrays, allow_empty, comma)
        self._delimiter = delimiter

    @staticmethod
    def _q(key: str, value: str) -> str:
        return f'{up.quote(key)}={up.quote(value)}'

    def stringify(self, data: dict) -> str:
        """
        Process a dictionary into a query string

        Args:
            data (dict): dictionary to process
            depth (int): max depth of nested objects
            - e.g. depth=1 : {'a': {'b': 'c'}} -> a[b]=c
            parameter_limit (int): max number of parameters to parse (in keyword count)
            allow_dots (bool): allow dot notation
            - e.g. {'a': {'b': 'c'}} -> a.b=c
            allow_sparse (bool): allow sparse arrays
            - e.g. {'a': [,'b',,'c']} -> a[1]=b&a[5]=c
            array_limit (int): max number of elements in array
            if limit is reached, array is converted to object
            parse_arrays (bool): parse array values as or keep object notation
            comma (bool): allow comma separated values
            - e.g. {'a': ['b', 'c']} -> a=b,c

        Returns:    
            str: query string
        """
        _q_args = {}
        for item in data:
            self._qs_tree[item] = QsNode.load(
                item,
                data[item],
                parse_arrays=self._parse_arrays)
        for item in self._qs_tree.values():
            for arg in self._get_arg(item):
                _q_args.update(self._transform_arg(arg))
        return self._delimiter.join([self._q(*i) for i in _q_args.items()])

    def _get_arg(self, node: QsNode) -> tuple[str, t.Any]:
        if node.is_leaf():
            yield ([node.key], node.value)
        else:
            for child in node.children:
                for arg in self._get_arg(child):
                    yield ([*arg[0], node.key], arg[1])

    def _transform_arg(self, arg: tuple[list, t.Any]) -> dict:
        notation, value = arg
        if len(notation) == 1:
            return {notation[0]: value}
        key = notation.pop()
        if self._allow_dots:
            for i in reversed(notation):
                key = f'{key}.{i}'
        else:
            for i in reversed(notation):
                key = f'{key}[{i}]'
        return {key: value}


def stringify(
        data: dict,
        depth: int = 5,
        parameter_limit: int = 1000,
        allow_dots: bool = False,
        allow_sparse: bool = False,
        array_limit: int = 20,
        parse_arrays: bool = False,
        allow_empty: bool = False,
        comma: bool = False,
) -> str:
    pass
