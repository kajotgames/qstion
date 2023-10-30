from .base import QS


class QsStringifier(QS):
    _qs: str = None

    def __init__(self, data: dict, **kw):
        super().__init__(**kw)
        query_args = []
        for k, v in data.items():
            query_args.extend(self._stringify_arg(k, v))
        self._process(query_args)

    def _stringify_arg(self, k, v):
        pass

    def _process(self, query_args):
        pass

    @property
    def qs(self):
        return self._qs

    @classmethod
    def stringify(cls, data: dict, **kw) -> str:
        """
        Process a dictionary into a query string

        Args:
            data (dict): dictionary to process
            depth (int): max depth of nested objects
            - e.g. depth=1 : {'a': {'b': 'c'}} -> a[b]=c
            parameter_limit (int): max number of parameters to parse (in keyword count)
            allow_dots (bool): allow dot notation
            - e.g. {'a': {'b': 'c'}} -> a.b=c
            allow_sparse (bool): allow sparse arrays
            - e.g. {'a': [,'b',,'c']} -> a[1]=b&a[5]=c
            array_limit (int): max number of elements in array
            if limit is reached, array is converted to object
            parse_arrays (bool): parse array values as or keep object notation
            comma (bool): allow comma separated values
            - e.g. {'a': ['b', 'c']} -> a=b,c

        Returns:    
            str: query string
        """
        return cls(**kw).qs


def stringify(data: dict, **kw):
    return QsStringifier(**kw).stringify(data)
