# Strategy Specification for YAML-003

## Bug 1: Negative Float Resolver (L4)

**Location**: `yaml/resolver.py`, `Resolver.add_implicit_resolver` call for float tag.

**What changed**: The `first` parameter, which tells the resolver which first-characters
to index the float pattern under, was changed from `list('-+0123456789.')` to
`list('+0123456789.')`. The character `'-'` was removed.

**Trigger condition**: Any YAML scalar that starts with `'-'` and would match the
YAML 1.1 float pattern. Specifically, plain negative decimal floats:
`-1.5`, `-0.5`, `-100.0`, `-.inf`.

**Why default strategy doesn't work**: Using `st.floats()` and round-tripping via
`safe_dump/safe_load` does NOT trigger the bug, because `safe_dump(-1.5)` adds an
explicit `!!float` tag which bypasses the resolver. The bug only manifests when
loading a YAML text where the scalar lacks an explicit tag.

**Targeted strategy**: 
```python
st.floats(min_value=-1e15, max_value=-1e-10, allow_nan=False, allow_infinity=False)
.filter(lambda f: repr(f).startswith('-') and '.' in repr(f) and 'e' not in repr(f).lower())
```
Then load `repr(f)` directly. This gives 100% trigger rate.

**Trigger probability with default strategy** (direct text parsing): ~50% for
`st.floats()` generating negative values, but only if the test calls
`yaml.safe_load(repr(f))` rather than the roundtrip pattern.

**Minimum trigger example**: `yaml.safe_load('-1.5')` returns string `-1.5` instead of float.

---

## Bug 2: Sexagesimal Base Multiplier (L3)

**Location**: `yaml/constructor.py`, `construct_yaml_int`, sexagesimal branch.

**What changed**: `base *= 60` changed to `base *= 6`.

**Trigger condition**: Any YAML scalar in sexagesimal (colon) notation recognized
by the int resolver: `1:30`, `2:05`, `1:02:03`, etc.

**Why default strategy doesn't work**: `safe_dump(n)` for any Python integer produces
decimal notation, never sexagesimal. The bug is only triggered when loading YAML text
that was written with colon notation. There's no safe_dump/safe_load roundtrip path.

**Targeted strategy**:
```python
st.integers(min_value=1, max_value=99), st.integers(min_value=0, max_value=59)
```
Format as `f"{h}:{m:02d}"` and check `yaml.safe_load(text) == h*60 + m`.

**Trigger probability**: ~98% (fails whenever h*60+m != h*6+m, i.e., h*(60-6) != 0,
which is whenever h != 0. Since h >= 1, all examples trigger it.)

**Minimum trigger example**: `yaml.safe_load('1:00')` should be 60, gives 6.

---

## Bug 3: Set Tag Replaced with Map (L3)

**Location**: `yaml/representer.py`, `SafeRepresenter.represent_set`.

**What changed**: Tag `'tag:yaml.org,2002:set'` changed to `'tag:yaml.org,2002:map'`.

**Trigger condition**: Any Python `set` object passed to `safe_dump`.

**Why default strategy doesn't work (before this is easy)**: Actually this bug is
easily detected by any strategy that generates sets. The challenge is knowing to
test sets at all, and knowing to use `type()` not `isinstance()`.

**Targeted strategy**:
```python
st.sets(st.one_of(st.integers(-100, 100), st.text(min_size=1, max_size=10, ...)),
        min_size=1, max_size=8)
```

**Trigger probability**: 100% for any non-empty set.

**Minimum trigger example**: `yaml.safe_load(yaml.safe_dump({1}))` returns `{1: None}`,
not `{1}`.

---

## Bug 4: Date Representer Appends Time (L2)

**Location**: `yaml/representer.py`, `SafeRepresenter.represent_date`.

**What changed**: `data.isoformat()` changed to `data.isoformat() + ' 00:00:00'`.

**Trigger condition**: Any `datetime.date` object (not `datetime.datetime`) passed to
`safe_dump`.

**Why default strategy doesn't work (but is actually easy to find)**:
This bug is triggered by any date. The tricky part is that:
1. `datetime.datetime` is a subclass of `datetime.date`, so `isinstance(result, datetime.date)`
   is `True` even when `result` is a datetime — must use `type(result) is datetime.date`.
2. The values are numerically equal: `datetime.date(2024,6,15) == datetime.datetime(2024,6,15,0,0,0)`
   is `False`, so equality check works too.

**Targeted strategy**:
```python
st.dates(min_value=datetime.date(1970, 1, 1), max_value=datetime.date(2100, 12, 31))
```
Check `type(yaml.safe_load(yaml.safe_dump(d))) is datetime.date`.

**Trigger probability**: 100% for any date.

**Minimum trigger example**: `type(yaml.safe_load(yaml.safe_dump(datetime.date(2024,1,1))))` 
returns `datetime.datetime`, not `datetime.date`.
