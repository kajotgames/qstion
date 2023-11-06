from .base import QS, QsNode
import urllib.parse as up
import typing as t

LIST_FORMAT_OPTIONS = ['indices', 'brackets', 'repeat', 'comma']


class QsStringifier(QS):
    _af: str = 'indices'

    def __init__(self, depth: int = 5, parameter_limit: int = 1000, allow_dots: bool = False, allow_sparse: bool = False, array_limit: int = 20, parse_arrays: bool = False, allow_empty: bool = False, comma: bool = False, array_format: str = 'indices'):
        super().__init__(depth, parameter_limit, allow_dots,
                         array_limit, parse_arrays, allow_empty, comma)
        if array_format not in LIST_FORMAT_OPTIONS:
            raise ValueError(
                f'array_format must be one of {LIST_FORMAT_OPTIONS}')
        self._af = array_format

    def stringify(self, data: dict, filter: list = None) -> list[tuple]:
        """
        Process a dictionary into a query string

        Args:
            data (dict): dictionary to process
            filter (list): list of keys to filter

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
        """
        Format key based on array_format into proper string representation recursively

        Args:
            key (list): list of keys

        Returns:
            str: formatted key
        """
        if len(key) == 1:
            # decide based on array_format
            k = key[0]
            k = key[0]
            if isinstance(k, int) and (self._af == 'repeat' or self._af == 'brackets'):
                return '[]' if self._af == 'brackets' else None
            else:
                return f'[{k}]' if not self._allow_dots else k
        else:
            current_key = key.pop()
            formatted = self._format_key(key)
            if formatted is None:
                return f'[{current_key}]' if not self._allow_dots else f'.{current_key}'
            if self._allow_dots:
                return f'{current_key}.{formatted}'
            return f'[{current_key}]{formatted}'

    def _get_arg(self, node: QsNode) -> tuple[str, t.Any]:
        """
        Get argument from node recursively as generator

        Args:
            node (QsNode): node to process

        Returns:
            tuple[str, Any]: argument
        """
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
        """
        Transform argument into proper string format

        Args:
            arg (tuple[list, Any]): argument

        Returns:
            tuple[str, Any]: transformed argument
        """
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
        encode: bool = True,
        delimiter: str = '&',
        encode_values_only: bool = False,
        array_format: str = 'indices',
        sort: bool = False,
        sort_reverse: bool = False,
        charset: str = 'utf-8',
        filter: list = None,
        charset_sentinel: bool = False,
) -> str:
    """
    Process a dictionary into a query string

    Args:
        data (dict): dictionary to process
        allow_dots (bool): use dot notation instead of brackets
        encode (bool): encode values and keys
        delimiter (str): delimiter to use
        encode_values_only (bool): encode only values
        array_format (str): array format to use
        sort (bool): sort query string
        sort_reverse (bool): sort query string in reverse
        charset (str): charset to use
        filter (list): list of keys to filter
        charset_sentinel (bool): add utf8 sentinel

    Returns:    
        str: query string
    """
    qs = QsStringifier(
        allow_dots=allow_dots,
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
        return delimiter.join([f'{k}={up.quote(v, encoding=charset, errors="xmlcharrefreplace")}' for k, v in _qt])
    return delimiter.join([f'{k}={v}' for k, v in _qt])
