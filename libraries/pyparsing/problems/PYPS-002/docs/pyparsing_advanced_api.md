# pyparsing 3.3.2 — Advanced API Reference

This document covers ParseResults named-result handling, SkipTo, NotAny, and Combine.

## ParseResults — Named Results and list_all_matches

`ParseResults` is the return type from `parse_string()` and related methods. It supports
both list indexing and named-result (dictionary) access.

### set_results_name / Shorthand

```python
# Using set_results_name
integer("year")  # shorthand for integer.set_results_name("year")
integer.set_results_name("year", list_all_matches=True)
```

### list_all_matches

By default, when a results name is assigned to multiple tokens, only the **last** token
is accessible by name. To collect **all** tokens under a name, use `list_all_matches=True`:

```python
from pyparsing import Word, nums, alphas

num = Word(nums)
grammar = num("val") + Word(alphas) + num("val")
result = grammar.parse_string("123 abc 456")
result["val"]  # → "456" (only last match)

# With list_all_matches=True:
num_lam = Word(nums).set_results_name("val", list_all_matches=True)
grammar2 = num_lam + Word(alphas) + num_lam
result2 = grammar2.parse_string("123 abc 456")
result2["val"]  # → ["123", "456"] (all matches as a list)
```

**Property**: If `list_all_matches=True` is set on a results name, then accessing
`result[name]` returns a **list** of all matched values, not just the last one.

**Property (combining results)**: When two `ParseResults` are combined (via `+` operator
internally), the `list_all_matches` attribute is preserved for ANY name that has it set
in EITHER of the two results being combined.

```python
# The grammar: label + num_lam + num_lam
# After parsing "abc 123 456":
# result["val"] == ["123", "456"]  # both nums accessible
```

### ParseResults as a List and Dictionary

```python
result = grammar.parse_string("2024/03/15")
list(result)         # → ['2024', '/', '03', '/', '15']
result["year"]       # → '2024'
result.get("hour", "N/A")  # → 'N/A' (default for missing name)
"month" in result    # → True (checks named results)
```

## SkipTo — Skip Until Target Expression

`SkipTo(expr, include=False, ignore=None, fail_on=None)` matches all text up to
(but not including, by default) the first match of `expr`.

```python
from pyparsing import SkipTo, Literal, StringEnd

# Skip to a delimiter
SkipTo('|').parse_string("hello|world")       # → ['hello']
SkipTo('|').parse_string("|world")            # → ['']  (empty string before |)
SkipTo(StringEnd()).parse_string("hello")     # → ['hello']  (skip to end)
SkipTo(StringEnd()).parse_string("")          # → ['']   (empty skip to end)
```

**Property**: `SkipTo(StringEnd()).parse_string(s)` always succeeds and returns `[s]`
for any string `s` (including empty string).

**Property**: `SkipTo(expr).parse_string(s)` returns all text before the first
occurrence of `expr` in `s`. If `expr` matches at the very beginning, returns `['']`.
If `expr` matches at the very end of `s`, returns all text before the last position.

### include=True

When `include=True`, the matched target expression is also consumed and included in the
result:

```python
SkipTo(Literal("|"), include=True).parse_string("hello|world")
# → ['hello', '|']
```

## NotAny — Negative Lookahead

`NotAny(expr)` (also written as `~expr`) is a **zero-width** assertion that succeeds
only when `expr` does **NOT** match at the current position. It does not consume any
input.

```python
from pyparsing import NotAny, Word, alphas, nums, Keyword

# Use NotAny to prevent keywords from being parsed as identifiers
AND = Keyword("AND")
ident = ~AND + Word(alphas)

ident.parse_string("hello")   # → ['hello']   (not AND, so ident matches)
ident.parse_string("AND")     # → ParseException (AND is blocked by ~AND)
```

**Property**: `~expr + expr2` successfully parses `s` if and only if `expr` does NOT
match at the start of `s` (after whitespace skip).

**Property**: `~Word(nums) + Word(alphas)` should parse any pure-alpha string `s`:
the `~Word(nums)` lookahead succeeds because digits are NOT found, allowing `Word(alphas)`.

**Property**: `~Word(nums) + Word(alphas)` should FAIL on any numeric string `s`:
the `~Word(nums)` lookahead fails because digits ARE found, blocking the parse.

```python
# Correctness invariant:
# For any string s:
# parse(~expr + rest, s) succeeds  ⟺  expr does NOT match at start of s
# parse(~expr + rest, s) fails     ⟺  expr DOES match at start of s
```

## Combine — Concatenate Matched Tokens

`Combine(expr, join_string="", adjacent=True)` runs `expr` and then joins all matched
tokens into a single string, using `join_string` as the separator (default: empty string,
meaning no separator).

```python
from pyparsing import Combine, Word, nums

# Parse a floating-point number
real = Combine(Word(nums) + "." + Word(nums))
real.parse_string("3.1416")    # → ['3.1416']  (tokens joined: "3" + "." + "1416")
real.parse_string("3. 1416")   # → ParseException (adjacent=True: no space allowed)

# With adjacent=False, spaces are allowed
real2 = Combine(Word(nums) + "." + Word(nums), adjacent=False)
real2.parse_string("3. 1416")  # → ['3.1416']
```

**Property**: `Combine(expr).parse_string(s)[0]` equals the concatenation of all tokens
matched by `expr` in `s` (joined with `join_string`, default empty string "").

**Property**: `Combine(Word(nums) + Literal(".") + Word(nums)).parse_string("3.14")[0]`
equals `"3.14"` (no spaces in the result).

**Property**: The result of `Combine` is always a **single string** containing all
tokens from the matched expression joined with `join_string`. With the default
`join_string=""`, there are **no spaces** in the result.

```python
# join_string="" (default): tokens concatenated without separator
Combine(Word(alphas) + Word(nums)).parse_string("abc123")[0]  # → "abc123"

# join_string=" ": tokens joined with a space
Combine(Word(alphas) + Word(nums), join_string=" ").parse_string("abc123")[0]  # → "abc 123"
```
