from ._qs_core import QSCore
from ._struct_core import QsNode, QsRoot, t_Delimiter, NoValue
from ._exc import UnknownInputType, Unparsable, ConfigurationError

import enum
import urllib.parse as up
from copy import deepcopy


class NestedArgument:
    keys: list[str]
    value: str | NoValue

    def __init__(self):
        self.keys = []
        self.value = None

    def append_key(self, key: str):
        self.keys.append(key)

    def set_value(self, value: str):
        self.value = value

    def stringify(
        self,
        charset: str = "utf-8",
        allow_dots: bool = False,
        encode_dot_in_keys: bool = False,
        encode: bool = False,
        encode_values_only: bool = False,
    ) -> str:
        # sanitize keys to be strings
        self.keys = [str(key) for key in self.keys]
        key: str = None
        value: str | NoValue = None
        if encode_dot_in_keys:
            self.keys = [key.replace(".", "%2E") for key in self.keys]
        if allow_dots:
            key = ".".join(self.keys)
        else:
            if len(self.keys) > 1:
                key = f"{self.keys[0]}[{']['.join(self.keys[1:])}]"
            else:
                key = self.keys[0]
        if encode:
            key = f"{up.quote(key, encoding=charset, errors='xmlcharrefreplace')}"
            value = (
                f"{up.quote(self.value, encoding=charset, errors='xmlcharrefreplace')}"
                if self.value is not NoValue
                else self.value
            )
        elif encode_values_only:
            value = (
                f"{up.quote(self.value, encoding=charset, errors='xmlcharrefreplace')}"
                if self.value is not NoValue
                else self.value
            )
        else:
            value = self.value if self.value is not None else "null"
        if value is NoValue:
            return key
        else:
            return f"{key}={value}"

    def create_copy(self):
        return deepcopy(self)


class ArrayFormat(enum.Enum):
    INDICES = "indices"
    BRACKETS = "brackets"
    REPEAT = "repeat"
    COMMA = "comma"


class QsStringifier(QSCore):
    array_format: ArrayFormat
    encode: bool = True
    encode_dot_in_keys: bool = False
    encode_values_only: bool = False
    allow_empty_arrays: bool = False

    def __init__(
        self,
        charset: str = "utf-8",
        delimiter: t_Delimiter = "&",
        allow_dots: bool = False,
        encode_dot_in_keys: bool = False,
        charset_sentinel: bool = False,
        allow_empty_arrays: bool = False,
        encode: bool = True,
        encode_values_only: bool = False,
        array_format: str = "indices",
    ):
        """
        Constructor for the QsStringifier class.

        Args:
            charset (str, optional): The charset to use for encoding and decoding. Defaults to "utf-8".
            delimiter (t_Delimiter, optional): The delimiter to use for separating key-value pairs. Defaults to "&".
            allow_dots (bool, optional): Whether to allow dots in keys. Defaults to False.
            charset_sentinel (bool, optional): Whether to use the charset sentinel. Defaults to False.
            interpret_numeric_entities (bool, optional): Whether to interpret numeric entities. Defaults to False.
            array_format (str, optional): Preferred format for arrays. Defaults to "indices". If filter contains combined
                arrays and objects, the format will use preffered format where it can be applied and fallback to indices where it can't.
        """
        super().__init__(charset, delimiter, allow_dots, charset_sentinel, interpret_numeric_entities=True)
        self.encode = encode
        if encode and encode_values_only:
            raise ConfigurationError("Cannot encode values only when encoding is enabled")
        if not self.config["allow_dots"] and encode_dot_in_keys:
            raise ConfigurationError("Cannot encode dots in keys when dots are not allowed")
        self.encode_dot_in_keys = encode_dot_in_keys
        self.encode_values_only = encode_values_only
        self.allow_empty_arrays = allow_empty_arrays
        self.array_format = ArrayFormat(array_format)

    def stringify(self, filter_: dict | QsRoot) -> str:
        if isinstance(filter_, dict):
            return self.stringify_dict(filter_)
        elif isinstance(filter_, QsRoot):
            return self.stringify_tree(filter_)
        else:
            raise UnknownInputType(f"Cannot stringify {type(filter_)}, only dict or QSRoot allowed")

    def charset_sentinel_arg(self) -> NestedArgument:
        charset_sentinel = NestedArgument()
        charset_sentinel.append_key("utf8")
        charset_sentinel.set_value("✓")
        return charset_sentinel

    def stringify_tree(self, root: QsRoot) -> str:
        if root.is_empty:
            return formatted_string
        arglist: list[NestedArgument] = []
        for node in root.children:
            arglist += self.traverse_node(node, None)
        if self.config["charset_sentinel"]:
            arglist.insert(0, self.charset_sentinel_arg())
        formatted_string = self.config["delimiter"].join(
            [
                arg.stringify(
                    charset=self.config["charset"],
                    allow_dots=self.config["allow_dots"],
                    encode=self.encode,
                    encode_dot_in_keys=self.encode_dot_in_keys,
                    encode_values_only=self.encode_values_only,
                )
                for arg in arglist
            ]
        )
        return formatted_string

    def traverse_node(self, node: QsNode, parent_arg: NestedArgument) -> list[NestedArgument]:
        arg = NestedArgument() if parent_arg is None else parent_arg.create_copy()
        if node.is_leaf:
            arg.append_key(node.key)
            arg.set_value(node.value)
            return [arg]
        elif node.is_simple_array_branch:
            child_nodes = sorted(node.value, key=lambda x: x.key)
            arg.append_key(node.key)
            return self.create_array_arguments(child_nodes, arg)
        elif node.is_array_branch:
            return self.process_complex_array_branch(node, arg)
        else:
            # object branch
            arglist = []
            for child in node.value:
                if parent_arg is None:
                    arg = NestedArgument()
                else:
                    arg = parent_arg.create_copy()
                arg.append_key(node.key)
                arglist += self.traverse_node(child, arg)
            return arglist

    def create_array_arguments(self, node_list: list[QsNode], parent_arg: NestedArgument) -> list[NestedArgument]:
        """
        Create a list of NestedArgument objects from a list of QsNode (which are always array leaf nodes in correct order).

        Args:
            node_list (list[QsNode]): List of QsNode array leaf nodes in correct order (based on their key representing array index).
            parent_arg (NestedArgument): Parent argument object.

        Returns:
            list[NestedArgument]: List of NestedArgument objects.
        """
        arglist = []
        if parent_arg is None:
            raise Unparsable("Cannot create array without parent argument")
        match self.array_format:
            case ArrayFormat.INDICES:
                # iterate over the children with sorted keys
                for node in node_list:
                    arg = parent_arg.create_copy()
                    # set value of the argument to the value of the child node
                    arg.set_value(node.value)
                    # append index as key to the list of keys
                    arg.append_key(node.key)
                    arglist.append(arg)
            case ArrayFormat.BRACKETS:
                arg = parent_arg.create_copy()
                arg.set_value(f'[{",".join([node.value for node in node_list])}]')
                arglist.append(arg)
            case ArrayFormat.REPEAT:
                for node in node_list:
                    arg = parent_arg.create_copy()
                    # set value of the argument to the value of the child node
                    arg.set_value(node.value)
                    # append the current node key to the list of keys
                    arglist.append(arg)
            case ArrayFormat.COMMA:
                # same as brackets, but with commas
                arg = parent_arg.create_copy()
                arg.set_value(f'{",".join([node.value for node in node_list])}')
                arglist.append(arg)
        if arglist == []:
            if self.allow_empty_arrays:
                arg = parent_arg.create_copy()
                arg.append_key("")
                arg.set_value(NoValue)
                arglist.append(arg)
        return arglist

    def process_complex_array_branch(self, node: QsNode, parent_arg: NestedArgument) -> list[NestedArgument]:
        """
        Create a list of NestedArgument objects from a complex array branch.
        """
        # this operation is kind of tricky since we want to minimize the number of arguments
        # complex array branch means it can contain simple values but nested arrays or objects as well
        # best approach is to produce single argument that represents as many simple values as possible until first non-simple value is encountered
        # after that, 'indices' array format has to be used
        arglist = []
        simple_values = []
        for child in sorted(node.value, key=lambda x: x.key):
            if child.is_leaf:
                simple_values.append(child)
            else:
                if simple_values:
                    new_arg = parent_arg.create_copy()
                    new_arg.append_key(node.key)
                    # if there are simple values, process them first
                    arglist += self.create_array_arguments(simple_values, parent_arg)
                    simple_values = []
                # process the child node
                # handle all other items as 'indices' array format
                arg = parent_arg.create_copy()
                arg.append_key(node.key)
                arglist += self.traverse_node(child, arg)
        return arglist

    def stringify_dict(self, filter_: dict) -> str:
        root = QsRoot(None)
        for key, value in filter_.items():
            node = QsNode.load_from_dict(key, value, parse_array=True, allow_empty=True)
            root.add_child(node)
        return self.stringify_tree(root)


# shortcut method
def stringify(
    filter_: dict | QsRoot,
    charset: str = "utf-8",
    delimiter: t_Delimiter = "&",
    allow_dots: bool = False,
    encode_dot_in_keys: bool = False,
    charset_sentinel: bool = False,
    encode: bool = True,
    allow_empty_arrays: bool = False,
    encode_values_only: bool = False,
    array_format: str = "indices",
) -> str:
    """
    Shortcut method for stringifying a filter.

    Args:
        filter_ (dict | QSRoot): Filter to stringify.
        charset (str, optional): The charset to use for encoding and decoding. Defaults to "utf-8".
        delimiter (t_Delimiter, optional): The delimiter to use for separating key-value pairs. Defaults to "&".
        allow_dots (bool, optional): Whether to allow dots in keys. Defaults to False.
        charset_sentinel (bool, optional): Whether to use the charset sentinel. Defaults to False.
        interpret_numeric_entities (bool, optional): Whether to interpret numeric entities. Defaults to False.
        array_format (str, optional): Preferred format for arrays. Defaults to "indices". If filter contains combined
            arrays and objects, the format will use preffered format where it can be applied and fallback to indices where it can't.

    Returns:
        str: Stringified filter.
    """
    stringifier = QsStringifier(
        charset=charset,
        delimiter=delimiter,
        allow_dots=allow_dots,
        encode_dot_in_keys=encode_dot_in_keys,
        charset_sentinel=charset_sentinel,
        allow_empty_arrays=allow_empty_arrays,
        encode=encode,
        encode_values_only=encode_values_only,
        array_format=array_format,
    )
    return stringifier.stringify(filter_)
