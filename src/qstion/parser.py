import typing as t
import re
import urllib.parse as up


class QsParser:
    _separator = '&'
    _args: dict[str, str] = None

    @classmethod
    def from_url(cls, url: str, separator: str = '&') -> 'QsParser':
        args = {}
        parsed_url = up.urlparse(url)
        query_args = parsed_url.query.split(separator)
        for arg in query_args:
            args.update(cls._parse_arg_name(arg))
        return cls(args)

    @staticmethod
    def _parse_arg_name(arg: str) -> str:
        arg_key, arg_val = arg.split('=')
        return {up.unquote(arg_key) : up.unquote(arg_val)}


    def __init__(self, args: dict[str, str]) -> None:
        for k, v in args.items():
            self._parse_arg(k, v)

    def _parse_arg(self, k: str, v: str) -> None:
        nested = self._parse_key(k)
        self._args = QsParser._add_nested(nested, v, self._args)

    @staticmethod
    def _handle_incoming(incoming) -> dict:
        if incoming is None:
            return {}
        if isinstance(incoming, str):
            return {incoming: True}
        if isinstance(incoming, dict):
            return incoming


    @staticmethod
    def _handle_add(incoming, k, v):
        if incoming == {}:
            return {k: v}
        if k not in incoming:
            incoming[k] = v
        else:
            incoming[k].update({v: True})
        return incoming
    
    @staticmethod
    def _add_nested(keys: list, v: str, incoming: dict = None) -> dict:
        incoming = QsParser._handle_incoming(incoming)
        if len(keys) == 1:
            return QsParser._handle_add(incoming, keys[0], v)
        if keys[0] not in incoming:
            incoming[keys[0]] = QsParser._add_nested(keys[1:], v)
        else:
            incoming[keys[0]] = QsParser._add_nested(keys[1:], v, incoming[keys[0]])
        return incoming

    def _parse_key(self, k: str) -> list:
        """
        Parses key into a list of nested keys.
        """
        if res := re.match(r'^(\w+)(\[\w+\])*$', k):
            nested = re.findall(r'\[(\w+)\]', k)
            return [res.group(1)] + nested

