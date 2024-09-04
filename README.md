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

### Documentation details

Full documentation reference: https://www.npmjs.com/package/qs
Result of parsing can be returned as root object if needed, but default implementation is to return a dictionary.

#### Not supported
Parser:
- `plainObjects`
- `ignoreQueryPrefix` - always `False`, query is always considered without prefix
- `Strict null handling`


Stringifier:
- custom `encoder` and `decoder` functions
- `sorting` of keys
- `filtering` of keys

#### Additional support
- parsing `primitive` values: `int`, `float` are represented as `decimal.Decimal`, bool-like values are represented as `bool` whatever the case they are in, however this can be processed strictly using `primitive_strict` option, null-like values are represented as `None`

#### Modifications:
Parser:
- `sparse arrays` are represented as dictionaries with keys as indexes
- `undefined` values are represented as strings `'undefined'`
- queries such as `a` without `=` are considered as non-value and thus are not included in the result