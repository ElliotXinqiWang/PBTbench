# Pint 0.25.2 — String Formatting & Compact Notation (Official Documentation)

Source: https://pint.readthedocs.io/en/0.25.2/user/formatting.html

---

## Overview

Pint enables customization of how `Unit`, `Quantity`, and `Measurement` objects convert to strings through format specifications. The basic format structure follows this pattern:

```
[magnitude format][modifier][pint format]
```

where each component is optional.

## Format Types

Pint supports six primary formats affecting the complete representation:

| Code | Name | Example Output |
|------|------|----------------|
| `D`  | default | `3.4e+09 kilogram * meter / second ** 2` |
| `P`  | pretty | `3.4×10⁹ kilogram·meter/second²` |
| `H`  | HTML | `3.4×10<sup>9</sup> kilogram meter/second<sup>2</sup>` |
| `L`  | latex | `3.4\times 10^{9}\ \frac{\mathrm{kilogram} \cdot \mathrm{meter}}{\mathrm{second}^{2}}` |
| `Lx` | latex siunitx | `\SI[]{3.4e+09}{\kilo\gram\meter\per\second\squared}` |
| `C`  | compact | `3.4e+09 kilogram*meter/second**2` |

## Modifier Types

### Quantity Modifiers

The `#` modifier invokes `Quantity.to_compact()` before formatting, converting units to smaller, more human-readable scales. For example, a quantity in `m·mg/s²` might be expressed compactly as `1.0 m·mg/s²`.

```python
q = 2.3e-6 * ureg.m ** 3 / (ureg.s ** 2 * ureg.kg)
f"{q:~#P}"       # Results: '2.3 mm³/g/s²' (compact short pretty)
f"{q:.2f~#P}"    # Results: '2.30 mm³/g/s²' (with 2 decimal places)
```

### Unit Modifiers

The `~` modifier substitutes unit symbols instead of canonical names:

```python
f"{q:~P}"        # Results: '2.3×10⁻⁶ m³/kg/s²'
```

### Magnitude Modifiers

Pint implements Python's standard format specifications for numeric values (e.g., `.2f`, `e`, `g`).

## Practical Examples

```python
from pint import UnitRegistry
ureg = UnitRegistry()
q = 2.3e-6 * ureg.m ** 3 / (ureg.s ** 2 * ureg.kg)

f"{q:~P}"        # '2.3×10⁻⁶ m³/kg/s²'
f"{q:~#P}"       # '2.3 mm³/g/s²'
f"{q:.2f~#P}"    # '2.30 mm³/g/s²'
```

## `to_compact()` Method

The `to_compact()` method converts a quantity to a more compact representation by selecting an appropriate unit from the same dimensionality.

### Behavior

`to_compact()` finds the "best" unit — the one that brings the magnitude closest to 1 (or within a reasonable order of magnitude). It works by iterating over compatible units in the registry and selecting the one that minimizes the number of leading zeros or very large exponents.

```python
distance = 1e-6 * ureg.meter
distance.to_compact()
# Result: <Quantity(1.0, 'micrometer')>

big_distance = 1e9 * ureg.meter
big_distance.to_compact()
# Result: <Quantity(1.0, 'gigameter')>
```

### `to_compact(unit=None)`

You can optionally pass a unit to constrain which family of units is searched:

```python
q.to_compact('m')   # Restricts to SI prefixed meters
```

### Rounding and Magnitude

`to_compact()` selects the unit that results in a magnitude in the range `[1, 1000)` when possible. The actual magnitude value is not rounded — the raw floating-point result is returned. Any rounding must be done separately (e.g., via format specifiers like `.2f`).

## Default Format Configuration

When no format specification is provided, Pint uses the value stored in `formatter.default_format`. This can be configured globally:

```python
ureg = UnitRegistry()
ureg.formatter.default_format = '.3f'
# All quantities now default to 3 decimal places
```

## Custom Formatting

### Registering Custom Formats

Use the `@pint.register_unit_format()` decorator:

```python
import pint

@pint.register_unit_format("Z")
def format_unit_simple(unit, registry, **options):
    return " * ".join(f"{u} ** {p}" for u, p in unit.items())

ureg = pint.UnitRegistry()
u = ureg.kg * ureg.m / ureg.s**2
f"{u:Z}"  # Uses custom format
```

### Subclassing Formatters

For comprehensive customization, subclass `DefaultFormatter` and override:

- `format_magnitude(magnitude, mspec, **kwspec)` — controls how numbers display
- `format_unit(unit, uspec, **kwspec)` — controls unit string rendering
- `format_quantity(quantity, qspec, **kwspec)` — controls overall quantity rendering

### Integration with External Libraries

Third-party libraries like SciForm integrate with custom formatters to provide advanced magnitude formatting with engineering notation and significant figure control.
