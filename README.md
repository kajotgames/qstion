# qstion

A querystring parsing and stringifying library with some added security. 
Library was based on [this](https://www.npmjs.com/package/qs?activeTab=readme) js library.

## Usage 

```python
import qstion as qs

x = qs.parse('a=c')
assert x == {'a': 'c'}

x_str = qs.stringify(x)
assert x_str == 'a=c'
```

### Parsing strings

**qstion** (as well as **qs** in js) allows you to parse string into nested objects.
    
```python
import qstion as qs

assert qs.parse('a[b][c]=1') == {'a': {'b': {'c': '1'}}}
```
There is no support for plain object options or prototype pollution.

Uri encoded strings are supported
    
```python
import qstion as qs

assert qs.parse('a%5Bb%5D=c') == {'a': { 'b': 'c' }}
```

Following options are supported:
1. `from_url` : **bool** - if `True` then `parse` will parse querystring from url using `urlparse` from `urllib.parse` module, default: `False`
```python
import qstion as qs

assert qs.parse('http://localhost:8080/?a=c', from_url=True) == {'a': 'c'}

assert qs.parse('a=c', from_url=False) == {'a': 'c'}
```
2. `delimiter` : **str**|**re.Pattern** - delimiter for parsing, default: `&`
```python
import qstion as qs

assert qs.parse('a=c&b=d', delimiter='&') == {'a': 'c', 'b': 'd'}

assert qs.parse('a=c;b=d,c=d', delimiter='[;,]') == {'a': 'c', 'b': 'd', 'c': 'd'}
```
3. `depth` : **int** - maximum depth for parsing, default: `5`
```python
import qstion as qs

assert qs.parse('a[b][c][d][e][f][g][h][i]=j', depth=5) == {'a': {'b': {'c': {'d': {'e': {'f': {'[g][h][i]': 'j'}}}}}}}

assert qs.parse('a[b][c][d][e][f][g][h][i]=j', depth=1) == {'a': {'b': {'[c][d][e][f][g][h][i]': 'j'}}}
```

4. `parameter_limit` : **int** - maximum number of parameters to parse, default: `1000`
```python
import qstion as qs

assert qs.parse('a=b&c=d&e=f&g=h&i=j&k=l&m=n&o=p&q=r&s=t&u=v&w=x&y=z', parameter_limit=5) == {'a': 'b', 'c': 'd', 'e': 'f', 'g': 'h', 'i': 'j'}
```

5. `allow_dots` : **bool** - if `True` then dots in keys will be parsed as nested objects, default: `False`
```python
import qstion as qs

assert qs.parse('a.b=c', allow_dots=True) == {'a': {'b': 'c'}}
```
6. `parse_arrays`: **bool** - if `True` then arrays will be parsed, default: `False`
```python
import qstion as qs

assert qs.parse('a[]=b&a[]=c', parse_arrays=True) == {'a': {0: 'b', 1: 'c'}}

assert qs.parse('a[0]=b&a[1]=c', parse_arrays=False) == {'a': {'0': 'b', '1': 'c'}}
```

7. `array_limit` : **int** - maximum number of elements in array to keep array notation (only used with combination of argument `parse_arrays`), default: `20`
```python
import qstion as qs

assert qs.parse('a[]=b&a[]=c&', parse_arrays=True) == {'a': {0: 'b', 1: 'c'}}

assert qs.parse('a[0]=b&a[1]=c&', array_limit=1, parse_arrays=True) == {'a': {'0': 'b', '1': 'c'}}
```

8. `allow_empty` : **bool** - if `True` then empty values and keys are accepted, default: `False`
```python
import qstion as qs

assert qs.parse('a=&b=', allow_empty=True) == {'a': '', 'b': ''}

assert qs.parse('a[]=&b[]=', allow_empty=True) == {'a': {'': ''}, 'b': {'': ''}}
```

9. `charset` : **str** - charset to use when decoding uri encoded strings, default: `utf-8`
```python
import qstion as qs

assert qs.parse('a=%A7', charset='iso-8859-1') == {'a': '§'}

assert qs.parse('a=%C2%A7', charset='utf-8') == {'a': '§'}
```

10. `charset_sentinel` : **bool** - if `True` then, if `utf8=✓` arg is included in querystring, then charset will be deduced based on encoding of '✓' character (recognizes only `utf8` and `iso-8859-1`), default: `False`
```python
import qstion as qs

assert qs.parse('a=%C2%A7&utf8=%E2%9C%93',charset='iso-8859-1', charset_sentinel=True) == {'a': '§'}

assert qs.parse('a=%A7&utf8=%26%2310003', charset='utf-8', charset_sentinel=True) == {'a': '§'}
```

11. `interpret_numeric_entities` : **bool** - if `True` then numeric entities will be interpreted as unicode characters, default: `False`
```python
import qstion as qs

assert qs.parse('a=%26%2310003',charset='iso-8859-1', interpret_numeric_entities=True) == {'a': '✓'}
```

12. `parse_primitive`: **bool** - if `True` then primitive values will be parsed in their appearing types, default: `False`
```python
import qstion as qs

assert qs.parse('a=1&b=2&c=3', parse_primitive=True) == {'a': 1, 'b': 2, 'c': 3}

assert qs.parse('a=true&b=false&c=null', parse_primitive=True) == {'a': True, 'b': False, 'c': None}
```

13. `primitive_strict`: **bool** - if `True` then primitive values of `bool` and `NoneType` will be parsed to reserved strict keywords (used only if `parse_primitive` is `True`), default: `True`
```python
import qstion as qs

assert qs.parse('a=true&b=false&c=null&d=None', parse_primitive=True, primitive_strict=True) == {'a': True, 'b': False, 'c': None, 'd': 'None'}

assert qs.parse('a=True&b=False&c=NULL', parse_primitive=True, primitive_strict=True) == {'a': 'True', 'b': 'False', 'c': 'NULL'}

assert qs.parse('a=True&b=False&c=NULL', parse_primitive=True, primitive_strict=False) == {'a': True, 'b': False, 'c': None}
```

14. `comma`: **bool** - if `True`, then coma separated values will be parsed as multiple separate values instead of string, default: `False`
```python
import qstion as qs

assert qs.parse('a=1,2,3', comma=True, parse_primitive=True) == {'a': [1, 2, 3]}
```

### Stringifying objects

**qstion** (as well as **qs** in js) allows you to stringify objects into querystring.
    
```
import qstion as qs

assert qs.stringify({'a': 'b'}) == 'a=b'
```

Following options are supported:
1. `allow_dots` : **bool** - if `True` then nested keys will be stringified using dot notation instead of brackets, default: `False`
```python
import qstion as qs

assert qs.stringify({'a': {'b': 'c'}}, allow_dots=True) == 'a.b=c'
```

2. `encode` : **bool** - if `True` then keys and values will be uri encoded (with default `charset`), default: `True`
```python
import qstion as qs

assert qs.stringify({'a[b]': 'b'}, encode=False) == 'a[b]=b'

assert qs.stringify({'a[b]': 'b'}, encode=True) == 'a%5Bb%5D=b'
```

3. `charset` : **str** - charset to use when encoding uri strings, default: `utf-8` (if `encode` is `True`), note that un-encodable characters will be encoded using their xml numeric entities
```python
import qstion as qs

assert qs.stringify({'a': '§'}, charset='iso-8859-1') == 'a=%A7'

assert qs.stringify({'a': '☺'}, charset='iso-8859-1') == 'a=%26%2312850'
```

4. `charset_sentinel` : **bool** - if `True` then, `utf8=✓` will be added to querystring to indicate that charset based on encoding of '✓' character (recognizes only `utf8` and `iso-8859-1`), default: `False`
```python
import qstion as qs

assert qs.stringify({'a': '§'}, charset='iso-8859-1', charset_sentinel=True) == 'a=%A7&utf8=%E2%9C%93'
```


5. `delimiter` : **str** - delimiter for stringifying, default: `&`
```python
import qstion as qs

assert qs.stringify({'a': 'b', 'c': 'd'}, delimiter='&') == 'a=b&c=d'

assert qs.stringify({'a': 'b', 'c': 'd'}, delimiter=';') == 'a=b;c=d'
``` 

6. `encode_values_only` : **bool** - if `True` then only values will be encoded, default: `False` (this option is overridden when `encode` is `True`)
```python

import qstion as qs

assert qs.stringify({'a': {'b': '☺'}}, encode_values_only=True, charset='iso-8859-1') == 'a[b]=%26%2312850'
```

7. `array_format` : **str** - format for array notation, options: 'brackets','indices', 'repeat', 'comma', default: 'indices'
```python
import qstion as qs

assert qs.stringify({'a': {1: 'b', 2: 'c'}}, array_format='brackets') == 'a[]=b&a[]=c'

assert qs.stringify({'a': {1: 'b', 2: 'c'}}, array_format='indices') == 'a[1]=b&a[2]=c'

assert qs.stringify({'a': {1: 'b', 2: 'c'}}, array_format='repeat') == 'a=b&a=c'

assert qs.stringify({'a': {1: 'b', 2: 'c'}}, array_format='comma') == 'a=b,c'
```

8. `sort` : **bool** - if `True` then keys will be sorted alphabetically, default: `False`
```python
import qstion as qs

assert qs.stringify({'x': 'y', 'a': 'b'}, sort=True) == 'a=b&x=y'
```

9. `sort_reverse` : **bool** - if `True` then keys will be sorted (if `sort` is `True`) in reverse order, default: `False`
```python
import qstion as qs

assert qs.stringify({'x': 'y', 'a': 'b'}, sort=True, sort_reverse=True) == 'x=y&a=b'
```

10. `filter` : **list[str]** - list of keys to filter, default: `None`
```python
import qstion as qs

assert qs.stringify({'a': 'b', 'c': 'd'}, filter=['a']) == 'a=b'
```
