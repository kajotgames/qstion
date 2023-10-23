import typing as t
import urllib.parse as up
import re

t_Delimiter = t.Union[str, t.Pattern[str]]

class QsParser:
    _args: dict = None
    _depth: int = 5
    _parameter_limit: int = 1000
    _allow_dots: bool = False
    _allow_sparse: bool = False
    _array_limit: int = 20
    _parse_arrays: bool = False
    _comma: bool = False

    # maybe use classic up.parse_qs instead of this class
    def __init__(
            self, 
            args: list[str],
            depth: int,
            parameter_limit: int,
            allow_dots: bool,
            allow_sparse: bool,
            array_limit: int,
            parse_arrays: bool,
            comma: bool,
            ):
        """
        Args:
            args (list): list of arguments to parse
            depth (int): max depth of nested objects
            - e.g. depth=1 : a[b]=c -> {'a': {'b': 'c'}}
            - depth=1 : a[b][c]=d -> {'a': { '['b']['c']' : 'd'}}
            parameter_limit (int): max number of parameters to parse (in keyword count)
            allow_dots (bool): allow dot notation
            - e.g. a.b=c -> {'a': {'b': 'c'}}
            allow_sparse (bool): allow sparse arrays
            - e.g. a[1]=b&a[5]=c -> {'a': [,'b',,'c']}
            array_limit (int): max number of elements in array
            if limit is reached, array is converted to object
            parse_arrays (bool): parse array values as or keep object notation
            comma (bool): allow comma separated values
            - e.g. a=b,c -> {'a': ['b', 'c']}
        """
        self._args = {}
        self._max_depth = depth
        self._parameter_limit = parameter_limit
        self._allow_dots = allow_dots
        self._allow_sparse = allow_sparse
        self._array_limit = array_limit
        self._parse_arrays = parse_arrays
        self._comma = comma
        for arg in args:
            pass




    @property
    def args(self) -> dict[str, str]:
        """
        Returns parsed arguments.
        """
        return self._args

    # Todo : according to qs in npm, delimiter can be a regex -> remove default value
    # todo : allow dot notation
    # TODO: parsing of array notation : a[]=b&a[]=c -> {'a': ['b', 'c']}
    # a[1]=c&a[0]=b -> {'a': ['b', 'c']}
    # -> allow sparse arrays option
    # -> empty string as value option
    # -> array limit option (max number of elements in array, converting to object if limit is reached)
    # -> parse array option (parse array values as numbers or booleans)
    # - mixing notation will result in object notation
    # comma option for array notation
    @classmethod
    def parse(
        cls, 
        url: str, 
        delimiter: t_Delimiter = '&', 
        depth: int = 5, 
        parameter_limit: int = 1000,
        allow_dots: bool = False,
        allow_sparse: bool = False,
        array_limit: int = 20,
        parse_arrays: bool = False,
        comma: bool = False,
        ) -> dict:
        """
        Creates a parser from a url.
        """
        args = []
        parsed_url = up.urlparse(url)
        query_args = re.split(delimiter, parsed_url.query, maxsplit=parameter_limit)
        for arg in query_args:
            args.append(cls._unq(arg))
        return 

    @staticmethod
    def _unq(arg: str) -> str:
        """
        Unquotes a string (removes url encoding).

        Args:
            arg (str): string to unquote

        Returns:
            str: unquoted string
        """
        arg_key, arg_val = arg.split('=')
        return f'{up.unquote(arg_key)}={up.unquote(arg_val)}'

    def _parse_arg(self, k: str, v: str) -> None:
        """
        Parses a single argument into a nested dict.
        """
        nested = self._parse_key(k)
        self._args = QsParser._add_nested(
            nested, v, self._args, depth=self._max_depth+1)

    @staticmethod
    def _handle_incoming(incoming) -> dict:
        """
        Helper function to handle incoming dict in recursive calls.
        """
        if incoming is None:
            return {}
        if isinstance(incoming, str):
            return {incoming: True}
        if isinstance(incoming, dict):
            return incoming

    @staticmethod
    def _handle_add(incoming: dict, k, v):
        """
        Helper function to handle adding a key to a dict in recursive calls.
        """
        if incoming == {}:
            return {k: v}
        if k not in incoming:
            incoming[k] = v
        else:
            incoming[k].update({v: True})
        return incoming

    @staticmethod
    def _add_nested(keys: list, v: str, incoming: dict = None, depth: int = 5) -> dict:
        """
        Recursive function to add url param as item into nested dict.
        """
        incoming = QsParser._handle_incoming(incoming)
        if len(keys) == 1 or depth == 0:
            key_arg = f'[{"][".join(keys)}]' if len(keys) > 1 else keys[0]
            return QsParser._handle_add(incoming, key_arg, v)
        if keys[0] not in incoming:
            incoming[keys[0]] = QsParser._add_nested(
                keys[1:], v, depth=depth - 1)
        else:
            incoming[keys[0]] = QsParser._add_nested(
                keys[1:], v, incoming[keys[0]], depth=depth - 1)
        return incoming

    def _parse_key(self, k: str) -> list:
        """
        Parses key into a list of nested keys.
        """
        if res := re.match(r'^(\w+)(\[\w+\])*$', k):
            nested = re.findall(r'\[(\w+)\]', k)
            return [res.group(1)] + nested


if __name__ == '__main__':
    url = 'http://localhost:5500/students?name[in]=richard&name[in]=eduardo'
    print(QsParser.parse(url))