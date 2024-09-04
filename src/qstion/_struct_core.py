import typing as t
from enum import Enum
import urllib.parse as up
from html import escape as escape_html

t_Delimiter = t.Union[str, t.Pattern[str]]


class NoValue:
    """
    Placeholder for missing values
    """

    def __str__(self) -> str:
        return "NoValue"

    def __repr__(self) -> str:
        return "NoValue"


class EnumDuplicateKeys(Enum):
    """
    Enum for duplicate keys handling
    """

    COMBINE = "combine"
    FIRST = "first"
    LAST = "last"


class QsNode:
    """
    Data structure to represent a query string as a tree for better manipulation of arrays and objects
    """

    auto_set_key: bool = False

    key: int | str | tuple
    value: t.Any | list["QsNode"]

    def __init__(self, key: str | int, value: t.Any, auto_set_key: bool = False):
        self.key = key
        self.value = value
        self.auto_set_key = auto_set_key

    @classmethod
    def load_from_dict(
        cls,
        item_key: int | str | tuple,
        item_value: t.Any,
        parse_array: bool = False,
        allow_empty: bool = False,
        auto_set_key: bool = False,
    ) -> "QsNode":
        """
        Load data (recursively) from dictionary into QSNode

        Args:
            data (dict): dictionary to load

        Returns:
            QSNode: QSNode instance
        """
        parsed_value = None
        # If item_value is a dictionary, means it's nested, or array with unknown indexes
        if isinstance(item_value, dict):
            parsed_value = []
            for key, value in item_value.items():
                new_node = cls.load_from_dict(key, value, allow_empty=allow_empty, parse_array=parse_array)
                if new_node is not None:
                    parsed_value.append(new_node)
            if not parsed_value and not allow_empty:
                raise ValueError("Empty objects are not allowed")
        # If item_value is a list, means it's an array - process as array-like-dictionary
        elif isinstance(item_value, list):
            parsed_value = [
                (
                    cls(idx, value, auto_set_key=True)
                    if not isinstance(value, (dict, list))
                    else cls.load_from_dict(
                        idx, value, parse_array=parse_array, allow_empty=allow_empty, auto_set_key=True
                    )
                )
                for idx, value in enumerate(item_value)
            ]
        else:
            if item_value is NoValue:
                return
            parsed_value = item_value
        if parse_array and item_key == "":
            return cls(0, parsed_value, auto_set_key=True)
        return cls(item_key, parsed_value, auto_set_key=auto_set_key)

    def __contains__(self, key: str | tuple) -> bool:
        """
        Check if key is present in children
        """
        if self.is_leaf:
            return False
        for child in self.value:
            if child.key == key:
                return True
        return False

    def __getitem__(self, key: str | tuple, default: t.Any = None) -> "QsNode":
        """
        Get child node by key
        """
        if self.is_leaf:
            return default
        for child in self.value:
            if child.key == key:
                return child
        return default

    def update(
        self, value: t.Any | list["QsNode"], handle_duplicate_keys: EnumDuplicateKeys = EnumDuplicateKeys.COMBINE
    ) -> None:
        """
        Update (recursively) value of current or nested node
        """
        if self.value is NoValue:
            self.value = value
            return
        if value is NoValue:
            return
        if handle_duplicate_keys == EnumDuplicateKeys.FIRST:
            return
        elif handle_duplicate_keys == EnumDuplicateKeys.LAST:
            self.value = value
            return
        else:
            # combining
            if self.is_leaf:
                self.update_leaf_case(value)
            elif self.is_array_branch:
                self.update_array_branch_case(value)
            elif self.is_object_branch:
                self.update_object_branch_case(value)
            else:
                # safety net, should never happen
                raise ValueError("Invalid node type")

    def update_leaf_case(self, value: t.Any | list["QsNode"]) -> None:
        """
        Update node if self is leaf node
        Using following behavioral expectation:
        {k: v} + {k: x} = {k: {0: v, 1: x}}
        {k: v} + {k: [x, y]} = {k: {0: v, 1: x, 2: y}}
        {k: v} + {k: {x: y}} = {k: {v: True, x: y}}
        Special case:
        {k: v} + {k: {v: w}} = {k: {v: w}}
        """
        if isinstance(value, list):
            # Scenario 2 or 3
            if all(v.is_array_node for v in value):
                # reindex incoming +1
                [v.reindex(shift=v.key + 1) for v in value]
                self.value = [QsNode(0, self.value), *value]
            else:
                # Scenario 3
                # Special case check
                if self.value in [v.key for v in value]:
                    self.value = value
                else:
                    self.value = [QsNode(self.value, True), *value]
        else:
            # Scenario 1 - based on self
            self.value = [QsNode(0, self.value), QsNode(1, value)]

    def update_array_branch_case(self, value: t.Any | list["QsNode"]) -> None:
        """
        Update node if self is array-branched node
        Using following behavioral expectation:
        {k: [v, w]} + {k: x} = {k: {0: v, 1: w, 2: x}}
        {k: [v, w]} + {k: [x, y]} = {k: {0: v, 1: w, 2: x, 3: y}}
        {k: [v, w]} + {k: {x: y}} = {k: {str(v_index): v, str(w_index): w, x: y}}
        """
        if isinstance(value, list):
            # Scenario 2
            if all(v.is_array_node for v in value):
                # reindex incoming + next index available
                for v in value:
                    if v.auto_set_key:
                        v.reindex(shift=self.value[-1].key + 1)
                    if v.key in [v.key for v in self.value]:
                        targeted_node = self[v.key]
                        targeted_node.update(v.value)
                    else:
                        self.value.append(v)

            else:
                # Scenario 3
                for child in self.value:
                    child.convert_to_object_type()
                for incoming_node in value:
                    if incoming_node.key in [v.key for v in self.value]:
                        targeted_node = self[incoming_node.key]
                        targeted_node.update(incoming_node.value)
                    else:
                        self.value.append(incoming_node)

        else:
            # Scenario 1 - append with next index available
            self.value.append(QsNode((int(self.value[-1].key) + 1), value))

    def update_object_branch_case(self, value: t.Any | list["QsNode"]) -> None:
        """
        Update node if self is object-branched node
        Using following behavioral expectation:
        {k: {v: w}} + {k: x} = {k: {v: w, x: True}}
        {k: {v: w}} + {k: [x, y]} = {k: {v: w, str(x_index): x, str(y_index): y}}
        {k: {v: w}} + {k: {x: y}} = {k: {v: w, x: y}}
        """
        if isinstance(value, list):
            if all(v.is_array_node for v in value):
                # Scenario 2
                for inc_v in value:
                    inc_v.convert_to_object_type()
                    if inc_v.key in [v.key for v in self.value]:
                        targeted_node = self[inc_v.key]
                        targeted_node.update(inc_v.value)
                    else:
                        self.value.append(inc_v)
            else:
                # Scenario 3
                for child in value:
                    if child.key in [v.key for v in self.value]:
                        targeted_node = self[child.key]
                        targeted_node.update(child.value)
                    else:
                        self.value.append(child)
        else:
            # Scenario 1
            if value in [v.key for v in self.value]:
                targeted_node = self[value]
                targeted_node.value = True
            else:
                self.value.append(QsNode(value, True))

    def reindex(self, shift: int = 0) -> None:
        """
        Reindex self if self is array node
        """
        if self.is_array_node:
            self.key += shift

    def convert_to_object_type(self) -> None:
        """
        Convert self to object type
        """
        if self.is_array_node:
            self.key = str(self.key)

    @property
    def is_leaf(self) -> bool:
        """
        Check if node is a leaf node
        """
        return not isinstance(self.value, list)

    @property
    def is_array_branch(self) -> bool:
        """
        Check if node is an array-branched node
        """
        if self.is_leaf:
            return False
        for child in self.value:
            # key is always string or tuple
            if not child.is_array_node:
                return False
        return True

    @property
    def is_simple_array_branch(self) -> bool:
        """
        Check if node is a simple array-branched node (it's values are not nested nodes and it's not a sparse array)
        """
        if self.is_array_branch and not self.is_sparse_array:
            for child in self.value:
                if isinstance(child.value, list):
                    return False
            return True
        return False

    @property
    def is_object_branch(self) -> bool:
        """
        Check if node is an object-branched node
        """
        if self.is_leaf:
            return False
        if not self.is_array_branch:
            return True
        return False

    @property
    def is_array_node(self) -> bool:
        """
        Check if node is an array leaf node
        """
        if isinstance(self.key, int):
            return True
        return False

    @property
    def is_sparse_array(self) -> bool:
        """
        Check if node is a sparse array
        """
        if self.is_array_branch:
            for idx, child in enumerate(sorted(self.value, key=lambda x: x.key)):
                if child.key != idx:
                    return True
        return False

    @property
    def is_empty_node(self) -> bool:
        """
        Check if node is empty
        """
        if self.value is NoValue or self.value == []:
            return True
        return False

    def _repr(self, level: int = 0) -> str:
        """
        Provide a nice formatted representation of the tree
        """
        level_dashes = "-" * level
        if self.is_leaf:
            return f"|{level_dashes} Leaf: ({type(self.key)}){self.key} -> {self.value}"
        else:
            formatted_string = f"|{level_dashes} Branch: {self.key}\n"
            for child in self.value:
                formatted_string += f"{child._repr(level=level + 1)}\n"
            return formatted_string

    def to_dict(self) -> dict:
        """
        Convert QsNode to dictionary
        """
        if self.is_leaf:
            return self.value
        if self.is_array_branch and not self.is_sparse_array:
            # return them in correct order
            return [child.to_dict() for child in sorted(self.value, key=lambda x: x.key)]
        return {child.key: child.to_dict() for child in self.value}

    def _preorder_traversal(self) -> t.Generator["QsNode", None, None]:
        """
        Preorder traversal of the tree
        """
        yield self
        if not self.is_leaf:
            for child in self.value:
                yield from child._preorder_traversal()

    def _postorder_traversal(self) -> t.Generator["QsNode", None, None]:
        """
        Postorder traversal of the tree
        """
        if not self.is_leaf:
            for child in self.value:
                yield from child._postorder_traversal()
        yield self


class QsRoot:
    """
    Base class for query string parser and stringifier - preserves order of children
    """

    parameter_limit: int = 1000
    children: list[QsNode]

    def __init__(self, parameter_limit: int = 1000):
        self.children = []
        self.parameter_limit = parameter_limit

    def add_child(self, node: QsNode, duplicate_keys: EnumDuplicateKeys = EnumDuplicateKeys.COMBINE) -> None:
        """
        Add child node to root
        """
        if node is None:
            return
        if node.key in self:
            self[node.key].update(node.value, handle_duplicate_keys=duplicate_keys)
        else:
            if self.parameter_limit is not None and len(self.children) >= self.parameter_limit:
                return
            self.children.append(node)

    def __contains__(self, key: str) -> bool:
        """
        Check if key is present in children
        """
        for child in self.children:
            if child.key == key:
                return True
        return False

    def __getitem__(self, key: str, default: t.Any = None) -> QsNode:
        """
        Get child node by key
        """
        for child in self.children:
            if child.key == key:
                return child
        return default

    def _repr(self):
        """
        Provide a nice formatted representation of the tree
        """
        formatted_string = "Root:\n"
        for child in self.children:
            formatted_string += f"{child._repr(level=1)}\n"
        return formatted_string

    def to_dict(self) -> dict:
        """
        Convert QSRoot to dictionary
        """
        return {child.key: child.to_dict() for child in self.children}

    def _preorder_traversal(self) -> t.Generator[QsNode, None, None]:
        """
        Preorder traversal of the tree
        """
        for child in self.children:
            yield from child._preorder_traversal()

    def _postorder_traversal(self) -> t.Generator[QsNode, None, None]:
        """
        Postorder traversal of the tree
        """
        for child in self.children:
            yield from child._postorder_traversal()

    def process_array_limts(self, limit: int = None):
        """
        Process array limits
        """
        for node in self._preorder_traversal():
            if node.is_array_branch:
                # since indexing starts from 0, we need to check if max index is greater or equal to limit
                if not node.is_empty_node and limit is not None and max([child.key for child in node.value]) >= limit:
                    [child.convert_to_object_type() for child in node.value]

    @property
    def has_sparse_arrays(self) -> bool:
        """
        Check if root has sparse arrays
        """
        for node in self._preorder_traversal():
            if node.is_sparse_array:
                return True
        return False

    @property
    def is_empty(self) -> bool:
        """
        Check if root is empty
        """
        return self.children == []
