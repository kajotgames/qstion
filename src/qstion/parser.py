import typing as t
import urllib.parse as up
import re



t_Delimiter = t.Union[str, t.Pattern[str]]

class ArrayItem:
    _index: int | None = None
    _value: t.Any

    def __init__(self, idx, val) -> None:
        self._index = idx
        self._value = val

    @property
    def index(self) -> int | None:
        return self._index
    
    @index.setter
    def index(self, idx: int) -> None:
        self._index = idx

    @property
    def value(self) -> t.Any:
        return self._value
    
    @value.setter
    def value(self, val: t.Any) -> None:
        self._value = val

    def __repr__(self) -> str:
        return str(self._value)
    


class ArrayParse:
    _limit: int = 20

    @classmethod
    def process(cls, notation: list, array: list[ArrayItem], max_limit: int = 20) -> list:
        """
        Performs a syntax check on the key. works as state machine.
        """
        cls._limit = max_limit
        return cls.process_notation(notation, array)

    @classmethod 
    def process_notation(cls, notation: list[str], val: t.Any) -> ArrayItem:
        """
        Parses array notation recursively.
        """
        if not notation:
            return val 
        current = notation[0]        
        if current.isdigit():
            if int(current) > cls._limit:
                raise IndexError('Array limit reached')
            return [ArrayItem(int(current), cls.process_notation(notation[1:], val))]
        elif current == '':
            data = cls.process_notation(notation[1:], val)
            if not isinstance(data, list):
                data = [ArrayItem(None, data)]
            return data
        else:
            return {current: cls.process_notation(notation[1:], val)}
            

class QsParser:
    _args: dict[str|int, str | int | dict ] = None
    _depth: int = 5
    _parameter_limit: int = 1000
    _allow_dots: bool = False
    _allow_sparse: bool = False
    _array_limit: int = 20
    _parse_arrays: bool = False
    _allow_empty: bool = False
    _comma: bool = False

    # maybe use classic up.parse_qs instead of this class
    def __init__(
            self, 
            args: list[str],
            depth: int,
            parameter_limit: int,
            allow_dots: bool,
            allow_sparse: bool,
            array_limit: int,
            parse_arrays: bool,
            allow_empty: bool,
            comma: bool,
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
        self._args = {}
        self._max_depth = depth
        self._parameter_limit = parameter_limit
        self._allow_dots = allow_dots
        self._allow_sparse = allow_sparse
        self._array_limit = array_limit
        self._parse_arrays = parse_arrays
        self._allow_empty = allow_empty
        self._comma = comma
        for arg in args:
            k, v = arg.split('=')
            self._parse_arg(k, v)

    @property
    def args(self) -> dict[str, str]:
        """
        Returns parsed arguments.
        """
        return self._args

    @classmethod
    def parse(
        cls, 
        url: str, 
        delimiter: t_Delimiter = '&', 
        depth: int = 5, 
        parameter_limit: int = 1000,
        allow_dots: bool = False,
        allow_sparse: bool = False,
        array_limit: int = 20,
        parse_arrays: bool = False,
        allow_empty: bool = False,
        comma: bool = False,
        ) -> dict:
        """
        Creates a parser from a url.
        """
        args = []
        parsed_url = up.urlparse(url)
        query_args = re.split(delimiter, parsed_url.query)
        for arg in query_args:
            args.append(cls._unq(arg))
        return cls(args, depth, parameter_limit, allow_dots, allow_sparse, array_limit, parse_arrays, allow_empty, comma).args

    @staticmethod
    def _unq(arg: str) -> str:
        """
        Unquotes a string (removes url encoding).

        Args:
            arg (str): string to unquote

        Returns:
            str: unquoted string
        """
        arg_key, arg_val = arg.split('=')
        return f'{up.unquote(arg_key)}={up.unquote(arg_val)}'

    def _parse_arg(self, k: str, v: str) -> None:
        """
        Parses a single argument into a nested dict.
        """
        self._parse_array(k, v)
        

    def _parse_key(self, k: str) -> list:
        """
        Parses key into a list of nested keys.
        """
        # TODO add depth limit
        # TODO handle dot notation
        pass

    def _parse_dots(self, k: str) -> list | None:
        """
        Parses key with dot notation into a list of nested keys.
        """
        pass

    def _parse_array(self, k: str, v: str) -> bool:
        """
        Parses key with array notation into a list of nested keys.
        """
        if not self._parse_arrays:
            return False
        match = re.match(r'(\w+)(\[(.*)\])+', k)
        key = match.group(1)
        if not match:
            return False
        array_notation = re.findall(r'\[(.*?)\]', k)
        if not array_notation:
            return False
        if not re.match(r'\d*', array_notation[0]):
            return False
        try:
            array = ArrayParse.process(array_notation, v)
            if key not in self._args:
                self._args[key] = array
            else:
                QsParser._update_arg(self._args[key], array)
        except IndexError:
            return False    

    @staticmethod
    def _handle_type(arg: t.Any, val: t.Any) -> t.Any:
        """
        Handles type mismatch between arg and val.
        """
        if isinstance(arg, str) and isinstance(val, dict):
            # special case :
            # {b : c} being updated with {b : {d : e}}
            # -> c becomes {c : True}
            arg = {arg: True}
        # other cases must match
        if type(arg) != type(val):
            raise TypeError(f'Cannot update {type(arg)} with {type(val)}')
        return arg
    
    # TODO incomplete
    @staticmethod
    def _update_arg(arg: t.Any, val: t.Any) -> None:
        """
        Updates an existing argument recursively.
        This method is neccesarly in case of using multiple arguments with the same key nesting.
        """
        # TODO type mismatch handling not included -> types must match except this case
        arg = QsParser._handle_type(arg, val)
        if isinstance(arg, dict):
            for k, v in v.items():
                if k in arg:
                    QsParser._update_arg(arg[k], v)
                else:
                    arg[k] = v
        elif isinstance(arg, list):
            for item in val:
                if item.index is None:
                    item.index = arg[-1].index + 1 if arg else 0
                    arg.append(item)
                else:
                    # if item index is already in list, update it
                    # otherwise append it
                    if item.index in [i.index for i in arg]:
                        for array_item in arg:
                            if array_item.index == item.index:
                                QsParser._update_arg(array_item.value, item.value)
                    else:
                        arg.append(item)
                    QsParser._sort_array(arg)
        else:
            raise TypeError(f'Cannot update {type(arg)} with {type(val)}')

    @staticmethod
    def _sort_array(array: list[ArrayItem]) -> None:
        """
        Sorts array by index.
        """
        array.sort(key=lambda x: x.index)      


    def _conv_to_non_array(self) -> None:
        """
        Converts current args to non-array notation.
        """
        pass

    def _parse_brackets(self, k: str) -> list | None:
        """
        Parses key with brackets notation into a list of nested keys.
        """
        pass

if __name__ == '__main__':
    url = 'http://localhost:5000/?a[][1][][1]=b&a[][1][][0]=c&a[0][b]=c'
    print(QsParser.parse(url, parse_arrays=True))

