import typing as t
from html import unescape as unescape_html
import urllib.parse as up
import re

from ._exc import Unparsable
from ._struct_core import QsNode, QsRoot

t_Delimiter = t.Union[str, t.Pattern[str]]


def unpack_payload(payload: str | bytes) -> str:
    """
    Unpacks payload from bytes to string.

    Args:
        payload (str): payload to unpack

    Returns:
        str: unpacked payload
    """
    if isinstance(payload, bytes):
        return payload.decode("utf-8")
    return payload


def retrieve_charset(arg_list: list[str]) -> str | None:
    """
    Retrieve charset sentinel from list of arguments and remove it from the list

    Args:
        arg_list (list): list of arguments

    Returns:
        str: charset or None if not found
    """
    charset_arg = next((arg for arg in arg_list if arg.startswith("utf8=")), None)
    if charset_arg is None:
        return None
    # Remove charset sentinel from list
    arg_list.remove(charset_arg)
    charset_value = re.match(r"utf8=(.*)", charset_arg).group(1)
    available_charsets = ["utf-8", "iso-8859-1"]
    targeted_character = "✓"
    for charset in available_charsets:
        if unescape_html(up.unquote(charset_value, encoding=charset)) == targeted_character:
            return charset
    raise Unparsable("Unable to parse charset sentinel")


def unquote_arguments(arg_list: list[str], charset: str) -> list[str]:
    """
    Unquote arguments in list

    Args:
        arg_list (list): list of arguments
        charset (str): charset to use

    Returns:
        list: unquoted arguments
    """
    return [up.unquote(arg, encoding=charset) for arg in arg_list]


def process_numeric_entities(arg_list: list[str]) -> list[str]:
    """
    Process numeric entities in list

    Args:
        arg_list (list): list of arguments

    Returns:
        list: processed arguments
    """
    return [unescape_html(arg) for arg in arg_list]


class QsConfiguration(t.TypedDict):
    """
    Configuration options for query string parser and stringifier
    """

    charset: str
    delimiter: t_Delimiter
    allow_dots: bool
    charset_sentinel: bool
    interpret_numeric_entities: bool


class QSCore:
    """
    Base class for query string parser and stringifier
    Contains basic configuration options for parsing and stringifying query strings and
    methods for loading and preprocessing data.
    """

    config: QsConfiguration

    def __init__(
        self,
        charset: str = "utf-8",
        delimiter: t_Delimiter = "&",
        allow_dots: bool = False,
        charset_sentinel: bool = False,
        interpret_numeric_entities: bool = False,
    ):
        self.config = {
            "charset": charset,
            "delimiter": delimiter,
            "allow_dots": allow_dots,
            "charset_sentinel": charset_sentinel,
            "interpret_numeric_entities": interpret_numeric_entities,
        }

    def load_query_string(self, query_string: str | bytes) -> list[str]:
        """
        Load query string from bytes or string into list of raw arguments

        Args:
            qs (str): query string

        Returns:
            list: list of raw arguments in query string
        """
        raw_args = []
        unpacked_qs = unpack_payload(query_string)

        split_args = re.split(self.config["delimiter"], unpacked_qs)
        if self.config["charset_sentinel"]:
            charset = retrieve_charset(split_args)
            if charset is not None:
                self.config["charset"] = charset
        unquoted_args = unquote_arguments(split_args, self.config["charset"])
        if self.config["interpret_numeric_entities"]:
            raw_args = process_numeric_entities(unquoted_args)
        else:
            raw_args = unquoted_args
        return raw_args
