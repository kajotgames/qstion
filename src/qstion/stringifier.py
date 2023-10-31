from .base import QS, QsNode


class QsStringifier(QS):

    @property
    def qs(self):
        pass

    def stringify(self, data: dict) -> str:
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
        for item in data:
            self._qs_tree[item] = QsNode.load(
                item, 
                data[item], 
                parse_arrays=self._parse_arrays,
                depth=self._max_depth)


def stringify(
        data: dict,
        depth: int = 5,
        parameter_limit: int = 1000,
        allow_dots: bool = False,
        allow_sparse: bool = False,
        array_limit: int = 20,
        parse_arrays: bool = False,
        allow_empty: bool = False,
        comma: bool = False,
) -> str:
    pass
