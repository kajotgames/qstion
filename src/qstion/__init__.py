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