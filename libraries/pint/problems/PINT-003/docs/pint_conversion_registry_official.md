# pint Unit Conversion and Arithmetic — Official Documentation

## Overview

pint is a Python package for defining, operating, and manipulating physical quantities: the product of a numerical value and a unit of measurement. It supports arithmetic operations between quantities, unit conversions, and dimensional analysis.

```python
import pint
ureg = pint.UnitRegistry()

distance = 1.0 * ureg.meter
speed = 10.0 * ureg.meter / ureg.second
area = distance ** 2
```

---

## Unit Conversion: `to()` Method

The primary method for converting a quantity from one unit to another is `Quantity.to(unit)`. This method always returns a **new** Quantity object with the converted value.

```python
ureg = pint.UnitRegistry()

q = 1.0 * ureg.meter
print(q.to('foot'))        # 3.28084 foot
print(q.to('centimeter'))  # 100.0 centimeter
print(q.to('kilometer'))   # 0.001 kilometer
print(q.to('inch'))        # 39.37008 inch
```

### Conversion Factor Direction

The conversion factor between units A and B satisfies:
- `q_in_A.to(B).magnitude = q_in_A.magnitude * factor(A→B)`
- `q_in_B.to(A).magnitude = q_in_B.magnitude * factor(B→A)`
- `factor(A→B) * factor(B→A) = 1` (factors are reciprocals)

This means that converting forward and then backward must recover the original value:

```python
ureg = pint.UnitRegistry()
q = 5.0 * ureg.meter
result = q.to('foot').to('meter')
assert abs(result.magnitude - 5.0) < 1e-9  # must hold exactly
```

### Roundtrip Property (Invariant)

For any compatible unit pair A and B, the following must always hold:

```
q.to(B).to(A) ≈ q  (up to floating-point precision)
```

This is a fundamental mathematical property: if `f(A→B)` is the conversion factor, then `f(B→A) = 1/f(A→B)`, and applying both in sequence gives `q * f(A→B) * f(B→A) = q * 1 = q`.

```python
import pint
ureg = pint.UnitRegistry()

# All of these roundtrips must hold
q_m = 3.5 * ureg.meter
assert abs(q_m.to('foot').to('meter').magnitude - 3.5) < 1e-9
assert abs(q_m.to('inch').to('meter').magnitude - 3.5) < 1e-9
assert abs(q_m.to('kilometer').to('meter').magnitude - 3.5) < 1e-9
assert abs(q_m.to('centimeter').to('meter').magnitude - 3.5) < 1e-9

q_s = 60.0 * ureg.second
assert abs(q_s.to('minute').to('second').magnitude - 60.0) < 1e-9
assert abs(q_s.to('hour').to('second').magnitude - 60.0) < 1e-9
```

### Standard Length Conversion Factors

| From | To | Factor |
|------|-----|--------|
| meter | foot | 3.280839895... |
| meter | inch | 39.37007874... |
| meter | yard | 1.093613298... |
| meter | mile | 0.000621371... |
| meter | centimeter | 100.0 (exact) |
| meter | kilometer | 0.001 (exact) |
| foot | meter | 0.3048 (exact) |
| inch | meter | 0.0254 (exact) |

---

## In-Place Conversion: `ito()` Method

The `ito()` method performs conversion **in place**, modifying the Quantity object directly and returning `None`:

```python
ureg = pint.UnitRegistry()

q = 1.0 * ureg.meter
q.ito('foot')
print(q)  # 3.28084 foot
```

**Semantic contract**: `q.ito(target)` is semantically equivalent to assigning `q = q.to(target)`. The resulting magnitude must be identical:

```python
ureg = pint.UnitRegistry()

q1 = 5.0 * ureg.meter
q2 = 5.0 * ureg.meter

expected = q2.to('foot').magnitude  # 16.40419...
q1.ito('foot')

assert abs(q1.magnitude - expected) < 1e-9
```

---

## Quantity Power Operations: `q ** n`

Raising a Quantity to an integer power n multiplies each unit's dimension exponent by n.

### Dimensionality Rules

- `(meter)**n` → dimensionality `{[length]: n}`
- `(meter/second)**n` → dimensionality `{[length]: n, [time]: -n}`
- `(meter**2)**n` → dimensionality `{[length]: 2*n}`

```python
ureg = pint.UnitRegistry()

# Simple power
q = 3.0 * ureg.meter
print((q**2).dimensionality)  # {[length]: 2}
print((q**3).dimensionality)  # {[length]: 3}
print((q**2).units)           # meter ** 2
print((q**3).units)           # meter ** 3

# Compound unit power
v = 10.0 * ureg.meter / ureg.second
print((v**2).dimensionality)  # {[length]: 2, [time]: -2}
print((v**2).units)           # meter ** 2 / second ** 2

# Energy: E = 0.5 * m * v^2 → [mass] * [length]^2 / [time]^2
m = 2.0 * ureg.kilogram
E = 0.5 * m * v**2
print(E.dimensionality)  # {[length]: 2, [mass]: 1, [time]: -2}
```

### Magnitude Rule

When raising a quantity to power n, the magnitude is raised to n:

```python
ureg = pint.UnitRegistry()
q = 3.0 * ureg.meter
assert (q**2).magnitude == 9.0
assert (q**3).magnitude == 27.0
```

### Dimensional Analysis with Powers

The exponent of each base dimension in `q**n` must be exactly `n` times the exponent in `q`:

```python
ureg = pint.UnitRegistry()

# If q has dimensionality D, then (q**n) must have dimensionality n*D
q = 5.0 * ureg.meter
for n in range(2, 6):
    powered = q ** n
    assert dict(powered.dimensionality) == {'[length]': n}, \
        f"(meter**{n}).dimensionality should be {{[length]: {n}}}"
```

---

## Quantity Arithmetic: Addition and Subtraction

### Same-Unit Addition

When both operands have identical units, the magnitudes are added directly:

```python
ureg = pint.UnitRegistry()
q1 = 3.0 * ureg.meter
q2 = 5.0 * ureg.meter
result = q1 + q2
assert result.magnitude == 8.0
assert str(result.units) == 'meter'
```

### Different-Unit Addition (Compatible Dimensions)

When two quantities have different but compatible units (same dimensionality), pint converts the second operand to the first operand's units before adding:

**Rule**: `q1 (unit_A) + q2 (unit_B)` → result in `unit_A`, where `q2` is first converted to `unit_A`.

```python
ureg = pint.UnitRegistry()

# 1 meter + 100 centimeters:
# → converts 100 cm to meters: 100 cm = 1.0 m
# → adds 1.0 m + 1.0 m = 2.0 m
q1 = 1.0 * ureg.meter
q2 = 100.0 * ureg.centimeter
result = q1 + q2
assert result.magnitude == pytest.approx(2.0)  # NOT 101.0!
assert str(result.units) == 'meter'

# 1 kilometer + 500 meters:
# → converts 500 m to km: 500 m = 0.5 km
# → adds 1.0 km + 0.5 km = 1.5 km
q3 = 1.0 * ureg.kilometer
q4 = 500.0 * ureg.meter
result2 = q3 + q4
assert result2.magnitude == pytest.approx(1.5)  # NOT 501!
```

**Key invariant**: `q1 + q2` (different compatible units) should equal `q1 + q2.to(q1.units)`.

### Subtraction (Compatible Dimensions)

Same rule applies to subtraction — the second operand is converted to the first operand's units:

```python
ureg = pint.UnitRegistry()
q1 = 2.0 * ureg.kilometer
q2 = 500.0 * ureg.meter  # = 0.5 km
result = q1 - q2
assert result.magnitude == pytest.approx(1.5)  # 2.0 - 0.5 = 1.5 km
```

---

## Quantity Multiplication and Division

### Unit Multiplication (Dimensional Arithmetic)

When multiplying two quantities, their unit dimensions are **added** (exponents add):

```python
ureg = pint.UnitRegistry()

# meter * meter = meter**2
q1 = 3.0 * ureg.meter
q2 = 4.0 * ureg.meter
area = q1 * q2
print(area)          # 12.0 meter ** 2
print(area.units)    # meter ** 2
print(area.dimensionality)  # {[length]: 2}

# meter/second * second = meter
v = 10.0 * ureg.meter / ureg.second
t = 5.0 * ureg.second
d = v * t
print(d)          # 50.0 meter
print(d.units)    # meter
```

### Unit Cancellation

When units cancel (exponents sum to zero), the result is **dimensionless** with empty units:

```python
ureg = pint.UnitRegistry()

# meter * (1/meter) = dimensionless
q = 5.0 * ureg.meter
q_inv = 1.0 / ureg.meter  # 1/meter

result = (5.0 * q) * (q_inv / 5.0)
assert result.dimensionless
assert str(result.units) == ''  # empty string = no units = dimensionless

# kilometer / meter = dimensionless ratio
q_km = 10.0 * ureg.kilometer
q_m = 10000.0 * ureg.meter
ratio = q_km / q_m  # = 10000m / 10000m = 1.0 (dimensionless)
assert ratio.dimensionless
```

**Important**: The dimension exponent arithmetic must be exact. If unit A appears with exponent +1 in the numerator and -1 in the denominator, the result exponent for A is exactly 0 and A must be **completely eliminated** from the unit system (not kept as `A**0`).

### Unit Preservation

Non-cancelled units must be preserved with their correct exponents:

```python
ureg = pint.UnitRegistry()

# m * m = m^2 (NOT dimensionless)
q = 3.0 * ureg.meter
result = q * q
assert str(result.units) == 'meter ** 2'
assert not result.dimensionless
assert dict(result.dimensionality) == {'[length]': 2}

# m^2 * m = m^3
area = (3.0 * ureg.meter) ** 2
length = 4.0 * ureg.meter
volume = area * length
assert dict(volume.dimensionality) == {'[length]': 3}
```

---

## Dimensional Analysis Reference

### Base Dimensions

pint uses SI base dimensions:
- `[length]` — meter (m)
- `[mass]` — kilogram (kg)
- `[time]` — second (s)
- `[current]` — ampere (A)
- `[temperature]` — kelvin (K)
- `[substance]` — mole (mol)
- `[luminosity]` — candela (cd)

### Derived Dimensions

| Quantity | Expression | Example |
|----------|-----------|---------|
| Area | `[length]²` | m², cm², km² |
| Volume | `[length]³` | m³, liter |
| Velocity | `[length]/[time]` | m/s, km/h |
| Acceleration | `[length]/[time]²` | m/s² |
| Force | `[mass]·[length]/[time]²` | N = kg·m/s² |
| Energy | `[mass]·[length]²/[time]²` | J = kg·m²/s² |
| Power | `[mass]·[length]²/[time]³` | W = kg·m²/s³ |
| Pressure | `[mass]/([length]·[time]²)` | Pa = kg/(m·s²) |

### Checking Dimensionality

```python
ureg = pint.UnitRegistry()

# Access dimensionality as a dict
q = 1.0 * ureg.newton
print(dict(q.dimensionality))  # {[length]: 1, [mass]: 1, [time]: -2}

# Check if dimensionless
ratio = (3.0 * ureg.meter) / (5.0 * ureg.meter)
print(ratio.dimensionless)  # True

# Check compatibility
q1 = 1.0 * ureg.meter
q2 = 1.0 * ureg.foot
print(q1.is_compatible_with(q2))  # True (both [length])

q3 = 1.0 * ureg.second
print(q1.is_compatible_with(q3))  # False ([length] vs [time])
```

---

## UnitRegistry and Caching

The `UnitRegistry` manages all unit definitions and caches computed conversion factors for performance. The caching system stores the factor for each `(src_units, dst_units)` pair.

**Contract**: For any two compatible unit expressions `A` and `B`, the following must hold regardless of the order in which conversions are called:

1. `factor(A→B) == 1 / factor(B→A)` (exact reciprocal)
2. `quantity_A.to(B).to(A) ≈ quantity_A` (roundtrip)
3. The cached factor for `(A, B)` must be the factor for converting A to B (not B to A)

```python
ureg = pint.UnitRegistry()

# Regardless of which conversion is done first, all must be correct:
q = 100.0 * ureg.meter

# Forward and backward must both work correctly
fwd_result = q.to('foot').magnitude    # ≈ 328.084
bwd_result = fwd_result * ureg.foot    # ≈ 328.084 foot
restored = bwd_result.to('meter').magnitude  # must be ≈ 100.0
assert abs(restored - 100.0) < 1e-6
```

---

## Summary: Key Properties to Test

The following properties should always hold in a correct pint implementation:

1. **Roundtrip Invariant**: `q.to(B).to(A) ≈ q.magnitude` for any compatible units A, B
2. **Power Dimensionality**: `(q**n).dimensionality == {dim: n*exp for dim, exp in q.dimensionality.items()}`
3. **Mixed-Unit Addition**: `q_A + q_B == q_A.magnitude + q_B.to(A).magnitude` (in units of A)
4. **Unit Multiplication**: `(q_m * q_m).units == meter**2` and not dimensionless
5. **Unit Cancellation**: `(q_m * q_inv_m).units == ''` (exactly empty, no residual `m**0`)
