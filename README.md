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

### Parsing objects

**qstion** (as well as **qs** in js) allows you to parse objects with nested objects.
    
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
3. `depth` :
