# Babel Numbers API — Official Documentation

Source: [Babel 2.14.0 Documentation](https://babel.pocoo.org/en/latest/api/numbers.html)

---

## `format_decimal(number, format=None, locale=LC_NUMERIC, decimal_quantization=True, group_separator=True)`

Format a number as a decimal number according to the given format.

```python
>>> from babel.numbers import format_decimal
>>> format_decimal(1.2345, locale='en_US')
'1.234'
>>> format_decimal(1.2346, locale='en_US')
'1.235'
>>> format_decimal(-1.2346, locale='en_US')
'-1.235'
>>> format_decimal(1.2345, locale='sv_SE')
'1,234'
>>> format_decimal(1.2345, locale='de')
'1,234'
```

**Parameters:**
- `number` — the number to format
- `format` — decimal number format string or `None` for locale default
- `locale` — a `Locale` object or locale identifier
- `decimal_quantization` — quantize the final output to decimal notation
- `group_separator` — bool, use grouping separator in the return value

### Significant Digit Patterns

Number format strings can use `@` and `#` to specify significant digit formatting:

- `@` — significant digit (minimum count)
- `#` — optional significant digit (up to maximum count)

Examples:
- `@@##` — 2 to 4 significant digits (minimum 2, maximum 4)
- `@@@` — exactly 3 significant digits

```python
>>> format_decimal(12345, '@@##', locale='en_US')
'12,350'
>>> format_decimal(0.00012345, '@@##', locale='en_US')
'0.00012'
>>> format_decimal(1.23, '@@##', locale='en_US')
'1.23'
>>> format_decimal(10, '@@##', locale='en_US')
'10'
>>> format_decimal(100, '@@##', locale='en_US')
'100'
```

---

## `format_currency(number, currency, format=None, locale=LC_NUMERIC, currency_digits=True, format_type='standard', decimal_quantization=True, group_separator=True)`

Format a number as a currency value.

```python
>>> from babel.numbers import format_currency
>>> format_currency(1099.98, 'USD', locale='en_US')
'$1,099.98'
>>> format_currency(1099.98, 'USD', locale='es_CO')
'US$\xa01.099,98'
>>> format_currency(1099.98, 'EUR', locale='de_DE')
'1.099,98\xa0€'
```

**Parameters:**
- `number` — the number to format
- `currency` — the currency code (e.g., `'USD'`, `'EUR'`, `'GBP'`)
- `format` — currency format string or `None` for locale default
- `locale` — a `Locale` object or locale identifier
- `currency_digits` — bool, use the currency's natural number of decimal digits
- `format_type` — the currency format type to use. One of:
  - `'standard'` — symbol format (e.g., `'$1.50'`)
  - `'accounting'` — accounting format (negative in parentheses)
  - `'name'` — long-form name with correct grammatical plural
- `decimal_quantization` — quantize the final output to decimal notation
- `group_separator` — bool, use grouping separator in the return value

### Long-form Currency Name (`format_type='name'`)

When `format_type='name'` is used, the currency is rendered as a long-form name
with the correct plural form according to Unicode CLDR plural rules.

```python
>>> format_currency(1.00, 'USD', locale='en_US', format_type='name')
'1.00 US dollar'
>>> format_currency(1.50, 'USD', locale='en_US', format_type='name')
'1.50 US dollars'
>>> format_currency(2.00, 'USD', locale='en_US', format_type='name')
'2.00 US dollars'
>>> format_currency(0.50, 'USD', locale='en_US', format_type='name')
'0.50 US dollars'
```

**Plural rules for English (en_US):**
- Singular (`'US dollar'`): exactly `1` (i.e., `n == 1`)
- Plural (`'US dollars'`): everything else (0, 0.5, 1.5, 2, 100, etc.)

The plural form is determined by the **actual numeric value** of the amount, not
by rounding. An amount of `1.50` is not `1`, so it uses the plural form.

---

## `format_percent(number, format=None, locale=LC_NUMERIC, decimal_quantization=True, group_separator=True)`

Format a number as a percent value according to the given format.

```python
>>> from babel.numbers import format_percent
>>> format_percent(0.34, locale='en_US')
'34%'
>>> format_percent(25.1234, '#,##0.##%', locale='en_US')
'2,512.34%'
>>> format_percent(25.1234, '#,##0.##%', locale='sv_SE')
'2\xa0512,34\xa0%'
```

---

## `parse_decimal(string, locale=LC_NUMERIC, strict=False)`

Parse localized decimal string into a decimal.

```python
>>> from babel.numbers import parse_decimal
>>> parse_decimal('1,099.98', locale='en_US')
Decimal('1099.98')
>>> parse_decimal('1.099,98', locale='de')
Decimal('1099.98')
```

**Parameters:**
- `string` — the string to be parsed
- `locale` — a `Locale` object or locale identifier
- `strict` — bool, if `True`, raise `NumberFormatError` on ambiguous input

---

## Number Format Pattern Syntax

Babel uses Unicode CLDR number format patterns. Key symbols:

| Symbol | Meaning |
|--------|---------|
| `0`    | Digit (shows zero if absent) |
| `#`    | Digit (suppressed if absent) |
| `@`    | Significant digit |
| `.`    | Decimal separator |
| `,`    | Grouping separator |
| `%`    | Multiply by 100 and show as percent |
| `-`    | Minus sign |
| `+`    | Prefix positive numbers with `+` |

### Significant Digit Rules

When a pattern contains `@` symbols:
- Minimum significant digits = number of `@` symbols
- Maximum significant digits = number of `@` plus number of `#` symbols that follow
- The decimal point is only shown if fractional digits are actually needed

For example, with `@@##` (min=2, max=4):
- `10` has 2 significant digits → formatted as `'10'` (no decimal needed)
- `1.5` has 2 significant digits needed → formatted as `'1.5'`
- `0.001234` → formatted as `'0.001234'` (4 sig digits)
