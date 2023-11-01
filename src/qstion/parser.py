import typing as t
import urllib.parse as up
import re
from .base import QS, Unparsable, UnbalancedBrackets, QsNode, EmptyKey, ArrayLimitReached


t_Delimiter = t.Union[str, t.Pattern[str]]


class ArrayParse:
    _depth: int = 5
    _limit: int = 20

    @classmethod
    def process(cls, notation: list, val: str, depth: int = 5, max_limit: int = 20) -> QsNode:
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
    def process_notation(cls, notation: list[str], val: t.Any) -> QsNode:
        """
        Parses array notation recursively.

        Args:
            notation (list): list of remaining keys (in nested order)
            val (str): value to assign to the last key

        Returns:
            QsNode: tree like structure of parsed data

        Raises:
            ArrayLimitReached: if array limit is reached
        """
        if not notation:
            return val
        current = notation[0]
        if current.isdigit():
            if int(current) > cls._limit:
                raise ArrayLimitReached('Array limit reached')
            return QsNode(int(current), cls.process_notation(notation[1:], val))
        elif current == '':
            res = cls.process_notation(notation[1:], val)
            if not isinstance(res, QsNode):
                return QsNode(None, res)
            if not res.has_int_key() and res.key is not None:
                # initialization of array without index - set index None to be handled by parser
                return QsNode(None, res)
            return res
        else:
            return QsNode(current, cls.process_notation(notation[1:], val))


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
    ) -> QsNode:
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
    def process_notation(cls, notation: list[str], val: t.Any) -> QsNode:
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
            raise EmptyKey('Empty key not allowed')
        if cls._depth < 0:
            # join current and rest of notation
            current_key = cls._max_depth_key(notation)
            return QsNode(current_key, val)
        cls._depth -= 1
        return QsNode(current, cls.process_notation(notation[1:], val))

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
    _parse_primitive: bool = False

    def __init__(
            self,
            depth: int = 5,
            parameter_limit: int = 1000,
            allow_dots: bool = False,
            allow_sparse: bool = False,
            array_limit: int = 20,
            parse_arrays: bool = False,
            allow_empty: bool = False,
            comma: bool = False,
            parse_primitive: bool = False
    ):
        super().__init__(depth, parameter_limit, allow_dots,
                         allow_sparse, array_limit, parse_arrays, allow_empty, comma)
        self._parse_primitive = parse_primitive

    def parse(self, args: list[tuple]):
        for arg in args:
            parse_func = self._parse_array if self._parse_arrays else self._parse_lhs
            k, v = arg
            if self._comma:
                v = re.split(',', v)
                v = str(v[0]) if len(v) == 1 else v
            parse_func(k, v)

    @property
    def args(self) -> dict[str, str]:
        """
        Returns parsed arguments.
        """
        return {
            k.key: k.serialize() for k in self._qs_tree.values()
        }

    @staticmethod
    def _from_array_like(v: str | list) -> list | str:
        """
        Converts array-like string to list.

        Args:
            v (str): string to convert

        Returns:
            list: converted list
        """

        if isinstance(v, str) and (v.startswith('[') and v.endswith(']')):
            v = v.rstrip(']').lstrip('[')
            return v.split(',')
        return v

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
                raise UnbalancedBrackets(
                    'Using brackets as key is not allowed')
            if bracket == ']' and bracket_count == 0:
                raise UnbalancedBrackets('Unbalanced brackets')
            bracket_count += 1 if bracket == '[' else -1
        if bracket_count != 0:
            raise UnbalancedBrackets('Unbalanced brackets')
        if brackets and not k.endswith(']'):
            raise Unparsable('Nesting notation broken')

    def _parse_array(self, k: str, v: str | list) -> None:
        """
        Parses key with array notation into a list of nested keys.

        Args:
            k (str): key to parse
            v (str): value to assign to the key
        """
        v = self._process_primitive(v)
        notation = self._split_key(k)
        if notation is None:
            # continue as default lhs
            self._parse_arrays = False
            self._to_obj()
            return self._parse_lhs(k, v)
        if re.match(r'[^\d]+', notation[1]):
            self._parse_arrays = False
            self._to_obj()
            return self._parse_lhs(k, v)
        try:
            item = ArrayParse.process(notation, v)
            item.set_index(self._qs_tree.get(item.key, None),
                           array_limit=self._array_limit)
        except ArrayLimitReached:
            self._parse_arrays = False
            self._to_obj()
            return self._parse_lhs(k, v)
        if item.key not in self._qs_tree:
            if len(self._qs_tree) >= self._parameter_limit:
                return
            self._qs_tree[item.key] = item
        else:
            self._qs_tree[item.key].update(item)

    def _parse_lhs(self, k: str, v: str | list) -> None:
        """
        Parses key with brackets notation into a list of nested keys.

        Args:
            k (str): key to parse
            v (str): value to assign to the key
        """
        v = self._process_primitive(v)
        notation = self._split_key(k)
        if notation is None:
            raise Unparsable('Unable to parse key')
        data = LHSParse.process(
            notation, v, depth=self._max_depth, allow_empty=self._allow_empty)
        if data.key not in self._qs_tree:
            if len(self._qs_tree) >= self._parameter_limit:
                return
            self._qs_tree[data.key] = data
        else:
            self._qs_tree[data.key].update(data)

    def _process_primitive(self, v: str | list) -> t.Any:
        v = self._from_array_like(v)
        if not self._parse_primitive:
            return v
        if isinstance(v, list):
            return [self._process_primitive(item) for item in v]
        if v.isdigit():
            return int(v)
        # TODO: decide whether accept case insensitive booleans
        if v.lower() in ['true', 'false']:
            return v.lower() == 'true'
        # TODO: decide whether accept case insensitive nulls
        if v.lower() in ['null', 'none']:
            return None
        try:
            return float(v)
        except ValueError:
            return v

    def _split_key(self, k: str) -> list[str] | None:
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
            return [match.group(1)] + notation if match else None
        if self._allow_dots:
            match = re.match(
                r'(\w+)(\.\w+)+', k) if not self._allow_empty else re.match(r'(\w*)(\.(\w*))', k)
            notation = re.findall(
                r'\.(\w+)', k) if not self._allow_empty else re.findall(r'\.(\w*)', k)
            if match:
                return [match.group(1)] + notation
        QsParser._check_brackets(k)
        match_pattern = r'^(\w+)(\[\w+\])*$' if not self._allow_empty else r'^(\w*)(\[\w*\])*$'
        match = re.match(match_pattern, k)
        notation = re.findall(
            r'\[(\w+)\]', k) if not self._allow_empty else re.findall(r'\[(\w*)\]', k)
        return [match.group(1)] + notation if match else None

    def _to_obj(self) -> None:
        """
        Transforms array-like dictionary into object-like dictionary, recursively.

        Args:
            arg (dict): dictionary to transform

        Returns:    
            dict: transformed dictionary
        """
        for v in self._qs_tree.values():
            v.to_object_notation()


def parse(
        data: str,
        from_url: bool = False,
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
        parse_primitive: bool = False,
        comma: bool = False):
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
        qs = up.urlparse(data).query
    else:
        qs = data
    args = []
    try:
        query_args = re.split(delimiter, qs)
        for arg in query_args:
            args.append(QsParser._unq(
                arg, charset, interpret_numeric_entities))
        parser = QsParser(depth, parameter_limit, allow_dots,
                          allow_sparse, array_limit, parse_arrays, allow_empty, comma, parse_primitive)
        parser.parse(args)
        return parser.args
    except (Unparsable, UnbalancedBrackets):
        return up.parse_qs(
            qs,
            keep_blank_values=allow_empty,
            max_num_fields=parameter_limit,
            separator=delimiter)


if __name__ == "__main__":
    item = parse('a=[b,c]')
