# parso Tokenizer API Reference

## Overview

parso 0.8.6 is a Python 2/3 parser with error-recovery support, extracted from the Jedi IDE toolkit. At its core, parso converts Python source text into a parse tree of `Leaf` and `Node` objects. The main entry point is `parso.parse()`.

---

## 1. Parsing API

### `parso.parse(code, **kwargs)`

Parse a string of Python source code and return the root `Module` node.

```python
import parso

module = parso.parse('x = 1 + 2\n')
module = parso.parse('result = a // b\n', version='3.10')
module = parso.parse('if (n := 10) > 5:\n    pass\n', version='3.8')
```

**Parameters:**
- `code` (str): Python source code to parse.
- `version` (str, optional): Python version string, e.g. `'3.8'`, `'3.10'`, `'3.12'`. Defaults to the running Python version. Determines which grammar and tokenizer rules apply.
- `error_recovery` (bool, optional): If `True` (default), the parser attempts to recover from syntax errors.

**Returns:** A `Module` node (subclass of `BaseNode`).

**Important:** The `version` parameter controls which tokenizer patterns are active. For example, the walrus operator `:=` was introduced in Python 3.8, so code using `:=` must be parsed with `version='3.8'` or higher.

---

## 2. Round-Trip Guarantee

parso is designed for **lossless round-trip parsing**: `module.get_code()` must reproduce the original source exactly, including all whitespace, comments, and formatting.

```python
import parso

code = 'x = rb"hello"\n'
module = parso.parse(code)
assert module.get_code() == code  # must hold for any valid Python code
```

This property can be used to verify that the tokenizer correctly identified every token without misclassifying or merging/splitting tokens.

---

## 3. Token Types

The tokenizer (`parso/python/tokenize.py`) produces tokens of these types (defined in `PythonTokenTypes`):

| Type | Description | Examples |
|---|---|---|
| `STRING` | String literal | `'hello'`, `b"data"`, `rb'raw'`, `r"\n"` |
| `NUMBER` | Numeric literal | `42`, `3.14`, `0xFF`, `1_000` |
| `NAME` | Identifier or keyword | `foo`, `def`, `return`, `x` |
| `OP` | Operator or punctuation | `+`, `**`, `//`, `//=`, `:=`, `...`, `(`, `)` |
| `NEWLINE` | Statement-terminating newline | `\n` at end of logical line |
| `INDENT` | Indentation increase | (empty string) |
| `DEDENT` | Indentation decrease | (empty string) |
| `COMMENT` | Comment (stored as prefix) | `# this is a comment` |
| `ENDMARKER` | End of file | (empty string) |
| `ERRORTOKEN` | Unrecognised character | any single unexpected char |
| `FSTRING_START` | Opening of f-string | `f"`, `f'`, `f"""`, `F"` |
| `FSTRING_STRING` | Literal text inside f-string | `hello `, ` world` |
| `FSTRING_END` | Closing quote of f-string | `"`, `'`, `"""`, `'''` |

---

## 4. String Literal Prefixes

Python supports several string prefix characters. parso recognises all of them:

### Single-character prefixes
| Prefix | Meaning | Example |
|---|---|---|
| `b` or `B` | Bytes literal | `b'hello'`, `B"data"` |
| `r` or `R` | Raw string (backslashes literal) | `r'\n'`, `R"\t"` |
| `u` or `U` | Unicode string (Python 2 compat) | `u'text'`, `U"text"` |
| `f` or `F` | F-string (formatted string) | `f"{x}"`, `F"{name}"` |

### Two-character prefixes
| Prefix | Meaning | Example |
|---|---|---|
| `rb` or `br` (any case) | Raw bytes | `rb'data\n'`, `br"raw"`, `RB'...'` |
| `fr` or `rf` (any case) | Raw f-string | `fr"{path}"`, `rf"{name}\n"` |

**Key point:** All permutations and mixed-case variants are valid. `rb`, `Rb`, `rB`, `RB`, `br`, `bR`, `Br`, `BR` are all equivalent and must be tokenized as a single `STRING` token that starts with the two-letter prefix.

### String quote styles
Strings can use single quotes (`'`), double quotes (`"`), triple-single (`'''`), or triple-double (`"""`). Triple-quoted strings can span multiple lines.

---

## 5. Multi-Character Operators

The tokenizer uses a priority-ordered regex to recognise operators. Longer patterns are matched first:

| Operator | Type | Version |
|---|---|---|
| `**=` | Augmented power-assignment | all |
| `**` | Power | all |
| `>>=` | Augmented right-shift | all |
| `>>`| Right-shift | all |
| `<<=` | Augmented left-shift | all |
| `<<` | Left-shift | all |
| `//=` | Augmented floor-division | all |
| `//` | Floor division | all |
| `->` | Return annotation arrow | all |
| `:=` | Walrus (named expression) | Python >= 3.8 |
| `...` | Ellipsis literal | all (as OP, not NUMBER) |
| `==`, `!=`, `<=`, `>=` | Comparison operators | all |
| `/=`, `*=`, `+=`, `-=`, etc. | Augmented assignment | all |

**Key points:**
- `//` (floor division) is a **single OP token** with string `'//'`, not two `/` tokens.
- `//=` is a **single OP token** with string `'//='`.
- `...` (ellipsis) is an **OP token** with string `'...'`, not a NUMBER.
- `:=` (walrus) is only recognised as a single token when `version >= '3.8'`. In earlier versions, `:` and `=` are two separate OP tokens.

---

## 6. Leaf Node Access

After parsing, you can traverse the parse tree to access individual leaf nodes:

```python
import parso

module = parso.parse('x = 1 + 2\n')

# Get the first/last leaf
first = module.get_first_leaf()   # Name 'x'
last = module.get_last_leaf()     # EndMarker ''

# Iterate all leaves in order
def all_leaves(node):
    if hasattr(node, 'children'):
        for child in node.children:
            yield from all_leaves(child)
    else:
        yield node

for leaf in all_leaves(module):
    print(leaf.type, repr(leaf.value), leaf.start_pos, leaf.end_pos)
```

### Leaf attributes

Every leaf has:
- `leaf.value` (str): The token text.
- `leaf.start_pos` (tuple): `(line, column)` 1-indexed line, 0-indexed column.
- `leaf.end_pos` (tuple): Position after the last character.
- `leaf.prefix` (str): Whitespace/comments that precede this token.
- `leaf.get_code(include_prefix=True)`: Returns `prefix + value`.

### Specific leaf types

```python
from parso.python.tree import String, Number, Operator, Name, Keyword
from parso.python.tree import FStringStart, FStringString, FStringEnd

# Check leaf type
for leaf in all_leaves(module):
    if isinstance(leaf, String):
        print("String:", leaf.value)
    elif isinstance(leaf, Operator):
        print("Operator:", leaf.value)
```

---

## 7. F-String Tokenization

F-strings are tokenized into three token types:
1. `FSTRING_START`: The prefix + opening quote(s), e.g. `f"`, `f'''`.
2. `FSTRING_STRING`: Literal text segments between expressions.
3. `FSTRING_END`: The closing quote(s), e.g. `"`, `'''`.

Expression content (inside `{...}`) is tokenized with normal Python token types.

```python
module = parso.parse('f"hello {name:20s} world"\n')
# Tokens: FSTRING_START 'f"', FSTRING_STRING 'hello ', OP '{',
#         NAME 'name', OP ':', FSTRING_STRING '20s', OP '}',
#         FSTRING_STRING ' world', FSTRING_END '"'
```

**Format specifiers:** Content after `:` inside `{...}` (the format spec) is tokenized as `FSTRING_STRING`, not as expression tokens. For example, in `f"{value:.2f}"`, the `.2f` is a single `FSTRING_STRING` leaf, not `.` + `2` + `f` as separate tokens.

**Nested expressions in format specs:** `f"{x:{width}}"` — the `{width}` inside the format spec is a nested expression with its own `FSTRING_STRING` / expression tokens.

---

## 8. Indent and Dedent

parso emits virtual `INDENT` and `DEDENT` tokens to represent indentation changes:

```python
module = parso.parse('def f():\n    pass\n')
# Tokens: NAME 'def', NAME 'f', OP '(', OP ')', OP ':', NEWLINE '\n',
#         INDENT '', NAME 'pass', NEWLINE '\n', DEDENT '', ENDMARKER ''
```

- `INDENT` tokens have an empty string value and are emitted when indentation increases.
- `DEDENT` tokens have an empty string value and are emitted when indentation decreases.
- `ERROR_DEDENT` is emitted when an unexpected dedent occurs (error recovery).

---

## 9. Version-Specific Behaviour

Certain tokens or constructs are only recognised in specific Python versions:

| Feature | Minimum Version | Tokenizer Behaviour |
|---|---|---|
| Walrus operator `:=` | 3.8 | Recognised as single OP `':='`; below 3.8, split into `':'` + `'='` |
| f-strings | 3.6 | Recognised; below 3.6, `f"..."` is parsed as NAME + STRING |
| Positional-only params `/` | 3.8 | Recognised as OP |
| Match statement | 3.10 | Grammar-level; tokenizer not affected |

```python
# Walrus in 3.8 -> single ':=' token
m38 = parso.parse('(x := 5)\n', version='3.8')

# In 3.7, ':=' becomes ':' + '='
m37 = parso.parse('(x := 5)\n', version='3.7')
```

---

## 10. Round-Trip Testing Pattern

A reliable way to detect tokenizer bugs is to use the round-trip property:

```python
import parso

def check_roundtrip(code, version=None):
    kwargs = {'version': version} if version else {}
    module = parso.parse(code, **kwargs)
    recovered = module.get_code()
    assert recovered == code, f"Expected {code!r}, got {recovered!r}"

# Examples that test specific tokenizer features
check_roundtrip('x = a // b\n')           # floor division
check_roundtrip('x //= 3\n')              # augmented floor division
check_roundtrip("s = rb'bytes'\n")        # byte-raw string prefix
check_roundtrip("s = br\"bytes\"\n")      # alternate byte-raw prefix
check_roundtrip('f"{x:.2f}"\n')           # f-string with format spec
check_roundtrip('(n := 5)\n', '3.8')      # walrus operator in 3.8
```
