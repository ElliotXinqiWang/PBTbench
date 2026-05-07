# pint API Reference (version 0.25.2)

## Overview

`pint` is a Python library for physical quantity arithmetic and unit conversions. It provides:

- A `UnitRegistry` that knows about all standard SI and non-SI units.
- A `Quantity` type that wraps a numeric value with a unit.
- Support for arithmetic, comparison, and conversion between compatible units.
- Special handling of **non-multiplicative** units such as temperatures (Celsius, Fahrenheit).
- **Delta** unit variants for temperature differences.
- `to_compact()` for automatic SI prefix selection.

---

## Creating a UnitRegistry and Quantities

```python
import pint

ureg = pint.UnitRegistry()

# Create a quantity
q = ureg.Quantity(100, 'meter')        # 100 m
q = ureg.Quantity(0, 'degC')          # 0 degrees Celsius
q = ureg.Quantity(5.5, 'kilogram')    # 5.5 kg

# Shorthand via registry attributes
q = 100 * ureg.meter
q = 0 * ureg.degC
```

> **Important**: Create a single `UnitRegistry` instance per script. All quantities must belong to the same registry to be compared or converted.

---

## Unit Conversion: `.to()`

```python
q = ureg.Quantity(100, 'm')
q.to('km')          # 0.1 km
q.to('cm')          # 10000 cm

q = ureg.Quantity(1, 'atm')
q.to('Pa')          # 101325.0 Pa
```

Conversion raises `pint.DimensionalityError` if units are incompatible (e.g., meters to kilograms).

---

## Temperature Conversions

Temperatures in pint use **offset units** (non-multiplicative). The conversion formula between Celsius and Fahrenheit is:

```
T_F = T_C * 9/5 + 32
T_C = (T_F - 32) * 5/9
```

Equivalently, in terms of Kelvin:

```
T_K = T_C + 273.15
T_K = T_F * 5/9 + 255.3722...
```

```python
ureg = pint.UnitRegistry()

ureg.Quantity(0, 'degC').to('degF')     # 32 degF
ureg.Quantity(100, 'degC').to('degF')   # 212 degF
ureg.Quantity(-40, 'degC').to('degF')   # -40 degF  (the unique crossover point)
ureg.Quantity(37, 'degC').to('degF')    # 98.6 degF

ureg.Quantity(32, 'degF').to('degC')    # 0 degC
ureg.Quantity(212, 'degF').to('degC')   # 100 degC
ureg.Quantity(98.6, 'degF').to('degC')  # 37 degC
```

### Known exact equivalences (useful for verification)

| Celsius | Fahrenheit |
|---------|-----------|
| -40 °C  | -40 °F    |
| 0 °C    | 32 °F     |
| 20 °C   | 68 °F     |
| 37 °C   | 98.6 °F   |
| 100 °C  | 212 °F    |
| 200 °C  | 392 °F    |

These equalities follow directly from the conversion formula `T_F = T_C * 9/5 + 32` and must hold exactly (within floating-point precision, i.e., tolerance < 0.001).

---

## Delta Temperature Units

**Delta units** represent a *difference* in temperature, not an absolute position on a scale. They have no offset — they are purely multiplicative.

```
1 Δ°C = 1 K               (same size as Kelvin step)
1 Δ°F = 5/9 Δ°C ≈ 0.5556 Δ°C
1 Δ°C = 9/5 Δ°F = 1.8 Δ°F
```

This arises from the formula: since `T_F = T_C * 9/5 + 32`, a *change* of 1 °C corresponds to a *change* of 9/5 °F; conversely, a *change* of 1 °F corresponds to a *change* of 5/9 °C.

In pint, delta units are named with a `delta_` prefix:

```python
ureg = pint.UnitRegistry()

# Temperature differences
d1 = ureg.Quantity(1, 'delta_degF')
d1.to('delta_degC')    # 0.5556 delta_degC  (= 5/9)

d2 = ureg.Quantity(1, 'delta_degC')
d2.to('delta_degF')    # 1.8 delta_degF    (= 9/5)

# Delta units are multiplicative — no offset involved
d3 = ureg.Quantity(9, 'delta_degF')
d3.to('delta_degC')    # 5.0 delta_degC

d4 = ureg.Quantity(5, 'delta_degC')
d4.to('delta_degF')    # 9.0 delta_degF
```

The conversion factor between Fahrenheit and Celsius delta units is exactly `5/9` in the direction `delta_degF → delta_degC`. This means:

```
d delta_degF = d * (5/9) delta_degC    for any d
```

---

## SI Prefix Auto-Selection: `to_compact()`

`Quantity.to_compact()` returns the quantity rescaled to a "human-readable" form by selecting the most appropriate SI prefix so that the magnitude falls in the range **[1, 1000)**.

```python
ureg = pint.UnitRegistry()

ureg.Quantity(1000, 'm').to_compact()       # 1.0 km    (magnitude 1.0)
ureg.Quantity(1500, 'm').to_compact()       # 1.5 km    (magnitude 1.5)
ureg.Quantity(500, 'm').to_compact()        # 500 m     (magnitude 500)
ureg.Quantity(1, 'm').to_compact()          # 1 m       (magnitude 1)
ureg.Quantity(0.001, 'm').to_compact()      # 1.0 mm    (magnitude 1.0)
ureg.Quantity(0.0005, 'm').to_compact()     # 0.5 mm    (magnitude 0.5)

ureg.Quantity(1000, 'g').to_compact()       # 1.0 kg
ureg.Quantity(5000, 'W').to_compact()       # 5.0 kW
ureg.Quantity(0.001, 'W').to_compact()      # 1.0 mW
```

### Invariants of `to_compact()`

1. **Physical equivalence**: `q.to_compact()` is physically equal to `q`.

   ```python
   compact = q.to_compact()
   assert compact.to(q.units).magnitude == approx(q.magnitude)
   ```

2. **Magnitude in [1, 1000)**: After `to_compact()`, the absolute value of the magnitude should be at least 1 and less than 1000 (when the input magnitude is positive and non-zero).

   ```python
   compact = ureg.Quantity(magnitude, unit).to_compact()
   assert 1 <= abs(compact.magnitude) < 1000  # when magnitude != 0
   ```

   Exception: if the original magnitude is 0 or if no appropriate prefix exists, the result may not satisfy this range.

3. **Idempotency**: `q.to_compact().to_compact() == q.to_compact()` (applying twice gives the same result).

The prefix is selected by finding the SI prefix such that dividing the base-unit magnitude by the prefix scale gives a value in [1, 1000). Available SI prefixes include: nano (10⁻⁹), micro (10⁻⁶), milli (10⁻³), (none = 10⁰), kilo (10³), mega (10⁶), giga (10⁹), and others.

---

## Unit Arithmetic

Quantities support standard arithmetic. Units are tracked automatically:

```python
ureg = pint.UnitRegistry()

distance = ureg.Quantity(100, 'm')
time = ureg.Quantity(10, 's')
speed = distance / time              # 10.0 m/s

energy = ureg.Quantity(1, 'kJ')
mass = ureg.Quantity(2, 'kg')
speed_squared = energy / mass        # 500.0 m²/s²

# Addition requires compatible units
a = ureg.Quantity(1, 'km')
b = ureg.Quantity(500, 'm')
total = a + b                        # 1.5 km
```

---

## Comparison

Two quantities can be compared if they have the same dimensionality:

```python
ureg.Quantity(1000, 'm') == ureg.Quantity(1, 'km')   # True
ureg.Quantity(100, 'degC') > ureg.Quantity(50, 'degC')  # True
```

---

## Error Handling

```python
# DimensionalityError for incompatible units
try:
    ureg.Quantity(1, 'm').to('kg')
except pint.DimensionalityError:
    pass

# UndefinedUnitError for unknown unit names
try:
    ureg.Quantity(1, 'parsec_per_fortnight').to('m/s')
except pint.UndefinedUnitError:
    pass
```
