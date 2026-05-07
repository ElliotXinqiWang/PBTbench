# Pint 0.25.2 — Non-Multiplicative Units (Official Documentation)

Source: https://pint.readthedocs.io/en/0.25.2/user/nonmult.html

---

## Overview of Non-Multiplicative Units

Temperature units differ fundamentally from standard measurements. As the documentation explains: "Unlike meters and seconds, the temperature units fahrenheits and celsius are non-multiplicative units." These units operate within a reference-point system where conversions involve both scaling factors and offsets.

## Supported Temperature Units

Pint's default registry includes four temperature units:

- **degC** (Celsius)
- **degF** (Fahrenheit)
- **degK** (Kelvin)
- **degR** (Rankine)

## Basic Temperature Conversions

Converting between temperature scales is straightforward:

```python
from pint import UnitRegistry
ureg = UnitRegistry()
ureg.formatter.default_format = '.3f'
Q_ = ureg.Quantity

home = Q_(25.4, ureg.degC)
print(home.to('degF'))      # 77.720 degree_Fahrenheit
print(home.to('kelvin'))    # 298.550 kelvin
print(home.to('degR'))      # 537.390 degree_Rankine
```

## Delta Units: Temperature Differences

Every non-multiplicative temperature unit has a corresponding delta counterpart for expressing temperature *differences* rather than absolute values. This distinction is crucial because temperature *changes* follow different conversion rules than absolute temperatures.

For example, a change in Celsius equals a change in Kelvin (same scaling), but differs from Fahrenheit changes:

```python
increase = 12.3 * ureg.delta_degC
print(increase.to(ureg.kelvin))      # 12.300 kelvin
print(increase.to(ureg.delta_degF))  # 22.140 delta_degree_Fahrenheit
```

## Operations with Temperature Quantities

### Subtraction of Two Temperatures

Subtracting two offset-unit temperatures produces a delta unit:

```python
Q_(25.4, ureg.degC) - Q_(10., ureg.degC)
# Result: <Quantity(15.4, 'delta_degree_Celsius')>
```

### Adding/Subtracting Delta Units

You can combine delta quantities with absolute temperature values:

```python
Q_(25.4, ureg.degC) + Q_(10., ureg.delta_degC)
# Result: <Quantity(35.4, 'degree_Celsius')>

Q_(25.4, ureg.degC) - Q_(10., ureg.delta_degC)
# Result: <Quantity(15.4, 'degree_Celsius')>
```

### The Ambiguity Problem

Adding two absolute temperatures creates fundamental ambiguity. Pint raises an error to prevent this:

```python
heating_rate = 0.5 * ureg.kelvin/ureg.min
Q_(10., ureg.degC) + heating_rate * Q_(30, ureg.min)
# OffsetUnitCalculusError: Ambiguous operation with offset unit
```

**Solution 1:** Convert offset units to absolute units first:

```python
Q_(10., ureg.degC).to(ureg.kelvin) + heating_rate * Q_(30, ureg.min)
# Result: <Quantity(298.15, 'kelvin')>
```

**Solution 2:** Convert absolute units to delta units:

```python
Q_(10., ureg.degC) + heating_rate.to('delta_degC/min') * Q_(30, ureg.min)
# Result: <Quantity(25.0, 'degree_Celsius')>
```

## Multiplication and Division Restrictions

By default, multiplication, division, and exponentiation with offset units are prohibited due to ambiguity. Creating quantities with offset units requires explicit construction:

```python
ureg = UnitRegistry()
home = 25.4 * ureg.degC  # OffsetUnitCalculusError
Q_(25.4, ureg.degC)       # Correct approach
```

## The `autoconvert_offset_to_baseunit` Setting

For relaxed behavior, enable the `autoconvert_offset_to_baseunit` parameter:

```python
ureg = UnitRegistry(autoconvert_offset_to_baseunit=True)
T = 25.4 * ureg.degC
# Now multiplication by numbers works directly
```

In this mode, Pint automatically converts offset units to their base units (absolute units) before performing problematic operations:

```python
1/T
# Result: <Quantity(0.0033495..., '1 / kelvin')>

T * 10 * ureg.meter
# Result: <Quantity(527.15, 'kelvin * meter')>
```

You can toggle this behavior at runtime:

```python
ureg.autoconvert_offset_to_baseunit = False
# Now strict mode is reinstated
```

## Delta Unit Parsing

The parser automatically recognizes delta units in multiplicative contexts:

```python
print(ureg.parse_units('degC/meter'))
# Result: delta_degree_Celsius / meter

print(ureg.parse_units('degC'))
# Result: degree_Celsius (not delta)
```

Override this behavior with the `as_delta` parameter:

```python
print(ureg.parse_units('degC/meter', as_delta=False))
# Result: degree_Celsius / meter
```

## Defining Custom Temperature Units

To create new temperature units, specify the offset value in the unit registry definition file:

```
degC = degK; offset: 273.15 = celsius
degF = 5 / 9 * degK; offset: 255.372222 = fahrenheit
```

Delta units are automatically generated — no manual definition is needed.

The `offset` field in the unit definition specifies the additive offset applied during conversion to the base unit (Kelvin). For Fahrenheit:

- Scale factor: `5/9` (relative to Kelvin)
- Offset: `255.372222` K
- Full formula: `T_K = (5/9) * T_F + 255.372222`

Which is equivalent to the standard formula: `T_K = (T_F + 459.67) * 5/9`

## Key Takeaway

The documentation notes: "the addition of quantities with offset units is ambiguous" because multiple interpretations exist mathematically. Understanding when to use delta units and when to convert to absolute units is essential for correct temperature calculations in Pint.

---

## Internal Registry Format

In Pint's `default_en.txt` unit registry, non-multiplicative (offset) units are defined with a semicolon-separated offset field:

```
degK = [temperature]; offset: 0 = kelvin = K
degC = degK; offset: 273.15 = celsius = degreeC = degree_Celsius
degR = 5 / 9 * degK; offset: 0 = rankine = degR
degF = 5 / 9 * degK; offset: 255.372222 = fahrenheit = degreeF
```

The `offset` value represents the shift applied when converting to the base temperature unit (Kelvin). If the offset is incorrect (e.g., wrong value for Fahrenheit), all absolute Fahrenheit-to-Kelvin conversions will produce wrong results, while relative (delta) conversions — which only use the scale factor — remain correct.

### ScaleConverter vs OffsetConverter

Pint uses two different internal converter types:

- **ScaleConverter**: Used for multiplicative units (e.g., meters, kilograms). Conversion is `value * scale`.
- **OffsetConverter**: Used for non-multiplicative units (e.g., degC, degF). Conversion is `value * scale + offset`.

When computing with delta units (temperature differences), Pint internally uses only the scale factor and ignores the offset, because a *difference* does not shift by the reference point.

The `delta_degF` unit uses a `ScaleConverter` with scale = `5/9`, not an `OffsetConverter`. This means `delta_degF` conversions only multiply by the scale, with no offset involved.
