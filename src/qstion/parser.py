import typing as t
import re
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass

KEYWORDS = ['sort_by', 'limit', 'offset']


@dataclass(slots=True)
class FilterOption:
    _op: str
    _val: t.Any

    def __init__(self, op, val) -> None:
        self._op = op
        self._val = val


@dataclass(slots=True)
class KeywordOption:
    _val: t.Any

    def __init__(self, val):
        self._val = val

    # TODO - only for debug
    def __str__(self) -> str:
        return str(self._val)

@dataclass(slots=True)
class OrderOption(KeywordOption):
    _dir: int

    def __init__(self, arg_val) -> None:
        arg = self._parse_direction(arg_val)
        super().__init__(arg)

    def _parse_direction(self, arg_val: str):
        ordering_opts = {
            "+": 1,
            "-": -1,
            "asc": 1,
            "desc": -1,
        }
        try:
            if res := re.match(r"^(\+|-)(\w+)", arg_val):
                self._dir = ordering_opts[res.group(1)]
                return res.group(2)
            elif res := re.match(r"^(\w+)\((\w+)\)", arg_val):
                self._dir = ordering_opts[res.group(1)]
                return res.group(2)
            elif res := re.match(r"^(\w+)\.(\w+)", arg_val):
                self._dir = ordering_opts[res.group(2)]
                return res.group(2)
            else:
                raise ValueError(f"Invalid ordering argument: {arg_val}")
        except KeyError:
            raise ValueError(f"Invalid ordering argument: {arg_val}")

    # TODO - only for debug    
    def __str__(self) -> str:
        return f"{self._dir} {self._val}"

class ParsedUrl:
    """
    Parsed URL with validated url arguments.
    """
    _args: dict

    def __init__(self, url_args: dict):
        self._args = {}
        print(f'raw args: {url_args}')
        input(f'Press any key to continue...')
        for arg, val in url_args.items():
             self.parse_arg(arg, val)

    def _parse_kwarg(self, arg: str, arg_val: t.Any) -> KeywordOption:
        """
        Parse a keyword argument into a keyword option.

        :param arg: URL argument to parse
        """
        if arg == "sort_by":
            self._args['sort_by'] = [OrderOption(arg_val)]
        else:
            return KeywordOption(arg_val)

    def parse_arg(self, arg: str, arg_val: t.Any) -> FilterOption | KeywordOption:
        """
        Parse a url argument into a filter option.

        :param arg: URL argument to parse
        """
        if res := re.match(r"^(\w+)\[(\w+)\]$", arg):
            return self._parse_filter(res.group(1), res.group(2), arg_val)
        elif arg in KEYWORDS:
            return self._parse_kwarg(arg, arg_val)
        # TODO for now, just ignore other arguments (e.g. nesting)
        else:
            raise ValueError(f"Invalid argument: {arg}")

    def _parse_filter(self, filter_col: str, filter_op, arg_val: t.Any) -> None:
        """
        Parse a url argument into a filter option.

        :param arg: URL argument to parse
        """
        if filter_col not in self._args:
            self._args[filter_col] = [FilterOption(filter_op, arg_val)]
        else:
            self._args[filter_col].append(FilterOption(filter_op, arg_val))

    @classmethod
    def _from_string(cls, url: str, separator: str = "&"):
        """
        Parse a URL into a parsed object with url arguments.

        :param url: URL to parse
        """
        parsed = urlparse(url)
        url_args = parse_qs(parsed.query, separator=separator)
        return cls(url_args)

    # DEBUG
    def _filter(self):
        for arg, val in self._args.items():
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, FilterOption):
                        print(f"{arg}[{item._op}] = {item._val}")

    def _kw(self):
        for arg, val in self._args.items():
            if isinstance(val, KeywordOption):
                print(f"{arg} = {str(val)}")


def parse(url: str, url_args: dict = None) -> ParsedUrl:
    """
    Parse a URL into a parsed object with url arguments.

    :param url: URL to parse
    """
    obj = None
    if url_args is None:
        obj = ParsedUrl._from_string(url)
    else:
        obj = ParsedUrl(url_args)
    return obj

# TODO multiple same arguments handling
if __name__ == "__main__":
    o = parse("www.example.com?bla[gte]=10&bla[gte]=5&sort_by=+bla")
    o._filter()
    o._kw()
