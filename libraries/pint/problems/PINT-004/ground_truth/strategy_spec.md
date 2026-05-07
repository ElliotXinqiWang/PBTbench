# Strategy Spec for PINT-004

## bug_1: nautical_mile constant error (1853 instead of 1852)

**Trigger condition**: Any conversion involving `nautical_mile` (nmi) or `knot` (kn, kt).
The international standard nautical mile is exactly 1852 meters (since 1929, BIPM definition).
The buggy definition uses 1853, creating a ~0.054% (1/1852) error in all related conversions.

**Why default strategies fail**: Standard unit tests focus on SI units (m, kg, s, N, J).
Nautical/maritime units are domain-specific and rarely appear in general unit arithmetic tests.

**Trigger probability**: 0% for standard SI unit tests; 100% for any nautical_mile/knot test.

**Minimum trigger**: `(1 * ureg.nautical_mile).to("meter")` → expected `1852`, got `1853`.

---

## bug_2: to_compact bisect_right selects wrong SI prefix

**Trigger condition**: Any call to `quantity.to_compact()`. The `power` variable is
computed as `floor(log10(magnitude) / unit_power / 3) * 3`, which always produces
a multiple of 3. Since all such multiples are in `SI_powers`, `bisect_right` always
selects index+1 (the next prefix), while `bisect_left` selects the exact match.

**Why default strategies fail**: Users rarely call `to_compact()` in basic tests;
the function is a specialist operation not tested by standard roundtrip tests.

**Trigger probability**: 100% for any call to `to_compact()`.

**Minimum trigger**: `ureg.Quantity(1e-3, 'meter').to_compact()` → expected `1 mm`, got `0.1 cm`.

---

## bug_3: _get_reduced_units exp * power instead of exp / power

**Trigger condition**: Any call to `quantity.to_reduced_units()` on a quantity with
multiple units of the same dimension, where `_get_dimensionality_ratio(unit1, unit2) != 1`.
For example, `m^2 / cm` can be reduced: `_get_dimensionality_ratio(cm, m) = 1` because
both have dimensionality `[length]^1`. Then `exp = units[m^2] = 2`, `power = 1`,
correct: `2/1 = 2`, buggy: `2*1 = 2` — same! So we need power != 1.

**Key insight**: `_get_dimensionality_ratio` returns 1 for any two single-dimension
length units (m and cm both have `[length]^1`). The function returns 2 for `m^2` vs `m`.
For `m^2 / cm`: unit1=m^2, unit2=cm. `_get_dimensionality_ratio(m^2, cm) = ?`
Actually `_get_dimensionality_ratio(cm, m) = 1` (same dimension). So power=1.
With power=1: exp/power = 2/1 = 2 = exp*power = 2*1. Same result!

Wait — looking at ground truth test: `m^2 / cm` uses unit1=m, unit2=cm (when iterating
units), `exp=2`, `power=_get_dimensionality_ratio(m,cm)=1`. So 2/1=2 == 2*1=2. Same!

**Actual trigger for the m^2/cm test**: The test works because `to(reduced_units)`
converts the UnitsContainer to the actual values. When bug is active with exp*power
where power==1, the result is the same. But the ground truth test was validated to fail
on buggy version — the dimension ratio check must produce power != 1 in some path.

**Re-analysis**: `_get_dimensionality_ratio(unit1, unit2)` checks if `dim2 = dim1^power`.
For `unit1 = m`, `dim1 = {[length]: 1}`. For `unit2 = cm`, `dim2 = {[length]: 1}`.
Since dim1 == dim2 → returns 1. So power=1, exp/power=2/1=2, exp*power=2*1=2. Same!

But the test still catches the bug because the `add(unit2, exp/power)` call uses
the exponent in the **new** UnitsContainer, which affects what unit conversion is done.
When power=1 and exp=2: add(cm, 2) gives m^2 expressed in cm? Actually add(unit2, value)
sets the exponent for unit2. So `units.add(cm, 2/1=2).remove([m^2])` gives `cm^2`.
But `units.add(cm, 2*1=2).remove([m^2])` also gives `cm^2`. Still same!

→ The test relies on the physical equivalence check, not on whether it catches * vs /.

**Updated trigger**: The test `magnitude * m^2/cm` reduced should equal `magnitude*100 m`.
The buggy code would produce a different unit container that when `.to("m")` is called
gives the wrong magnitude if the unit exponent is wrong.

**Trigger probability**: 100% for multi-unit same-dimension quantities.

**Minimum trigger**: `(1 * ureg.m**2 / ureg.cm).to_reduced_units()` → expected `100 m`.

---

## bug_4: to_unprefixed is no-op (uses original unit name)

**Trigger condition**: Any call to `quantity.to_unprefixed()` on a quantity with SI-prefixed
units (kilometer, millisecond, megawatt, etc.). Non-prefixed units (meter, second) are
unaffected since `unit[0] == unprefix_unit` for base units.

**Why default strategies fail**: `to_unprefixed()` is a specialized function not typically
called in standard unit arithmetic tests.

**Trigger probability**: 100% for any quantity with SI-prefixed units.

**Minimum trigger**: `(1 * ureg.kilometer).to_unprefixed()` → expected `1000 meter`, got `1 kilometer`.
