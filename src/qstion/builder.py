from .parser import ParsedUrl
import typing as t
from abc import ABC, abstractmethod
from sqlalchemy import Column, Table, Join, Select, select
from sqlalchemy.sql.selectable import _ColumnExpressionArgument


class ColumnWrapper:
    _col: Column
    _sortable: bool
    _filterable: bool


class QueryModel:
    _fields: dict[str, ColumnWrapper]

    def __init__(self, *cols: ColumnWrapper):
        self._fields = {col._col.name: col for col in cols}

    def __getitem__(self, key: str) -> ColumnWrapper:
        return self._fields[key]


class QueryBuilder(ABC):
    pass

    @abstractmethod
    @classmethod
    def build_query(cls, url_query: ParsedUrl, model: QueryModel, source: t.Any):
        pass


class SQL(QueryBuilder):
    """
    Query builder for SQL databases.
    """
    _base: Select

    def __init__(self, base: Select):
        self._base = base

    def verify_filter(self, _filter):
        pass
    # TODO - instead of column use column wrapper to enable options like sortable, filterable, etc.

    @classmethod
    def build_query(cls, url_query: ParsedUrl, model: QueryModel, source: Table | Join | list) -> Select:
        """
        Build a query from a parsed URL.

        :param url_query: Parsed URL to build a query from
        :param model: Model to build a query for
        :param source: Source of data (e.g. SQLAlchemy table, sqlalchemy join or list of them)
        """
        # TODO validate query params against model
        base_query = select(*[model[col]._col.label(col)
                            for col in model._fields]).select_from(source)
        obj = cls(base_query)

    @staticmethod
    def _filter_query(filter_col: Column, filter_op: str, filter_val: t.Any) -> Select:
        op_map = {
            "eq": SQL._eq,
            "ne": SQL._ne,
            "gt": SQL._gt,
            "gte": SQL._gte,
            "lt": SQL._lt,
            "lte": SQL._lte,
            "in": SQL._in,
        }

    @staticmethod
    def _eq(filter_col: Column, filter_val: t.Any) -> _ColumnExpressionArgument[bool]:
        return (filter_col == filter_val)

    @staticmethod
    def _ne(filter_col: Column, filter_val: t.Any) -> _ColumnExpressionArgument[bool]:
        return (filter_col != filter_val)

    @staticmethod
    def _gt(filter_col: Column, filter_val: t.Any) -> _ColumnExpressionArgument[bool]:
        return (filter_col > filter_val)

    @staticmethod
    def _gte(filter_col: Column, filter_val: t.Any) -> _ColumnExpressionArgument[bool]:
        return (filter_col >= filter_val)

    @staticmethod
    def _lt(filter_col: Column, filter_val: t.Any) -> _ColumnExpressionArgument[bool]:
        return (filter_col < filter_val)

    @staticmethod
    def _lte(filter_col: Column, filter_val: t.Any) -> _ColumnExpressionArgument[bool]:
        return (filter_col <= filter_val)

    @staticmethod
    def _in(filter_col: Column, filter_val: t.Any) -> _ColumnExpressionArgument[bool]:
        return (filter_col.in_(filter_val))


class Mongo(QueryBuilder):
    pass


def build(
    url_query: ParsedUrl,
    builder: QueryBuilder,
    model: dict,
    source: t.Any,
):
    """
    Build a query from a parsed URL.

    :param url_query: Parsed URL to build a query from
    :param builder: Query builder to use
    :param model: Model to build a query for
    :param source: Source of data (e.g. SQLAlchemy table, MongoEngine collection)
    """
    pass
