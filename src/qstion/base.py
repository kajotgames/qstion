import typing as t
from html import unescape as unescape_html
import urllib.parse as up


class Unparsable(Exception):
    """Exception raised when query string cannot be parsed with QsParser"""
    pass


class ArrayLimitReached(Exception):
    """Exception raised when array limit is reached while parsing query string"""
    pass


class UnbalancedBrackets(Exception):
    """Exception raised when query string contains unbalanced brackets"""
    pass


class EmptyKey(Exception):
    """Exception raised when query string contains empty key and is not allowed"""
    pass


class QsNode:
    """
    Data structure to represent a query string as a tree for better manipulation of arrays and objects
    """
    key: str | int
    children: list['QsNode']
    value: t.Any

    def __init__(self, key: str | int, value: t.Any):
        self.key = key
        self.children = []
        if isinstance(value, type(self)):
            self.children = [value]
            self.value = None
        else:
            self.value = value
            self.children = []

    @classmethod
    def load(
        cls,
        parent_key: str | int,
        data: t.Any,
        filter: list = None
    ) -> 'QsNode':
        """
        Load a dictionary into a QsNode recursively

        Args:
            parent_key (str): parent key to be used as key for root node
            data (dict): dictionary to load
            filter (list): list of keys to filter - if key is not in filter, it will be ignored

        Returns:
            QsNode: current node
        """
        root = cls(parent_key, None)
        if filter and parent_key not in filter:
            return None
        if isinstance(data, dict):
            for k, v in data.items():
                child = cls.load(k, v, filter=filter)
                if child is not None:
                    root.children.append(child)
        elif isinstance(data, list):
            # list of dictionaries, indexed
            for i, v in enumerate(data):
                child = cls.load(i, v, filter=filter)
                if child is not None:
                    root.children.append(child)
        else:
            root.value = data
        return root

    def __getitem__(self, key: str):
        """
        Overload [] operator to get child by key
        """
        for child in self.children:
            if child.key == key:
                return child
        raise KeyError(key)

    def get(self, key: str, default: t.Any = None):
        """
        Method to get child by key with default value - behaves like dict.get
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str):
        """
        Overload in operator to check if child exists
        """
        for child in self.children:
            if child.key == key:
                return True
        return False

    def is_leaf(self):
        """
        Check if node is a leaf - has no children
        """
        return self.children is None or len(self.children) == 0

    def has_int_key(self):
        """
        Check if node has an integer key - used to determine whether node might be an array item
        """
        return isinstance(self.key, int)

    def is_array(self):
        """
        Check if node is an array - all children have integer keys - values might be nested
        """
        if self.value is None and all([child.has_int_key() for child in self.children]):
            return True

    def is_default_array(self):
        """
        Check if node is a default array - all children have integer keys and are leafs
        """
        if self.is_array() and all([child.is_leaf() for child in self.children]):
            return True

    def max_index(self) -> int:
        """
        Used to determine the next index for a new array item
        """
        # method is only called within _parse_array method but this is security measure
        return max([child.key for child in self.children]) if self.is_array() else -1

    def to_object_notation(self):
        """
        Transform self from possible array notation to default object notation - all integer indexes are replaced with 
        their string representation
        """
        if isinstance(self.key, int):
            self.key = str(self.key)
        for child in self.children:
            child.to_object_notation()

    def reorder(self):
        """
        Used to reorder children of a node - sorts them by key
        Only works if node is considered an array
        """
        if self.is_array():
            self.children.sort(key=lambda x: x.key)
            for child in self.children:
                child.reorder()

    def update(self, other: 'QsNode'):
        """
        Recursively update self with other node

        Args:
            other (QsNode): node to update self with

        Returns:
            None
        """
        if self.is_leaf() and other.is_leaf():
            self.merge_value(other)
        elif self.is_leaf() and not other.is_leaf():
            self.children = [QsNode(str(self.value), True)]
            self.value = None
            for child in other.children:
                if child.key in self:
                    self[child.key].update(child)
                else:
                    self.children.append(child)
            self.reorder()
        elif not self.is_leaf() and other.is_leaf():
            self.children.append(QsNode(other.value, True))
            self.reorder()
        else:
            for child in other.children:
                if child.key in self:
                    self[child.key].update(child)
                else:
                    self.children.append(child)
            self.reorder()

    def merge_value(self, other: 'QsNode'):
        """
        Merge values of two nodes

        Args:
            other (QsNode): node to merge value with

        Returns:
            None
        """
        if not isinstance(self.value, list):
            self.value = [self.value]
        if not isinstance(other.value, list):
            other.value = [other.value]
        self.value.extend(other.value)

    def serialize(self):
        """
        Represent self as a dictionary
        """
        if self.is_leaf():
            return self.value
        return {child.key: child.serialize() for child in self.children}

    def set_index(self, base: 'QsNode', array_limit: int = 20):
        """
        Set index of self and children recursively
        If base is provided, it is used to match children by key
        If array_limit is reached, ArrayLimitReached exception is raised

        Args:
            base (QsNode): base node to match children by key
            array_limit (int): array limit

        Returns:
            None
        """
        for child in self.children:
            match = base.get(child.key, None) if base else None
            child.set_index(match, array_limit=array_limit)
        for child in self.children:
            if child.key is None:
                child.key = base.max_index() + 1 if base else 0
            if child.has_int_key() and child.key > array_limit:
                raise ArrayLimitReached('Array limit reached')

    def is_empty(self):
        """
        Check if node is empty - has no value and no children
        """
        return self.is_leaf() and self.value is None


class QS:
    """
    Base class for query string parser and stringifier
    """
    _qs_tree: dict[str, QsNode]

    _depth: int = 5
    _depth: int = 5
    _parameter_limit: int = 1000
    _allow_dots: bool = False
    _array_limit: int = 20
    _parse_arrays: bool = False
    _allow_empty: bool = False
    _comma: bool = False

    def __init__(
            self,
            depth: int = 5,
            parameter_limit: int = 1000,
            allow_dots: bool = False,
            array_limit: int = 20,
            parse_arrays: bool = False,
            allow_empty: bool = False,
            comma: bool = False,
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
        self._qs_tree = {}
        self._max_depth = depth
        self._parameter_limit = parameter_limit
        self._allow_dots = allow_dots
        self._array_limit = array_limit
        self._parse_arrays = parse_arrays
        self._allow_empty = allow_empty
        self._comma = comma

    @staticmethod
    def _unq(arg: str, charset: str = 'utf-8', interpret_numeric_entities: bool = False) -> str:
        """
        Unquotes a string (removes url encoding).

        Args:
            arg (str): string to unquote
            charset (str): charset to use for unquoting
            interpret_numeric_entities (bool): interpret numeric entities in unicode

        Returns:
            str: unquoted string
        """
        try:
            arg_key, arg_val = arg.split('=')
        except ValueError:
            raise Unparsable('Unable to parse key')
        if interpret_numeric_entities:
            return (unescape_html(up.unquote(arg_key, charset)), unescape_html(up.unquote(arg_val, charset)))
        return (up.unquote(arg_key, charset), up.unquote(arg_val, charset))

    @staticmethod
    def _q(key: str, value: str, charset: str = 'utf-8') -> str:
        """
        Encodes a string (url encoding).

        Args:
            key (str): key to encode
            value (str): value to encode
            charset (str): charset to use for encoding

        Returns:
            str: encoded string
        """
        return f'{up.quote(key, encoding=charset, errors="xmlcharrefreplace")}={up.quote(value, encoding=charset, errors="xmlcharrefreplace")}'
