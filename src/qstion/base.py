class QS:
    _depth: int = 5
    _depth: int = 5
    _parameter_limit: int = 1000
    _allow_dots: bool = False
    _allow_sparse: bool = False
    _array_limit: int = 20
    _parse_arrays: bool = False
    _allow_empty: bool = False
    _comma: bool = False

    def __init__(
            self,
            depth: int = 5,
            parameter_limit: int = 1000,
            allow_dots: bool = False,
            allow_sparse: bool = False,
            array_limit: int = 20,
            parse_arrays: bool = False,
            allow_empty: bool = False,
            comma: bool = False,
    ):
        """
        Args:
            args (list): list of arguments to parse
            depth (int): max depth of nested objects
            - e.g. depth=1 : a[b]=c -> {'a': {'b': 'c'}}
            - depth=1 : a[b][c]=d -> {'a': { '['b']['c']' : 'd'}}
            parameter_limit (int): max number of parameters to parse (in keyword count)
            allow_dots (bool): allow dot notation
            - e.g. a.b=c -> {'a': {'b': 'c'}}
            allow_sparse (bool): allow sparse arrays
            - e.g. a[1]=b&a[5]=c -> {'a': [,'b',,'c']}
            array_limit (int): max number of elements in array
            if limit is reached, array is converted to object
            parse_arrays (bool): parse array values as or keep object notation
            comma (bool): allow comma separated values
            - e.g. a=b,c -> {'a': ['b', 'c']}
        """
        self._max_depth = depth
        self._parameter_limit = parameter_limit
        self._allow_dots = allow_dots
        self._allow_sparse = allow_sparse
        self._array_limit = array_limit
        self._parse_arrays = parse_arrays
        self._allow_empty = allow_empty
        self._comma = comma
