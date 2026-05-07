# pyparsing API Guide

pyparsing is a pure-Python parser combinator library. You build grammars by composing
`ParserElement` objects using operators and helper functions. This guide covers the
core API features relevant to this problem.

---

## 1. Core Token Elements

### `Word(init_chars, body_chars=None, min=1, max=0, exact=0)`
Matches a sequence of characters.
- If only `init_chars` is given, all characters in the token must be from that set.
- If `body_chars` is also given, the first character must be from `init_chars` and
  subsequent characters from `body_chars`.
- `min` and `max` restrict token length (default: no upper limit).

```python
from pyparsing import Word, alphas, alphanums, nums

identifier = Word(alphas, alphanums + '_')
# matches: "hello", "x1", "foo_bar"
# does NOT match: "1hello" (starts with digit)

integer = Word(nums)
# matches: "123", "0", "99"

word_any = Word(alphas)
result = word_any.parse_string("hello")
# result[0] == "hello"
```

**Invariant**: `Word(init, body).parse_string(s)` succeeds for any `s` where `s[0] in init`
and all `s[1:]` characters are in `body`.

---

### `Literal(match_string)`
Matches an exact string.

```python
from pyparsing import Literal

comma = Literal(",")
result = comma.parse_string(",")
# result[0] == ","
```

---

### `Keyword(match_string)`
Like `Literal`, but will not match if the keyword is a substring of a longer word.

```python
from pyparsing import Keyword

kw_if = Keyword("if")
kw_if.parse_string("if")   # succeeds
# kw_if.parse_string("ifdef")  # fails (it's a substring)
```

---

### `Regex(pattern, flags=0)`
Matches a regular expression pattern.

```python
from pyparsing import Regex

float_num = Regex(r"\d+\.\d*")
result = float_num.parse_string("3.14")
# result[0] == "3.14"

# Regex with * quantifier can match empty string (mayReturnEmpty=True)
opt_digits = Regex(r"\d*")
result = opt_digits.parse_string("")
# result[0] == ""
```

**mayReturnEmpty**: A Regex element has `mayReturnEmpty=True` if the pattern can match
an empty string (uses `*` or `?` quantifiers at the top level).

---

### `QuotedString(quote_char, esc_char=None, esc_quote=None, multiline=False, unquote_results=True, convert_whitespace_escapes=True)`
Matches a string delimited by quoting characters.

**Parameters**:
- `quote_char`: The opening (and closing) delimiter.
- `esc_char`: If specified, this character escapes the next character inside the quoted string.
  The escape sequence `esc_char + X` is unquoted to just `X` (the esc_char is consumed).
- `esc_quote`: A two-character sequence that represents a literal quote inside the string.
  For SQL-style `""` escaping.
- `multiline`: If `True`, quoted strings can span multiple lines.
- `unquote_results`: If `True` (default), return the contents without the enclosing quotes
  and with escape sequences processed.
- `convert_whitespace_escapes`: If `True` (default), convert `\t`, `\n`, `\r`, `\f` to
  their actual whitespace characters.

**Escape sequence invariants** (when `esc_char` is set):
- `esc_char + X` → `X` (the esc_char is stripped, leaving only the escaped character).
- `esc_char + quote_char` → `quote_char` (allows including the quote char in the string).
- `esc_char + esc_char` → `esc_char` (allows including a literal esc_char).

```python
from pyparsing import QuotedString

# Basic usage
qs = QuotedString('"')
result = qs.parse_string('"hello world"')
assert result[0] == "hello world"

# With esc_char (backslash escape)
qs_esc = QuotedString('"', esc_char='\\')
result = qs_esc.parse_string('"say \\"hello\\""')
# The \" inside is escaped → result[0] == 'say "hello"'

result2 = qs_esc.parse_string('"a\\xb"')
# \x → x (esc_char consumed, escaped char preserved)
assert result2[0] == "axb"

result3 = qs_esc.parse_string('"abc\\def"')
# \d → d (backslash stripped, 'd' preserved)
assert result3[0] == "abcdef"

# With esc_quote (SQL-style doubled-quote)
qs_sql = QuotedString('"', esc_quote='""')
result = qs_sql.parse_string('"say ""hello"""')
assert result[0] == 'say "hello"'
```

**Key invariant**: For `QuotedString('"', esc_char='\\')`, the result of parsing
`'"' + content + '"'` where content contains `'\x'` sequences should have all `\`
stripped, leaving only `x`. The backslash is never preserved in the output.

---

## 2. Combinator Operators

### `And (+)` — Sequence
Combines two elements that must match in order.

```python
from pyparsing import Word, alphas, nums

name_age = Word(alphas) + Word(nums)
result = name_age.parse_string("alice 30")
# result.as_list() == ["alice", "30"]
```

---

### `MatchFirst (|)` — First-Match
Tries alternatives left to right; returns the first that matches.

```python
from pyparsing import Literal

# | is first-match (not longest-match)
expr = Literal("ab") | Literal("abcd")
result = expr.parse_string("abcdef")
# result[0] == "ab"  (first match wins)
```

---

### `Or (^)` — Longest-Match
Tries all alternatives; returns the one that produces the longest match.

```python
from pyparsing import Literal

# ^ is longest-match
expr = Literal("ab") ^ Literal("abcd")
result = expr.parse_string("abcdef")
# result[0] == "abcd"  (longest match wins)
```

**Invariant**: For any ordering of alternatives in `^`, the result is always the longest
possible match, regardless of which alternative appears first.

---

### `Each (&)` — Any-Order Matching
Requires ALL given expressions to match, but accepts them in any order (unlike `+` which
requires a fixed left-to-right order).

**Invariant**: All required elements must be present. Missing any required element raises
`ParseException`. Optional elements (`Opt`) may be absent.

```python
from pyparsing import Word, Opt, alphas, nums

color = Word(alphas)
size = Word(nums)
flag = Opt(Literal("bold"), default="normal")

# Any of these orderings will work:
spec = color & size & flag
result1 = spec.parse_string("red 10 bold")
result2 = spec.parse_string("10 bold red")
result3 = spec.parse_string("bold red 10")
# All produce the same tokens, though possibly in different order

# If flag is absent, its default is used:
result4 = spec.parse_string("red 10")
# "normal" (the default) is included in result4
```

**`Opt` (Optional) inside `Each`**:
- If the Opt's inner expression IS present in the input, it is parsed and included ONCE
  in the result. The default value does NOT appear.
- If the Opt's inner expression is NOT present, the default value is used (returned as
  part of the result).

**This is a critical invariant**:
```python
from pyparsing import Word, Opt, alphas, nums

word_expr = Word(alphas)
num_expr = Opt(Word(nums), default="MISSING")
grammar = word_expr & num_expr

# Case A: optional IS present
result = grammar.parse_string("hello 42", parse_all=True)
assert result.as_list() == ["hello", "42"]   # "MISSING" does NOT appear

# Case B: optional NOT present
result = grammar.parse_string("hello", parse_all=True)
assert result.as_list() == ["hello", "MISSING"]  # default IS returned
```

---

## 3. Repetition Elements

### `OneOrMore(expr, stop_on=None)`
Matches one or more occurrences of `expr`. Returns ALL matched tokens.

**Invariant**: If the input contains `n >= 1` matches of `expr`, the result contains
exactly `n` tokens — all occurrences, not just the last one.

```python
from pyparsing import OneOrMore, Word, alphas

words = OneOrMore(Word(alphas))
result = words.parse_string("hello world foo")
assert result.as_list() == ["hello", "world", "foo"]  # ALL 3 tokens
assert len(result) == 3
```

**Critical property** (roundtrip):
```python
items = ["a", "bb", "ccc"]
grammar = OneOrMore(Word(alphas))
result = grammar.parse_string(" ".join(items), parse_all=True)
assert result.as_list() == items  # exact list equality
```

---

### `ZeroOrMore(expr, stop_on=None)`
Like `OneOrMore`, but also accepts zero occurrences. Also returns ALL matched tokens.

```python
from pyparsing import ZeroOrMore, Word, alphas

words = ZeroOrMore(Word(alphas))

result = words.parse_string("hello world foo")
assert result.as_list() == ["hello", "world", "foo"]  # all tokens accumulated

result_empty = words.parse_string("", parse_all=True)
assert result_empty.as_list() == []
```

**Same invariant as OneOrMore**: result contains ALL matches, not just the last.

---

### Repetition with `*` syntax
```python
# Equivalent to OneOrMore
expr = Word(alphas)[1, ...]
# Equivalent to ZeroOrMore
expr = Word(alphas)[0, ...]
# Exactly 3
expr = Word(alphas)[3]
# Between 2 and 5
expr = Word(alphas)[2, 5]
```

---

## 4. `Opt (Optional)`
Optionally matches an expression. When the expression is absent, returns an empty result
or a specified default value.

```python
from pyparsing import Opt, Word, nums

# Without default: returns empty list when absent
opt_num = Opt(Word(nums))
result = opt_num.parse_string("hello", parse_all=False)
# result.as_list() == []

# With default: returns default when absent
opt_num_default = Opt(Word(nums), default=-1)
result = opt_num_default.parse_string("hello", parse_all=False)
# result.as_list() == [-1]

# When present, the matched token is returned (NOT the default)
result_present = opt_num_default.parse_string("42", parse_all=True)
# result_present.as_list() == ["42"]  (default -1 does NOT appear)
```

**Key invariant**: `Opt(expr, default=D).parse_string(s)` either returns `[matched]`
(if expr matches) OR `[D]` (if expr doesn't match and D is set) — never both.

---

## 5. `Suppress`
Removes matched tokens from results.

```python
from pyparsing import Suppress, Literal, Word, alphas

parens = Suppress("(") + Word(alphas) + Suppress(")")
result = parens.parse_string("(hello)")
assert result.as_list() == ["hello"]  # parens suppressed
```

---

## 6. `Group`
Wraps matched tokens as a nested list in the result.

```python
from pyparsing import Group, Word, alphas, nums

row = Group(Word(alphas) + Word(nums))
result = row.parse_string("alice 30")
assert result[0].as_list() == ["alice", "30"]  # nested
```

---

## 7. `Combine`
Concatenates matched tokens into a single string.

```python
from pyparsing import Combine, Word, nums

float_num = Combine(Word(nums) + "." + Word(nums))
result = float_num.parse_string("3.14")
assert result[0] == "3.14"  # joined, no spaces

# Note: adjacent=True (default) prevents internal whitespace
# float_num.parse_string("3. 14")  would raise ParseException
```

---

## 8. `Forward`
Placeholder for a grammar expression defined later. Used for recursive grammars.

```python
from pyparsing import Forward, Literal, Suppress

expr = Forward()
parens = Suppress("(") + expr + Suppress(")")
atom = Literal("x")
expr <<= atom | parens  # <<= assigns the grammar

result = expr.parse_string("(((x)))")
assert result[0] == "x"
```

**Usage**: `forward <<= expr` or `forward << expr`. The `<<=` form is recommended to
avoid operator precedence issues with `|`.

---

## 9. `infix_notation` (also `operatorPrecedence`)
Builds a grammar for expressions with operator precedence.

```python
from pyparsing import infix_notation, Word, nums, OpAssoc

integer = Word(nums)
expr = infix_notation(
    integer,
    [
        ("-", 1, OpAssoc.RIGHT),       # unary minus
        ("+", 2, OpAssoc.LEFT),        # binary addition
        ("*", 2, OpAssoc.LEFT),        # binary multiplication
    ]
)

result = expr.parse_string("1 + 2 + 3")
# result == [['1', '+', '2', '+', '3']]
# Left-associative operators collect all terms at same level into one list.
```

**Associativity**:
- `LEFT`: `a op b op c` → `[[a, op, b, op, c]]` (all terms at same level in one group)
- `RIGHT`: `a op b op c` → `[[a, op, [b, op, c]]]` (right-recursive nesting)

---

## 10. `counted_array(expr, int_expr=None)`
Parses a self-describing counted array: a leading integer `n` followed by exactly `n`
occurrences of `expr`. The leading count integer is **suppressed** from the results.

```python
from pyparsing import counted_array, Word, alphas, nums

grammar = counted_array(Word(alphas))

result = grammar.parse_string("3 hello world foo")
assert result.as_list() == ["hello", "world", "foo"]  # count "3" suppressed

result0 = grammar.parse_string("0")
assert result0.as_list() == []  # count "0" suppressed, no items

# With more items
result4 = grammar.parse_string("4 a b c d")
assert result4.as_list() == ["a", "b", "c", "d"]
assert len(result4) == 4  # exactly 4 items, NOT 5 (4+1)
```

**Critical invariant**: The result of `counted_array(expr).parse_string(n_str + " " + items)`
must:
1. Have exactly `n` tokens (the count is suppressed).
2. Contain ONLY the parsed items, NOT the leading integer `n`.
3. Satisfy `result.as_list() == [parsed_item_1, ..., parsed_item_n]`.

A count of `0` returns an empty list `[]`.

---

## 11. `DelimitedList(expr, delim=",", combine=False, min=None, max=None)`
Parses a delimited list of `expr` values.

```python
from pyparsing import DelimitedList, Word, alphas

csv_words = DelimitedList(Word(alphas))
result = csv_words.parse_string("hello, world, foo")
assert result.as_list() == ["hello", "world", "foo"]  # delimiters suppressed
```

---

## 12. `nested_expr(opener="(", closer=")", content=None)`
Parses nested balanced bracket expressions.

```python
from pyparsing import nested_expr

expr = nested_expr()
result = expr.parse_string("(a (b c) d)")
# result[0].as_list() == ['a', ['b', 'c'], 'd']
```

---

## 13. ParseResults
The object returned by all parse operations.

```python
result = grammar.parse_string("alice 30 blue")

# Access by index
result[0]  # "alice"

# Access by name (if set_results_name was used)
result["name"]  # "alice"  (if grammar used Word(alphas)("name"))

# Convert to list
result.as_list()  # ["alice", "30", "blue"]

# Convert to dict
result.as_dict()  # {"name": "alice", ...}

# Length
len(result)  # 3
```

---

## 14. Key Properties and Invariants Summary

| Feature | Property | Failure Mode |
|---------|----------|-------------|
| `OneOrMore(expr)` | Returns ALL n matches | Bug: only last match kept |
| `ZeroOrMore(expr)` | Returns ALL n matches | Bug: only last match kept |
| `Each(&)` with `Opt(e, default=D)` | If e present: D absent; if e absent: D present | Bug: D appears when e present, or D missing when e absent |
| `QuotedString(q, esc_char=c)` | `c + X` in input → `X` in result (c stripped) | Bug: `c + X` → `c` (c preserved, X dropped) |
| `counted_array(expr)` | Result has n items, no leading integer | Bug: result has n+1 items (integer included) |
| `Or (^)` | Returns longest match regardless of ordering | Bug: returns first/shortest match |
| `Opt(expr, default=D)` | Returns `[D]` when expr absent | Bug: returns `[]` (default dropped) |

---

## 15. Common Patterns

### Parsing comma-separated key=value pairs in any order:
```python
from pyparsing import Word, Opt, alphas, nums, Suppress, each

color = "color:" + Word(alphas)
size = "size:" + Word(nums)
weight = Opt("bold", default="normal")

spec = color & size & weight
```

### Parsing counted binary data:
```python
from pyparsing import counted_array, Word, hexnums

hex_byte = Word(hexnums, exact=2)
data = counted_array(hex_byte)

result = data.parse_string("3 FF 00 AB")
# result.as_list() == ["FF", "00", "AB"]
```

### Collecting all words in a sentence:
```python
from pyparsing import OneOrMore, Word, alphas

sentence = OneOrMore(Word(alphas))
result = sentence.parse_string("the quick brown fox")
# result.as_list() == ["the", "quick", "brown", "fox"]
# len(result) == 4
```
