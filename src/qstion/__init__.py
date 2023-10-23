# TODO:
# url_query = qstion.parse("www.example.com?bla[gte]=10")
# sql_query = qstion.build(
#     url_query,
#     builder=qstion.sql,
#     model=my_model,
# )

# model cannot be from restx:
# 1. in order to build a query (as universal method `build`) - in SQL model should represent some kind of object
# which has options to show output fields, and produce a query for corresponding database
# meaning model should be universal class for all databases and based on builder, it should produce a query
# in sql assume base Table objects
# in mongo assume base Collection objects and Table objects

from . import loader, parser, models
import typing as t


def parse(
        url: str,
        separator: str = '&',
        max_depth: int = 5) -> dict:
    """
    Parses a url into a dict.
    """
    return parser.QsParser.parse(url, separator, max_depth).args()


def build(
        filters: dict,
        model: models.OutputModel,
        builder: type[loader.QueryFilterFactory],
        data_src: t.Any = None) -> t.Any:
    """
    Builds a query based on filters and model.
    """
    model.validate(filters, builder)
    return builder.build_query(data_src, filters)
