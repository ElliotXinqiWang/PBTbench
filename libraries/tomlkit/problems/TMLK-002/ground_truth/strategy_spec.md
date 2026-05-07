# Strategy Specification for TMLK-002

## Bug 1: Fractional seconds alignment (L4)

**Location**: `tomlkit/_utils.py:57` in `parse_rfc3339()`

**Trigger condition**: Parse a TOML datetime with fewer than 6 fractional second digits. The bug uses right-alignment (`:>06s`) instead of left-alignment (`:<06s`) when zero-padding the fractional string to 6 characters. This means `.5` becomes `000005` (microsecond=5) instead of `500000` (microsecond=500000).

**Why default strategy is not enough**: Default testing typically uses either no fractional seconds or full 6-digit precision (e.g., `.123456`). The bug only triggers for 1-5 digit fractional seconds, which are less common in test data. Additionally, the bug is in a format string character (`<` vs `>`), which looks innocuous in code review.

**Trigger probability with default strategy**: ~0% (default strategies don't generate TOML strings with short fractional seconds)

**Minimal trigger input**: `dt = 2024-01-15T10:30:00.5Z`
- Expected: microsecond = 500000
- Buggy: microsecond = 5

## Bug 2: Timezone minute offset calculation (L3)

**Location**: `tomlkit/_utils.py:67` in `parse_rfc3339()`

**Trigger condition**: Parse a TOML datetime with a timezone offset where the minute component is non-zero. The bug multiplies `minute_offset * 6` instead of `minute_offset * 60`, giving incorrect UTC offsets for timezones like +05:30 (India), +09:45 (Chatham Islands), +03:30 (Iran).

**Why default strategy is not enough**: Most test data uses UTC (`Z`) or whole-hour timezone offsets like `+05:00` or `-08:00`. Non-whole-hour offsets are uncommon in standard testing. Additionally, the arithmetic bug (6 vs 60) produces a plausible-looking offset, making visual verification difficult.

**Trigger probability with default strategy**: <5% (most random timezone offsets use whole hours)

**Minimal trigger input**: `dt = 2024-01-15T10:30:00+05:30`
- Expected: utcoffset = 5:30:00 (19800 seconds)
- Buggy: utcoffset = 5:03:00 (18180 seconds)

## Bug 3: Multiline string closing delimiter boundary (L3)

**Location**: `tomlkit/parser.py:855` in `Parser._parse_string()`

**Trigger condition**: Parse a multiline string (literal `'''` or basic `"""`) where 4 or 5 consecutive delimiter characters appear at the end. TOML allows up to 2 extra delimiter characters before the closing triple-delimiter. The bug uses `close[:-2]` instead of `close[:-3]`, adding one extra delimiter character to the parsed value.

**Why default strategy is not enough**: This edge case requires deliberately constructing a multiline string that ends with 1 or 2 extra quote characters before the closing triple-quote. Default test generators almost never produce this pattern. The TOML spec section on this edge case is rarely tested.

**Trigger probability with default strategy**: <1% (requires specific trailing quote pattern)

**Minimal trigger input**: `key = '''x''''` (multiline literal, 4 consecutive quotes at end)
- Expected: value = `x'` (1 trailing quote + closing `'''`)
- Buggy: value = `x''` (2 trailing quotes, 1 extra)

## Bug 4: Inline table trailing comma (L2)

**Location**: `tomlkit/items.py:1815` in `InlineTable.as_string()`

**Trigger condition**: Serialize any TOML document containing an inline table with at least one key-value pair. The bug changes `i < last_item_idx` to `i <= last_item_idx`, adding a comma after the last key-value pair. This produces output like `{a = 1, b = 2,}` which is invalid TOML 1.0 (trailing commas are forbidden in inline tables).

**Why default strategy is not enough**: Baseline tests often test parsing correctness but not serialization roundtrip. The bug only manifests when calling `dumps()` on a parsed inline table and then trying to re-parse the output.

**Trigger probability with default strategy**: <10% (needs to test roundtrip of inline tables specifically)

**Minimal trigger input**: `x = {a = 1}`
- Expected serialization: `x = {a = 1}`
- Buggy serialization: `x = {a = 1,}` (trailing comma, invalid TOML)
