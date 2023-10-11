from flask_restx import Namespace, fields, Model
import typing as t
if t.TYPE_CHECKING:
    from .loader import QueryFilterFactory

GenericField = t.Union[
    fields.Raw,
    fields.Nested,
    fields.List,
    fields.String,
    fields.Integer,
    fields.Float,
    fields.Boolean,
    fields.DateTime,
    fields.Date,
    fields.Fixed,
    fields.Url,
    fields.Arbitrary]


class OutputField:
    _sortable: bool
    _filterable: bool
    _field: fields.Raw

    def __init__(self, name: str, field: fields.Raw, sortable: bool = False, filterable: bool = False):
        self._name = name
        self._field = field
        self._sortable = sortable
        self._filterable = filterable

    @classmethod
    def restx(cls, name: str, field_type: type, *field_args, sortable: bool = False, filterable: bool = False, **field_kwargs):
        return cls(name, field_type(*field_args, **field_kwargs), sortable, filterable)

    @property
    def name(self):
        return self._name

    @property
    def field(self):
        return self._field


GeneralField = t.Union[GenericField, OutputField]


class OutputModel:
    _name: str
    _fields: dict[str, OutputField]

    def __init__(self, name: str, fields: dict[str, OutputField]) -> None:
        self._fields = fields
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def fields(self):
        return self._fields

    def _restx_fields(self) -> dict:
        return {name: field.field for name, field in self.fields.items()}

    def restx_model(self) -> Model:
        return Model(self.name, self._restx_fields())

    @classmethod
    def with_api_fields(cls, name: str, api: Namespace, fields: dict[str, GeneralField], sortable: list[str] = [], filterable: list[str] = []) -> 'OutputModel':
        obj = cls.from_mixed_dict(name, fields, sortable, filterable)
        api.model(name, obj.restx_model())
        return obj

    @classmethod
    def from_mixed_dict(cls, model_name: str,  fields: dict[str, GeneralField], sortable: list[str] = [], filterable: list[str] = []) -> 'OutputModel':
        parsed = {}
        for name, field in fields.items():
            if isinstance(field, OutputField):
                parsed[name] = field
            else:
                parsed[name] = OutputField(
                    name, field, name in sortable, name in filterable)
        return cls(model_name, parsed)

    @classmethod
    def from_restx_model(cls, model: Model, sortable: list[str] = [], filterable: list[str] = []) -> 'OutputModel':
        items = {
            field_name: field_value for field_name, field_value in list(model.items())
        }
        return cls.from_mixed_dict(model.name, items, sortable, filterable)

    def validate(self, filters: dict, builder_class: type['QueryFilterFactory']) -> None:
        for key in filters.keys():
            if key in self.fields: 
                if not self.fields[key]._filterable:
                    raise ValueError(f"Filtering by {key} is not allowed")
            else: 
                self.validate_keyword(key, filters[key], builder_class)
            
    def validate_keyword(self, builder_class: type['QueryFilterFactory'], keyword: str, val: str | list[str]) -> None:
        if keyword not in builder_class.KWARGS:
            raise ValueError(f"Keyword {keyword} is not known")
        if isinstance(val, str):
            val = [val]
        for v in val:
            _ , col = builder_class.parse_sort_item(v)
            if col not in self.fields:
                raise ValueError(f"Column {col} is not known")
            if not self.fields[col]._sortable:
                raise ValueError(f"Sorting by {col} is not allowed")
        
            