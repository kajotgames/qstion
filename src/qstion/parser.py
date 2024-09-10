import typing as t
import re
import decimal
import urllib.parse as urlparse

from ._qs_core import QSCore
from ._struct_core import QsNode, EnumDuplicateKeys, QsRoot, NoValue, t_Delimiter
from ._exc import Unparsable, ConfigurationError


def process_argument_key(arg_key: str, allow_dots: bool = False, allow_empty_key: bool = False) -> re.Match | None:
    """
    Process argument key - verify syntax by regular expression and return match object of nesting
    Groups:
    1. root key
    2. grouped nestings

    Args:
        arg_key (str): argument key

    Returns:
        re.Match | None: match object or None if not matched
    """
    key_pattern_no_empty = r"^([^\[\]]+)"
    key_pattern_empty = r"^([^\[\]]*)"
    nesting_pattern = r"((?:\[[^\[\]]*\])*)$"

    key_pattern_with_dots = r"^([^\[\]\.]+)"
    key_pattern_with_dots_empty = r"^([^\[\]\.]*)"
    nesting_pattern_with_dots = r"((?:\.[^\[\]\.]*)*)$"

    if allow_dots:
        parse_pattern = (
            key_pattern_with_dots_empty + nesting_pattern_with_dots
            if not allow_empty_key
            else key_pattern_with_dots + nesting_pattern_with_dots
        )
        dot_match = re.match(parse_pattern, arg_key)
        if dot_match is not None:
            return dot_match

    parse_pattern = (
        key_pattern_no_empty + nesting_pattern if not allow_empty_key else key_pattern_empty + nesting_pattern
    )
    return re.match(parse_pattern, arg_key)


def process_nested_keys(nestings: str, allow_dots: bool = False) -> list[str]:
    """
    Process nested keys - split nested keys into list of keys

    Args:
        nestings (str): nested keys
        allow_dots (bool): whether to allow dot notation

    Returns:
        list: list of nested keys
    """
    dot_notation_pattern = r"\.([^\[\]\.]*)"
    bracket_notation_pattern = r"\[([^\[\]]*)\]"
    dot_results = []
    if allow_dots:
        dot_results = re.findall(dot_notation_pattern, nestings)
    bracket_results = re.findall(bracket_notation_pattern, nestings)
    # if allow dots is enabled and bracket results are empty, return dot results, otherwise return bracket results
    return dot_results if allow_dots and not bracket_results else bracket_results


def process_into_primitive(arg_val: str, primitive_strict: bool = False) -> decimal.Decimal | bool | None | str:
    """
    Process value into primitive types

    Args:
        arg_val (str): argument value
        primitive_strict (bool): whether to parse values into primitives only if they have strict format e.g. True, False, None (case sensitive)

    Returns:
        any: processed value
    """
    # check for decimal values
    # if value starts with either '/" and ends with its counterpart, it is considered as string and should be stripped
    if arg_val.startswith(('"', "'")) and arg_val.endswith(arg_val[0]):
        return arg_val[1:-1]
    try:
        return decimal.Decimal(arg_val)
    except decimal.InvalidOperation:
        pass
    # check for boolean or null values
    strict_mapping = {
        "true": True,
        "True": True,
        "false": False,
        "False": False,
        "null": None,
        "None": None,
    }
    non_strict_mapping = {
        "true": True,
        "false": False,
        "null": None,
        "none": None,
    }
    if primitive_strict:
        return strict_mapping.get(arg_val, arg_val)
    return non_strict_mapping.get(arg_val.lower(), arg_val)


def process_argument_value(
    arg_val: str,
    parse_primitive: bool = False,
    primitive_strict: bool = False,
    comma: bool = False,
    brackets: bool = False,
) -> t.Any:
    """
    Process argument value - parse value into primitive types if needed

    Args:
        arg_val (str): argument value
        parse_primitive (bool): whether to parse value into primitive types e.g. int, float, bool
        primitive_strict (bool): whether to parse values into primitives only if they have strict format e.g. True, False, None (case sensitive)
        comma (bool): whether to parse comma separated values into list

    Returns:
        any: processed value
    """
    if arg_val is NoValue:
        return arg_val
    if comma:
        arg_val = arg_val.split(",")
        if len(arg_val) > 1:
            return [
                process_argument_value(val, parse_primitive=parse_primitive, primitive_strict=primitive_strict)
                for val in arg_val
            ]
        else:
            arg_val = arg_val[0]
    # also allow processing of bracketed arrays as values, mutually exclusive with comma
    if brackets:
        if arg_val.startswith("[") and arg_val.endswith("]"):
            arg_val = arg_val[1:-1].split(",")
            return [
                process_argument_value(val, parse_primitive=parse_primitive, primitive_strict=primitive_strict)
                for val in arg_val
            ]
    if parse_primitive:
        return process_into_primitive(arg_val, primitive_strict=primitive_strict)
    # if value starts with either '/" and ends with its counterpart, it is considered as string and should be stripped
    if arg_val.startswith(('"', "'")) and arg_val.endswith(arg_val[0]):
        return arg_val[1:-1]
    return arg_val


def dict_from_tuple(tup: tuple[t.Any, t.Any]) -> dict:
    """
    Convert tuple into dictionary

    Args:
        tup (tuple): tuple to convert

    Returns:
        dict: converted dictionary
    """
    return {tup[0]: tup[1]}


class QsParser(QSCore):
    """
    Query string parser class
    """

    decode_dots_in_keys: bool
    max_depth: int
    strict_depth: bool
    parameter_limit: int
    allow_empty_keys: bool
    parse_arrays: bool
    allow_empty_arrays: bool
    allow_sparse_arrays: bool
    array_limit: int
    comma: bool
    brackets: bool
    parse_primitive: bool
    primitive_strict: bool
    duplicate_keys: EnumDuplicateKeys

    def __init__(
        self,
        charset: str = "utf-8",
        delimiter: t_Delimiter = "&",
        allow_dots: bool = False,
        charset_sentinel: bool = False,
        interpret_numeric_entities: bool = False,
        decode_dots_in_keys: bool = False,
        max_depth: int = 5,
        strict_depth: bool = False,
        parameter_limit: int = 1000,
        allow_empty_keys: bool = True,
        parse_arrays: bool = True,
        allow_empty_arrays: bool = False,
        allow_sparse_arrays: bool = False,
        array_limit: int = 20,
        comma: bool = False,
        brackets: bool = False,
        parse_primitive: bool = False,
        primitive_strict: bool = False,
        duplicate_keys: str = "combine",
    ):
        super().__init__(
            charset=charset,
            delimiter=delimiter,
            allow_dots=allow_dots,
            charset_sentinel=charset_sentinel,
            interpret_numeric_entities=interpret_numeric_entities,
        )
        self.max_depth = max_depth
        self.strict_depth = strict_depth
        self.parameter_limit = parameter_limit
        self.allow_empty_keys = allow_empty_keys
        if self.config["allow_dots"] and parse_arrays:
            raise ConfigurationError("Arrays cannot be parsed with dot notation enabled")
        self.parse_arrays = parse_arrays
        if decode_dots_in_keys and not self.config["allow_dots"]:
            raise ConfigurationError(
                "Decode dots in keys implies allow_dots=True, it cannot be used with allow_dots=False"
            )
        self.decode_dots_in_keys = decode_dots_in_keys
        self.allow_empty_arrays = allow_empty_arrays
        self.allow_sparse_arrays = allow_sparse_arrays
        self.array_limit = array_limit
        self.comma = comma
        if self.comma and brackets:
            raise ConfigurationError("Comma and brackets cannot be used together")
        self.brackets = brackets
        self.parse_primitive = parse_primitive
        self.primitive_strict = primitive_strict
        self.duplicate_keys = EnumDuplicateKeys(duplicate_keys)

    def parse(
        self, input_data: list[tuple[str, str]] | list[str] | str, return_as_object: bool = False
    ) -> dict | QsRoot:
        """
        Parse input data into QsNode
        """
        arg_list = None
        if isinstance(input_data, list):
            if all(isinstance(item, tuple) for item in input_data):
                arg_list = self.parse_request_args(input_data)
            else:
                arg_list = self.parse_arg_list(input_data)
        elif isinstance(input_data, str):
            arg_list = self.parse_query_string(input_data)
        else:
            raise Unparsable("Invalid input data type")
        tree_root = QsRoot(self.parameter_limit)
        for arg in arg_list:
            # its dict so iterate over items
            for key, val in arg.items():
                node = QsNode.load_from_dict(
                    key, val, parse_array=self.parse_arrays, allow_empty=self.allow_empty_arrays
                )
                try:
                    tree_root.add_child(node, duplicate_keys=self.duplicate_keys)
                except Unparsable as e:
                    raise Unparsable(f"Error parsing argument '{key}': {e}")
        tree_root.process_array_limts(self.array_limit)
        if not self.allow_sparse_arrays and tree_root.has_sparse_arrays:
            raise Unparsable("Sparse arrays are not allowed")
        if return_as_object:
            return tree_root
        return tree_root.to_dict()

    def parse_request_args(self, request_args: list[tuple[str, str]]) -> list[dict]:
        """
        Parse request arguments into QsNode
        """
        # join tuples into single query string, then parse it normally
        self.config["delimiter"] = "&"
        query_string = "&".join([f"{key}={val}" for key, val in request_args])
        return self.parse_query_string(query_string)

    def parse_arg_list(self, arg_list: list[str]) -> None:
        """
        Parse argument list into QsNode
        """
        # join list into single query string, then parse it normally
        self.config["delimiter"] = "&"
        query_string = "&".join(arg_list)
        return self.parse_query_string(query_string)

    def parse_query_string(self, query_string: str) -> list[dict]:
        """
        Parse query string into list of nested dictionaries
        """
        separate_args = self.load_query_string(query_string)
        parsed_args = []
        for arg in separate_args:
            try:
                arg_key, arg_val = arg.split("=", 1)
            except ValueError:
                arg_key = arg
                arg_val = NoValue
            parsed_args.append(self.parse_arg(arg_key, arg_val))
        return parsed_args

    def parse_arg(self, arg_key: str, arg_val: str | None) -> dict:
        """
        Parse argument into nested dictionary
        """
        # 1. start with trivial parsing: (a,b)
        # 2. add nesting options: a[b]=c -> requires syntax check and parsing
        if arg_val is None:
            parsed_value = None
        else:
            parsed_value = process_argument_value(
                arg_val,
                parse_primitive=self.parse_primitive,
                primitive_strict=self.primitive_strict,
                comma=self.comma,
                brackets=self.brackets,
            )
        pattern_match = process_argument_key(
            arg_key, allow_dots=self.config["allow_dots"], allow_empty_key=self.allow_empty_keys
        )
        if pattern_match is None:
            raise Unparsable(f"Argument key '{arg_key}' has invalid syntax")
        root_key = pattern_match.group(1)
        nestings = pattern_match.group(2)
        if not nestings:
            return {root_key: parsed_value}
        # process nestings
        nesting_keys = process_nested_keys(nestings, allow_dots=self.config["allow_dots"])
        # based on max depth, check if nesting keys are within limits, otherwise replace items over limit with last index
        if self.strict_depth and len(nesting_keys) > self.max_depth:
            raise Unparsable(f"Argument key '{arg_key}' exceeds max depth of {self.max_depth}")
        if len(nesting_keys) > self.max_depth:
            over_limit_items = nesting_keys[self.max_depth :]
            replace_key = (
                ".".join(over_limit_items) if self.config["allow_dots"] else f'[{"][".join(over_limit_items)}]'
            )
            nesting_keys = nesting_keys[: self.max_depth]
            nesting_keys.append(replace_key)
        # if parse_arrays is enabled, empty strings are allowed and are considered as array elements
        # if parse_arrays is disabled, empty strings are allowed only if self.allow_empty_keys is enabled
        if self.parse_arrays:
            # replace any empty strings with integer index 0, replace any non-empty, digit-like strings with integers
            nesting_keys = [int(key) if key.isdigit() else key for key in nesting_keys]
        else:
            if not self.allow_empty_keys and "" in nesting_keys:
                raise Unparsable(f"Empty keys are not allowed in argument key '{arg_key}'")
        # process nesting keys
        for key in reversed(nesting_keys):
            parsed_value = dict_from_tuple((key, parsed_value))
        if self.decode_dots_in_keys:
            root_key = urlparse.unquote(root_key)
        return {root_key: parsed_value}


# Shortcut methods


def parse(
    data: t.Any,
    from_url: bool = False,
    charset: str = "utf-8",
    delimiter: t_Delimiter = "&",
    allow_dots: bool = False,
    charset_sentinel: bool = False,
    interpret_numeric_entities: bool = False,
    decode_dots_in_keys: bool = False,
    max_depth: int = 5,
    strict_depth: bool = False,
    parameter_limit: int = 1000,
    allow_empty_keys: bool = True,
    parse_arrays: bool = False,
    allow_empty_arrays: bool = False,
    allow_sparse_arrays: bool = False,
    array_limit: int = 20,
    comma: bool = False,
    brackets: bool = False,
    parse_primitive: bool = False,
    primitive_strict: bool = False,
    duplicate_keys: str = "combine",
    return_as_obj: bool = False,
) -> dict | QsRoot:
    """
    Parses a string into a qs-like nested dictionary or QsRoot object.

    Args:
        data (str): data to parse
        from_url (bool): whether data provided is whole url or not
        charset (str): charset to use
        delimiter (str): delimiter to use
        allow_dots (bool): whether to allow dots in keys
        charset_sentinel (bool): whether to use charset sentinel from args
        interpret_numeric_entities (bool): whether to interpret numeric entities
        decode_dots_in_keys (bool): whether to decode dots in keys
        max_depth (int): max depth of nesting
        strict_depth (bool): whether to strictly enforce max depth
        parameter_limit (int): parameter limit
        allow_empty_keys (bool): whether to allow empty keys
        parse_arrays (bool): whether to parse arrays
        allow_empty_arrays (bool): whether to allow empty arrays
        allow_sparse_arrays (bool): whether to allow sparse arrays
        array_limit (int): array limit
        comma (bool): whether to parse comma separated values into list
        parse_primitive (bool): whether to parse primitive values
        primitive_strict (bool): whether to parse primitive values strictly
        duplicate_keys (str): duplicate keys handling
        return_as_obj (bool): whether to return as QsRoot object

    Returns:
        dict | QSRoot: parsed data
    """
    parser = QsParser(
        charset=charset,
        delimiter=delimiter,
        allow_dots=allow_dots,
        charset_sentinel=charset_sentinel,
        interpret_numeric_entities=interpret_numeric_entities,
        decode_dots_in_keys=decode_dots_in_keys,
        max_depth=max_depth,
        strict_depth=strict_depth,
        parameter_limit=parameter_limit,
        allow_empty_keys=allow_empty_keys,
        parse_arrays=parse_arrays,
        allow_empty_arrays=allow_empty_arrays,
        allow_sparse_arrays=allow_sparse_arrays,
        array_limit=array_limit,
        comma=comma,
        brackets=brackets,
        parse_primitive=parse_primitive,
        primitive_strict=primitive_strict,
        duplicate_keys=duplicate_keys,
    )
    if from_url:
        data = urlparse.urlparse(data).query
    return parser.parse(data, return_as_object=return_as_obj)
