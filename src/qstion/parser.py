import typing as t
import urllib.parse as up
import re


class QsParser:
    _args: dict[str, str] = None
    _max_depth: int = 5

    def __init__(self, args: dict[str, str], max_depth: int = 5) -> None:
        """
        Parser initialisation. Performs syntax validation.
        """
        self._max_depth = max_depth
        for k, v in args.items():
            self._parse_arg(k, v)

    @property
    def args(self) -> dict[str, str]:
        """
        Returns parsed arguments.
        """
        return self._args

    @classmethod
    def from_url(cls, url: str, separator: str = '&', max_depth: int = 5) -> 'QsParser':
        """
        Creates a parser from a url.
        """
        args = {}
        parsed_url = up.urlparse(url)
        query_args = parsed_url.query.split(separator)
        for arg in query_args:
            args.update(cls._parse_arg_name(arg))
        return cls(args, max_depth=max_depth)

    @staticmethod
    def _parse_arg_name(arg: str) -> str:
        """
        Split argument into key and value. returns a dict (url decoded)
        """
        arg_key, arg_val = arg.split('=')
        return {up.unquote(arg_key): up.unquote(arg_val)}

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
