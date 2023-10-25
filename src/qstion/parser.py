import typing as t
import urllib.parse as up
import re


t_Delimiter = t.Union[str, t.Pattern[str]]


class ArrayParse:
    _depth: int = 5
    _limit: int = 20

    @classmethod
    def process(cls, notation: list, val: str, depth: int = 5, max_limit: int = 20) -> list:
        """
        Performs a syntax check on the key. works as state machine.
        """
        cls._limit = max_limit
        cls._depth = depth
        return cls.process_notation(notation, val)

    @classmethod
    def process_notation(cls, notation: list[str], val: t.Any) -> dict:
        """
        Parses array notation recursively.
        """
        if not notation:
            return val
        current = notation[0]
        if current.isdigit():
            if int(current) > cls._limit:
                raise IndexError('Array limit reached')
            return {int(current): cls.process_notation(notation[1:], val)}
        elif current == '':
            res = cls.process_notation(notation[1:], val)
            if not isinstance(res, dict):
                return {None: res}
            if not all(isinstance(x, (int, type(None))) for x in res.keys()):
                # initialization of array without index - set index None to be handled by parser
                return {None: res}
            return res
        else:
            return {current: cls.process_notation(notation[1:], val)}


class LHSParse:
    _depth: int = 5
    _dots: bool = False
    _allow_empty: bool = False

    @classmethod
    def process(
        cls,
        notation: list,
        val: str,
        depth: int = 5,
        allow_empty: bool = False,
        allow_dots: bool = False
    ) -> dict:
        """
        Parses left hand side notation recursively.
        """
        cls._depth = depth
        cls._allow_empty = allow_empty
        cls._dots = allow_dots
        return cls.process_notation(notation, val)

    @classmethod
    def process_notation(cls, notation: list[str], val: t.Any) -> dict:
        """
        Parses left hand side notation recursively.
        """
        if not notation:
            return val
        current = notation[0]
        if current == '' and not cls._allow_empty:
            raise ValueError('Empty key not allowed')
        if cls._depth <= 0:
            # join current and rest of notation
            current_key = cls._max_depth_key(notation)
            return {current_key: val}
        cls._depth -= 1
        return {current: cls.process_notation(notation[1:], val)}

    @classmethod
    def _max_depth_key(cls, notation: list[str]) -> str:
        """
        Returns a key for max depth reached.
        """
        if len(notation) == 1:
            return notation[0]
        if cls._dots:
            return f'{".".join(notation)}'
        return f'[{"][".join(notation)}]'


class QsParser:
    _args: dict[str | int, str | int | dict] = None
    _depth: int = 5
    _parameter_limit: int = 1000
    _allow_dots: bool = False
    _allow_sparse: bool = False
    _array_limit: int = 20
    _parse_arrays: bool = False
    _allow_empty: bool = False
    _comma: bool = False

    def __init__(
            self,
            args: list[str],
            depth: int,
            parameter_limit: int,
            allow_dots: bool,
            allow_sparse: bool,
            array_limit: int,
            parse_arrays: bool,
            allow_empty: bool,
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
        self._allow_empty = allow_empty
        self._comma = comma
        for arg in args:
            parse_func = self._parse_array if self._parse_arrays else self._parse_lhs
            k, v = arg.split('=')
            parse_func(k, v)

    @property
    def args(self) -> dict[str, str]:
        """
        Returns parsed arguments.
        """
        return self._args

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
        allow_empty: bool = False,
        comma: bool = False,
    ) -> dict:
        """
        Creates a parser from a url.
        """
        args = []
        parsed_url = up.urlparse(url)
        query_args = re.split(delimiter, parsed_url.query)
        for arg in query_args:
            args.append(cls._unq(arg))
        return cls(args, depth, parameter_limit, allow_dots, allow_sparse, array_limit, parse_arrays, allow_empty, comma).args

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

    def _parse_array(self, k: str, v: str):
        """
        Parses key with array notation into a list of nested keys.
        """
        if not self._parse_arrays:
            return False
        match = re.match(r'(\w+)(\[(.*)\])+', k)
        key = match.group(1)
        if not match:
            self._parse_arrays = False
        array_notation = re.findall(r'\[(.*?)\]', k)
        if re.match(r'[^\d]+', array_notation[0] if array_notation else ''):
            self._parse_arrays = False
        result, self._parse_arrays = self._set_index(self.args.get(key, {}), ArrayParse.process(array_notation, v))
        if key not in self._args:
            self._args[key] = result
        else:
            self._args[key] = self._update_arg(self._args[key], result)
        # post insertion check to verify array notation

    @staticmethod
    def _set_index(current: dict, incoming: dict) -> tuple[dict, bool]:
        """
        Sets index from None if unknown index is present
        also signals when object is no longer array
        """
        is_array = True
        if not current:
            max_index = -1
        try:
            max_index = max([int(key) for key in current] + [-1])
        except ValueError:
            # found non-numerical key
            max_index = max([key for key in current if key.isdigit()] + [-1])
            is_array = False
        if None in incoming:
            incoming[max_index+1] = incoming.pop(None)
        return incoming, is_array
    
    def _parse_lhs(self, k: str, v: str) -> bool:
        """
        Parses key with brackets notation into a list of nested keys.
        """
        pattern = r'(\w+)(\[(.*)\])*' if not self._allow_empty else r'(\w*)(\[(.*?)\])*'
        match = re.match(pattern, k)
        if not match:
            return False
        notation = re.findall(r'\[(.*?)\]', k)
        key = match.group(1)
        data = LHSParse.process(
            notation, v, depth=self._max_depth, allow_empty=self._allow_empty)
        try:
            if key not in self._args:
                self._args[key] = data
            else:
                self._args[key] = self._update_arg(self._args[key], data)
        except TypeError:
            return False
        return True

    @staticmethod
    def _process_types(arg: t.Any, val: t.Any) -> t.Any:
        """
        Handles type mismatch between arg and val.
        """
        # need to map typing to following:
        # arg: str and val: dict -> arg: {arg: True}
        # arg: dict and val: str -> val: {val: True}
        # arg: list and val: dict -> arg: {str(arg): True}
        # arg: dict and val: list -> val: {str(val): True}
        # arg: list and val: str -> val: [val]
        # arg: str and val: list -> arg: [arg]
        combination_map = {
            (str, dict): lambda x, y: ({x: True}, y),
            (dict, str): lambda x, y: (x, {y: True}),
            (list, dict): lambda x, y: ({str(x): True}, y),
            (dict, list): lambda x, y: (x, {str(y): True}),
            (list, str): lambda x, y: (x, [y]),
            (str, list): lambda x, y: ([x], y),
        }
        return combination_map.get((type(arg), type(val)), lambda x, y: (x, y))(arg, val)

    def _update_arg(self ,arg: t.Any, val: t.Any) -> t.Union[dict, list]:
        """
        Updates an existing argument recursively.
        This method is neccesarly in case of using multiple arguments with the same key nesting.
        """
        arg, val = QsParser._process_types(arg, val)
        if isinstance(arg, str):
            arg = [arg, val]
        elif isinstance(arg, dict):
            if all([isinstance(x, int) for x in arg.keys()]) and self._parse_arrays:
                val, self._parse_arrays = self._set_index(arg, val)
            for k, v in val.items():
                if k in arg:
                    arg[k] = self._update_arg(arg[k], v)
                else:
                    arg[k] = v
        else:
            arg.extend(val)
        return arg


if __name__ == '__main__':
    url = 'http://localhost:5000/?a[][]=b&a[][]=c'
    print(QsParser.parse(url, parse_arrays=True))
