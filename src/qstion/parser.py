import typing as t
import urllib.parse as up
from html import unescape as unescape_html
import re
from .base import QS
from . import errors as e

t_Delimiter = t.Union[str, t.Pattern[str]]


class ArrayParse:
    _depth: int = 5
    _limit: int = 20

    @classmethod
    def process(cls, notation: list, val: str, depth: int = 5, max_limit: int = 20) -> dict:
        """
        Parses array notation for single key-value pair.

        Args:
            notation (list): list of keys (in nested order)
            val (str): value to assign to the last key
            depth (int): max depth of nested objects
            max_limit (int): max number of elements in array

        Returns:
            list: parsed item into dictionary
        """
        cls._limit = max_limit
        cls._depth = depth
        return cls.process_notation(notation, val)

    @classmethod
    def process_notation(cls, notation: list[str], val: t.Any) -> dict:
        """
        Parses array notation recursively.

        Args:
            notation (list): list of remaining keys (in nested order)
            val (str): value to assign to the last key

        Returns:
            dict: parsed sub-dictionary

        Raises:
            ArrayLimitReached: if array limit is reached
        """
        if not notation:
            return val
        current = notation[0]
        if current.isdigit():
            if int(current) > cls._limit:
                raise e.ArrayLimitReached('Array limit reached')
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
        Parses left hand side notation for single key-value pair.

        Args:
            notation (list): list of keys (in nested order)
            val (str): value to assign to the last key
            depth (int): max depth of nested objects
            allow_empty (bool): allow empty keys
            allow_dots (bool): allow dot notation
        """
        cls._depth = depth
        cls._allow_empty = allow_empty
        cls._dots = allow_dots
        return cls.process_notation(notation, val)

    @classmethod
    def process_notation(cls, notation: list[str], val: t.Any) -> dict:
        """
        Parses left hand side notation recursively.

        Args:
            notation (list): list of remaining keys (in nested order)
            val (str): value to assign to the last key

        Returns:
            dict: parsed sub-dictionary

        Raises:
            EmptyKey: if empty key is found and not allowed
        """
        if not notation:
            return val
        current = notation[0]
        if current == '' and not cls._allow_empty:
            raise e.EmptyKey('Empty key not allowed')
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

        Args:
            notation (list): list of remaining keys (in nested order)

        Returns:
            str: key for max depth reached
        """
        if len(notation) == 1:
            return notation[0]
        if cls._dots:
            return f'{".".join(notation)}'
        return f'[{"][".join(notation)}]'


class QsParser(QS):
    _args: dict[str | int, str | int | dict] = None

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
        Handler for parsing query string into JS-object-like dictionary.
        """
        super().__init__(
            depth,
            parameter_limit,
            allow_dots,
            allow_sparse,
            array_limit,
            parse_arrays,
            allow_empty,
            comma,
        )
        self._args = {}
        for arg in args:
            parse_func = self._parse_array if self._parse_arrays else self._parse_lhs
            k, v = arg.split('=')
            if self._comma:
                v = re.split(',', v)
                v = str(v[0]) if len(v) == 1 else v
            parse_func(k, v)

    @property
    def args(self) -> dict[str, str]:
        """
        Returns parsed arguments.
        """
        return self._args

    @classmethod
    def from_url(
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
        charset: str = 'utf-8',
        interpret_numeric_entities: bool = False,
        comma: bool = False,
    ) -> dict:
        """
        Creates a parser from a url.

        Args:
            url (str): url to parse
            delimiter (str): delimiter for query arguments
            depth (int): max depth of nested objects
            parameter_limit (int): max number of parameters to parse (in keyword count)
            allow_dots (bool): allow dot notation
            allow_sparse (bool): allow sparse arrays
            array_limit (int): max number of elements in array
            parse_arrays (bool): parse array values as or keep object notation
            allow_empty (bool): allow empty keys
            charset (str): charset for url encoding
            interpret_numeric_entities (bool): interpret numeric entities
            comma (bool): allow comma separated values

        Returns:
            dict: parsed data
        """
        qs = up.urlparse(url).query
        return cls.parse(
            qs,
            delimiter,
            depth,
            parameter_limit,
            allow_dots,
            allow_sparse,
            array_limit,
            parse_arrays,
            allow_empty,
            charset,
            interpret_numeric_entities,
            comma,
        )

    @classmethod
    def parse(
        cls,
        qs: str,
        delimiter: t_Delimiter = '&',
        depth: int = 5,
        parameter_limit: int = 1000,
        allow_dots: bool = False,
        allow_sparse: bool = False,
        array_limit: int = 20,
        parse_arrays: bool = False,
        allow_empty: bool = False,
        charset: str = 'utf-8',
        interpret_numeric_entities: bool = False,
        comma: bool = False,
    ) -> dict:
        """
        Parses url query string into JS-object-like dictionary.

        Args:
            qs (str): query string to parse
            delimiter (str): delimiter for query arguments
            depth (int): max depth of nested objects
            parameter_limit (int): max number of parameters to parse (in keyword count)
            allow_dots (bool): allow dot notation
            allow_sparse (bool): allow sparse arrays
            array_limit (int): max number of elements in array
            parse_arrays (bool): parse array values as or keep object notation
            allow_empty (bool): allow empty keys
            charset (str): charset for url encoding
            interpret_numeric_entities (bool): interpret numeric entities
            comma (bool): allow comma separated values

        Returns:
            dict: parsed data
        """
        args = []
        try:
            query_args = re.split(delimiter, qs)
            for arg in query_args:
                args.append(cls._unq(arg, charset, interpret_numeric_entities))
            return cls(args, depth, parameter_limit, allow_dots, allow_sparse, array_limit, parse_arrays, allow_empty, comma).args
        except (e.Unparsable, e.UnbalancedBrackets):
            return up.parse_qs(
                qs,
                keep_blank_values=allow_empty,
                max_num_fields=parameter_limit,
                separator=delimiter)

    @staticmethod
    def _unq(arg: str, charset: str = 'utf-8', interpret_numeric_entities: bool = False) -> str:
        """
        Unquotes a string (removes url encoding).

        Args:
            arg (str): string to unquote

        Returns:
            str: unquoted string
        """
        try:
            arg_key, arg_val = arg.split('=')
        except ValueError:
            raise e.Unparsable('Unable to parse key')
        if interpret_numeric_entities:
            return f'{unescape_html(up.unquote(arg_key, charset))}={unescape_html(up.unquote(arg_val, charset))}'
        return f'{up.unquote(arg_key, charset)}={up.unquote(arg_val, charset)}'

    def _split_key(self, k: str) -> tuple[str, list[str]] | tuple[None, None]:
        """
        Splits key into a main key and a list of nested keys.

        Args:
            k (str): key to split

        Returns:
            tuple[str, list[str]]: main key and list of nested keys or None, None if key is not parsable with current settings
        """
        if self._parse_arrays:
            QsParser._check_brackets(k)
            match_pattern = r'(\w+)(\[(.*)\])+' if not self._allow_empty else r'(\w*)(\[(.*)\])+'
            match = re.match(match_pattern, k)
            notation = re.findall(r'\[(.*?)\]', k)
            return (match.group(1), notation) if match else (None, None)
        if self._allow_dots:
            match = re.match(
                r'(\w+)(\.\w+)+', k) if not self._allow_empty else re.match(r'(\w*)(\.(\w*))', k)
            notation = re.findall(
                r'\.(\w+)', k) if not self._allow_empty else re.findall(r'\.(\w*)', k)
            if match:
                return match.group(1), notation
        QsParser._check_brackets(k)
        match_pattern = r'^(\w+)(\[\w+\])*$' if not self._allow_empty else r'^(\w*)(\[\w*\])*$'
        match = re.match(match_pattern, k)
        notation = re.findall(
            r'\[(\w+)\]', k) if not self._allow_empty else re.findall(r'\[(\w*)\]', k)
        return (match.group(1), notation) if match else (None, None)

    @staticmethod
    def _check_brackets(k: str) -> None:
        """
        Checks if brackets are balanced.

        Args:
            k (str): key to check

        Raises:
            UnbalancedBrackets: if brackets are unbalanced
            Unparsable: if nesting notation is broken
        """
        brackets = [char for char in k if char in '[]']
        # check if brackets are balanced
        bracket_count = 0
        for bracket in brackets:
            if bracket == '[' and bracket_count > 0:
                raise e.UnbalancedBrackets(
                    'Using brackets as key is not allowed')
            if bracket == ']' and bracket_count == 0:
                raise e.UnbalancedBrackets('Unbalanced brackets')
            bracket_count += 1 if bracket == '[' else -1
        if bracket_count != 0:
            raise e.UnbalancedBrackets('Unbalanced brackets')
        if brackets and not k.endswith(']'):
            raise e.Unparsable('Nesting notation broken')

    def _parse_array(self, k: str, v: str | list) -> None:
        """
        Parses key with array notation into a list of nested keys.

        Args:
            k (str): key to parse
            v (str): value to assign to the key
        """
        key, notation = self._split_key(k)
        if key is None:
            # continue as default lhs
            self._parse_arrays = False
            self._args = QsParser.transform_to_object(self._args)
            return self._parse_lhs(k, v)
        if not notation or re.match(r'[^\d]+', notation[0]):
            self._parse_arrays = False
            self._args = QsParser.transform_to_object(self._args)
            return self._parse_lhs(k, v)
        try:
            result, self._parse_arrays = self._set_index(
                self.args.get(key, {}), ArrayParse.process(notation, v))
            if any([key > self._array_limit for key in result.keys()]):
                raise e.ArrayLimitReached('Array limit reached')
        except e.ArrayLimitReached:
            self._parse_arrays = False
            self._args = QsParser.transform_to_object(self._args)
            return self._parse_lhs(k, v)
        if key not in self._args:
            if len(self._args) >= self._parameter_limit:
                return
            self._args[key] = result
        else:
            self._args[key] = self._update_arg(self._args[key], result)

    def _parse_lhs(self, k: str, v: str | list) -> None:
        """
        Parses key with brackets notation into a list of nested keys.

        Args:
            k (str): key to parse
            v (str): value to assign to the key
        """
        key, notation = self._split_key(k)
        if key is None:
            raise e.Unparsable('Unable to parse key')
        data = LHSParse.process(
            notation, v, depth=self._max_depth, allow_empty=self._allow_empty)
        if key not in self._args:
            if len(self._args) >= self._parameter_limit:
                return
            self._args[key] = data
        else:
            self._args[key] = self._update_arg(self._args[key], data)

    @staticmethod
    def transform_to_object(arg: dict) -> dict:
        """
        Transforms array-like dictionary into object-like dictionary, recursively.

        Args:
            arg (dict): dictionary to transform

        Returns:    
            dict: transformed dictionary
        """
        fixed = {}
        for arg_key in arg:
            replaced_key = arg_key
            if isinstance(arg_key, int):
                replaced_key = str(arg_key)
                fixed[replaced_key] = arg[arg_key]
            else:
                fixed[replaced_key] = arg[arg_key]
            if isinstance(arg[arg_key], dict):
                fixed[replaced_key] = QsParser.transform_to_object(
                    arg[arg_key])
        return fixed

    @staticmethod
    def _set_index(current: dict, incoming: dict) -> tuple[dict, bool]:
        """
        Sets index from None if unknown index is present.
        also signals when object is no longer array

        Args:
            current (dict): current dictionary
            incoming (dict): incoming dictionary
        """
        is_array = True
        if not current:
            max_index = -1
        try:
            max_index = max([int(key) for key in current] + [-1])
        except ValueError:
            # found non-numerical key
            max_index = max(
                [key for key in current if str(key).isdigit()] + [-1])
            is_array = False
        if None in incoming:
            incoming[max_index+1] = incoming.pop(None)
        return incoming, is_array

    @staticmethod
    def _process_types(arg: t.Any, val: t.Any) -> tuple[t.Any, t.Any]:
        """
        Handles type mismatch between arg and val.

        Args:
            arg (any): argument
            val (any): value to assign to the argument

        Returns:
            tuple[any, any]: processed argument and value
        """
        combination_map = {
            (str, dict): lambda x, y: ({x: True}, y),
            (dict, str): lambda x, y: (x, {y: True}),
            (list, dict): lambda x, y: ({str(x): True}, y),
            (dict, list): lambda x, y: (x, {str(y): True}),
            (list, str): lambda x, y: (x, [y]),
            (str, list): lambda x, y: ([x], y),
        }
        return combination_map.get((type(arg), type(val)), lambda x, y: (x, y))(arg, val)

    def _update_arg(self, arg: t.Any, val: t.Any) -> t.Union[dict, list]:
        """
        Updates an existing argument recursively.
        This method is neccesarly in case of using multiple arguments with the same key nesting.

        Args:
            arg (any): argument
            val (any): value to assign to the argument

        Returns:
            any: updated argument
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


def parse(data: str, from_url: bool = False, **kw):
    """
    Parses a string into a dictionary.

    Args:
        data (str): string to parse
        from_url (bool): if True, parses url
        **kw: keyword arguments for QsParser

    Returns:
        dict: parsed data
    """
    if from_url:
        return QsParser.from_url(data, **kw)
    return QsParser.parse(data, **kw)
