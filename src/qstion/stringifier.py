from .base import QS, QsNode
import urllib.parse as up
import typing as t

LIST_FORMAT_OPTIONS = ['indices', 'brackets', 'repeat', 'comma']


class QsStringifier(QS):
    _af: str = 'indices'

    def __init__(self, depth: int = 5, parameter_limit: int = 1000, allow_dots: bool = False, allow_sparse: bool = False, array_limit: int = 20, parse_arrays: bool = False, allow_empty: bool = False, comma: bool = False, array_format: str = 'indices'):
        super().__init__(depth, parameter_limit, allow_dots,
                         allow_sparse, array_limit, parse_arrays, allow_empty, comma)
        if array_format not in LIST_FORMAT_OPTIONS:
            raise ValueError(
                f'array_format must be one of {LIST_FORMAT_OPTIONS}')
        self._af = array_format

    def stringify(self, data: dict, filter: list = None) -> list[tuple]:
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
            node = QsNode.load(
                item,
                data[item],
                filter=filter)
            if node is not None:
                self._qs_tree[node.key] = node
        for item in self._qs_tree.values():
            for arg in self._get_arg(item):
                if arg is None:
                    continue
                prepared_arg = self._transform_arg(arg)
                if prepared_arg[0] in _q_args:
                    _q_args[prepared_arg[0]] = [_q_args[prepared_arg[0]], prepared_arg[1]] if isinstance(
                        _q_args[prepared_arg[0]], str) else [*_q_args[prepared_arg[0]], prepared_arg[1]]
                else:
                    _q_args[prepared_arg[0]] = prepared_arg[1]
        res = []
        for key, value in _q_args.items():
            if isinstance(value, list) and (self._af == 'repeat' or self._af == 'brackets'):
                res += [(key, v) for v in value]
            else:
                res.append((key, str(value)))
        return res

    def _format_key(self, key: list) -> str | None:
        if len(key) == 1:
            # decide based on array_format
            k = key[0]
            match self._af:
                case 'indices':
                    return f'[{k}]' if not self._allow_dots else k
                case 'brackets':
                    if isinstance(k, int):
                        return f'[]'
                    return f'[{k}]'
                case 'repeat':
                    return None
                case 'comma':
                    return None
        else:
            current_key = key.pop()
            formatted = self._format_key(key)
            if formatted is None:
                return f'[{current_key}]' if not self._allow_dots else f'.{current_key}'
            if self._allow_dots:
                return f'{current_key}.{formatted}'
            return f'[{current_key}]{formatted}'

    def _get_arg(self, node: QsNode) -> tuple[str, t.Any]:
        if node.is_leaf():
            if node.is_empty():
                yield None
            else:
                yield ([node.key], node.value)
        elif node.is_default_array() and self._af == 'comma':
            yield ([node.key], ','.join([str(child.value) for child in node.children]))
        else:
            for child in node.children:
                for arg in self._get_arg(child):
                    yield arg if arg is None else ([*arg[0], node.key], arg[1])

    def _transform_arg(self, arg: tuple[list, t.Any]) -> tuple[str, t.Any]:
        notation, value = arg
        if len(notation) == 1:
            return (notation[0], value)
        key = notation.pop()
        nesting = self._format_key(notation)
        if self._allow_dots:
            key = f'{key}{("." + nesting) if nesting is not None else ""}'
        else:
            key = f'{key}{nesting or ""}'
        return (key, value)


def stringify(
        data: dict,
        allow_dots: bool = False,
        allow_empty: bool = False,
        encode: bool = True,
        delimiter: str = '&',
        encode_values_only: bool = False,
        array_format: str = 'indices',
        sort: bool = False,
        sort_reverse: bool = False,
        charset: str = 'utf-8',
        # TODO implement filter to be callable
        filter: list = None,
        charset_sentinel: bool = False,
) -> str:
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
        encode (bool): encode query string

    Returns:    
        str: query string
    """
    qs = QsStringifier(
        allow_dots=allow_dots,
        allow_empty=allow_empty,
        array_format=array_format
    )
    _qt = qs.stringify(data, filter=filter)
    if charset_sentinel:
        _qt.insert(0, ('utf8', '✓'))
    if sort:
        _qt = sorted(_qt, key=lambda x: x[0], reverse=sort_reverse)
    if encode:
        return delimiter.join([qs._q(k, v, charset=charset) for k, v in _qt])
    elif encode_values_only:
        return delimiter.join([f'{k}={up.quote(v, encoding=charset)}' for k, v in _qt])
    return delimiter.join([f'{k}={v}' for k, v in _qt])
