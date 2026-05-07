# pint Unit Transformation Documentation
# Source: https://pint.readthedocs.io/
# pint version: 0.25.2

## Overview

pint provides several utility functions for transforming quantities into alternative
unit representations. These include compact notation, reduced units, unprefixed units,
and base unit conversions.

## Core API

```python
import pint

ureg = pint.UnitRegistry()

# Create a quantity
q = 5000 * ureg.meter
q = ureg.parse_expression("60 km/h")
q = ureg.Quantity(1.5, "kilogram * meter / second**2")

# Basic conversions
q.to("kilometer")       # explicit unit conversion
q.to_base_units()       # convert to plain base units (m, kg, s, etc.)
q.to_compact()          # choose the most human-readable SI prefix
q.to_reduced_units()    # reduce multi-unit quantities to fewest dimensions
q.to_unprefixed()       # strip SI prefixes (km -> m, ms -> s, etc.)
```

## Speed Units and Conversion (km/h, mph)

Speed in km/h involves a compound unit with a time denominator (hour).
Conversion to/from base units (m/s) uses the formula:
- 1 km/h = 1000 m / 3600 s = 1/3.6 m/s

```python
import pint
ureg = pint.UnitRegistry()

# km/h to m/s conversion
q = 60 * ureg.parse_expression("km/h")
q_ms = q.to("m/s")
assert abs(q_ms.magnitude - 60/3.6) < 1e-9  # 16.667 m/s

# Roundtrip: km/h -> m/s -> km/h
q_back = q_ms.to("km/h")
assert abs(q_back.magnitude - 60.0) < 1e-9
```

**Invariant**: For any speed `v_kmh` in km/h:
`ureg.Quantity(v_kmh, "km/h").to("m/s").to("km/h").magnitude == v_kmh`

## to_compact() — SI Prefix Selection

`to_compact()` selects the most human-readable SI prefix for a quantity. The algorithm:
1. Converts to base units (m, kg, s, etc.)
2. Computes `power = floor(log10(magnitude) / unit_power / 3) * 3`
3. Finds the matching SI prefix from the sorted list of SI powers

The SI powers list includes: -30, -27, -24, ..., -6, -3, -2, -1, 0, 1, 2, 3, 6, ...

```python
import pint
ureg = pint.UnitRegistry()

# to_compact examples
assert str((0.001 * ureg.meter).to_compact().units) == "millimeter"
assert str((1e-6 * ureg.second).to_compact().units) == "microsecond"
assert str((1e3 * ureg.watt).to_compact().units) == "kilowatt"
assert str((1e6 * ureg.meter).to_compact().units) == "megameter"
```

**Invariant**: `quantity.to_compact().to(quantity.units).magnitude == quantity.magnitude`
(The compact representation preserves the original value.)

## to_reduced_units() — Dimension Reduction

`to_reduced_units()` reduces a quantity to one unit per dimension. When multiple
units of the same dimension appear in a quantity, they are merged into a single unit.

The reduction formula: if `unit2 = unit1^power`, then the new exponent for unit2 is
`exp / power` where `exp` is the original exponent of unit1.

```python
import pint
ureg = pint.UnitRegistry()

# m^2 / cm: m and cm are both length, cm = 0.01 m
q = 1 * ureg.m**2 / ureg.cm
reduced = q.to_reduced_units()
# result should be equivalent to 100 m (one length unit)
assert abs(reduced.to("m").magnitude - 100.0) < 1e-9
```

**Invariant**: The reduced quantity has the same physical value as the original.
`quantity.to_reduced_units().to(quantity.units) == quantity`

## to_unprefixed() — Prefix Stripping

`to_unprefixed()` converts a quantity to the unprefixed form of its units,
removing all SI prefixes. For example, km → m, ms → s, MW → W.

```python
import pint
ureg = pint.UnitRegistry()

# to_unprefixed examples
q1 = 5 * ureg.kilometer
assert abs(q1.to_unprefixed().to("meter").magnitude - 5000.0) < 1e-9

q2 = 100 * ureg.millisecond
assert abs(q2.to_unprefixed().to("second").magnitude - 0.1) < 1e-9

q3 = 1 * ureg.megawatt
assert abs(q3.to_unprefixed().to("watt").magnitude - 1e6) < 1e-9
```

**Invariant**: `quantity.to_unprefixed().magnitude != quantity.magnitude` when the
unit has a non-trivial SI prefix (like kilo, milli, mega, etc.).

## Hypothesis Strategy Suggestions

```python
from hypothesis import strategies as st
import pint

ureg = pint.UnitRegistry()

# For km/h roundtrip testing:
speeds_kmh = st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)

# For to_compact testing (specific known values):
compact_cases = st.sampled_from([1e-3, 1e-6, 1.0, 1e3, 1e6])

# For to_reduced_units testing:
# Create quantities with same-dimension units at different scales
```
