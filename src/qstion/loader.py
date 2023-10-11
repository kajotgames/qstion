from abc import ABC, abstractmethod
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import Label, BinaryExpression, UnaryExpression
from sqlalchemy import Column, and_, asc, desc
import typing as t
import re

if t.TYPE_CHECKING:
    from .models import OutputModel

class QueryFilterFactory(ABC):
    KWARGS = ['sort_by', 'limit', 'offset']

    @abstractmethod
    @classmethod
    def build_query(cls, query, filters: dict) -> t.Any:
        pass

    @staticmethod
    def parse_sort_item(item: str) -> tuple(int, str):
        """
        Method that parses sort item and returns column name and sort direction

        :param item: sort item
        :return: tuple of column name and sort direction
        """
        direction = 1
        sort_col = None
        if res:= re.match(r'^([+-]?)(\w+)$', item):
            direction = -1 if res.group(2) == '-' else 1
            sort_col = res.group(2)
        elif res:= re.match(r'(asc|desc)\((\w+)\)$', item):
            direction = -1 if res.group(1) == 'desc' else 1
            sort_col = res.group(2)
        elif res:= re.match(r'^(\w+)\.(asc|desc)$', item):
            direction = -1 if res.group(2) == 'desc' else 1
            sort_col = res.group(1)
        else:
            raise ValueError(f"Invalid sort item {item}")
        return (direction, sort_col)

class SQL(QueryFilterFactory):
    t_Column = t.Union[Column, Label]
    OPERATORS: dict[str, t.Callable]
    column_map: dict[str, Column]
    sort_directions: dict[str, callable] = {
        1: asc,
        -1: desc,
    }

    def __init__(self, *cols: t_Column):
        self.OPERATORS = {
            'eq': SQL._eq,
            'ne': SQL._ne,
            'neq': SQL._ne,
            'gt': SQL._gt,
            'ge': SQL._ge,
            'gte': SQL._ge,
            'lt': SQL._lt,
            'le': SQL._le,
            'lte': SQL._le,
            'in': SQL._in,
            'nin': SQL._nin,
        }
        for col in cols:
            self.add_col(col)

    def sort_expr(self, item: str) -> UnaryExpression:
        """
        Method that returns sort expression for single sort item

        :param item: sort item
        :return: sort expression
        """
        direction, sort_col = self.parse_sort_item(item)
        # TODO produces error if sort_col is not in column_map
        return self.sort_directions[direction](self.column_map[sort_col])
        
        
    def process_filter_item(self, key: str, value: dict) -> list(BinaryExpression) | None:
        """
        Method that processes single filter item and returns list of expressions

        :param key: key of filter item
        :param value: value of filter item
        :return: list of expressions

        Following filter values are supported:
        {<operator>: [<values>]}
        -> handling: `eq` operator as `in` operator (`ne` as `nin`)
        
        """
        expressions = []
        if key in self.KWARGS:
            return None
        if not isinstance(value, dict):
            # value is not dict and not a kwarg -> undefined operation on column
            raise ValueError(f"Invalid filter item {key}={value}")
        for op, val in value.items():
            if op not in self.OPERATORS:
                raise ValueError(f"Invalid operator {op}")
            if isinstance(val, list):
                for v in val:
                    expressions.append(self.OPERATORS[op](self.column_map[key], v))
            else:
                expressions.append(self.OPERATORS[op](self.column_map[key], val))
        return expressions

    def add_col(self, col: t_Column):
        if isinstance(col, Label):
            self.column_map[col.name] = col.element
        else:
            self.column_map[col.name] = col
        

    @staticmethod
    def verify_column(column: t.Any):
        if not isinstance(column, (Column, Label)):
            raise TypeError(f"Column must be instance of Column or Label not {type(column)}")

    def process_sort(self, query: Select, sort_by: str | list[str] | None) -> Select:
        if not sort_by:
            return query
        if isinstance(sort_by, str):
            sort_by = [sort_by]
        sort_expr = []
        for item in sort_by:
            sort_expr.append(self.parse_sort_item(item))
        return query.order_by(*sort_expr)
    
    def add_pagination(self, query: Select, limit: int | None, offset: int | None) -> Select:
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query

    @classmethod
    def build_query(cls, query : Select, filters: dict, model: 'OutputModel') -> Select:
        for col in query._raw_columns:
            cls.verify_column(col)
        obj = cls(*query._raw_columns)
        selected_cols = list(obj.column_map.keys())
        model_cols = list(model.fields.keys())
        # verify that all model columns correspond to selected columns
        if not all([col in selected_cols for col in model_cols]):
            raise ValueError(f"Model columns {model_cols} are not in selected columns {selected_cols}")
        binary_expressions = []
        for key, value in filters.items():
            expressions = obj.process_filter_item(key, value)
            if expressions:
                binary_expressions.extend(expressions)
        if binary_expressions:
            query = query.where(and_(*binary_expressions))
        query = obj.process_sort(query, filters.get('sort_by', None))
        query = obj.add_pagination(query, filters.get('limit', None), filters.get('offset', None))
        return query


    @staticmethod
    def _eq(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (column == value)
    
    @staticmethod
    def _ne(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (column != value)
    
    @staticmethod
    def _gt(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (column > value)
    
    @staticmethod
    def _ge(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (column >= value)
    
    @staticmethod
    def _lt(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (column < value)
    
    @staticmethod
    def _le(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (column <= value)
    
    @staticmethod
    def _in(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (column.in_(value))
    
    @staticmethod
    def _nin(column: t_Column, value: t.Any) -> BinaryExpression: 
        return (~column.in_(value))
    
    #TODO add more operators



# TODO - implement QueryFilter
# 1. load output model
# 2. run qsParser
# 3. validate input based on output model and filters provided
# 4. as result return object, with which query can be built for
# specific databqase - separate classes that will have method build_query
# which will return query for specific database
# - inspect sql selects (whole statements) and return list of columns
# mongo filtering