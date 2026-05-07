# H5LB-001 Strategy Specification

## Bug 1: AAA Outer Loop Limit (html5parser.py)

**Location**: `html5lib/html5parser.py` — `endTagFormatting`, outer `while` loop

**Correct behavior**: The Adoption Agency Algorithm runs up to 8 outer iterations.

**Bug**: Limit changed from 8 to 4, so deeply-nested structures (requiring 5+ iterations) are incorrectly processed.

### Trigger Condition

HTML of the form `<b>t0<div>t1<div>t2<div>t3<div>t4<p>t5</b>` requires exactly 5 outer AAA iterations. The formula: N nested block elements (divs + 1 terminal p) inside a formatting element requires N outer iterations.

- 1 div + 1 p inside `<b>` → 2 iterations (passes with limit=4)
- 2 divs + 1 p → 3 iterations (passes with limit=4)
- 3 divs + 1 p → 4 iterations (passes with limit=4, borderline)
- **4 divs + 1 p → 5 iterations (FAILS with limit=4)**

### Strategy Design

- **Minimum trigger**: `<b>a<div>b<div>c<div>d<div>e<p>f</b>` (4 divs + 1 p = 5 iterations)
- **Why default strategies miss it**: Random HTML generators rarely produce deeply nested unclosed div chains inside formatting elements. The default `st.from_regex` for HTML produces balanced tags.
- **Trigger probability with default strategy**: ~0.1% (must generate 4+ open divs inside a formatting element without closing them)
- **Trigger probability with targeted strategy**: 100% (always use 4-div nesting)

### Ground Truth PBT Strategy

Generate `<b>` containing 4 unclosed `<div>` elements and 1 `<p>`, with varying text content at each level. Check that the innermost text is wrapped in `<b>` in the output.

---

## Bug 2: Optional P End Tag before H6 (filters/optionaltags.py)

**Location**: `html5lib/filters/optionaltags.py` — `is_optional_end` method

**Correct behavior**: The HTML5 spec states that `</p>` may be omitted when the next element is `<h6>` (among others). The filter should recognize `h6` as a valid next element.

**Bug**: `'h6'` is removed from the tuple of elements after which `</p>` can be omitted.

### Trigger Condition

- Input: `<p>text<h6>heading</h6>` followed by re-serialization with `omit_optional_tags=True`
- With correct code: `</p>` before `<h6>` is omitted (round-trip preserves structure)
- With bug: `</p>` before `<h6>` is NOT omitted, but since the spec says it's legal to omit, the serializer output may deviate from expected HTML5 behavior

Actually the bug manifests in round-trip: the serialized output with `omit_optional_tags=True` for the buggy version retains `</p>` unnecessarily. When re-parsed, this can change the structure.

### Strategy Design

- **Minimum trigger**: any `<p>` followed directly by `<h6>` in the parse tree
- **Why default strategies miss it**: The bug only activates with `omit_optional_tags=True` AND specifically `<h6>` (not `<h1>`-`<h5>`). Random HTML generation has low probability of generating `p` immediately before `h6`.
- **Trigger probability with default strategy**: ~1% (must generate `<p>` immediately followed by `<h6>`)
- **Trigger probability with targeted strategy**: 100% (always generate `<p>...<h6>...` structure)

---

## Bug 3: Boolean Attribute Minimization (serializer.py)

**Location**: `html5lib/serializer.py` — `serialize` method, boolean attribute check

**Correct behavior**: Element-specific boolean attributes (e.g., `disabled` on `<input>`) should be minimized to bare `disabled` (no `=""`).

**Bug**: `booleanAttributes.get(name, tuple())` changed to `booleanAttributes.get(name.upper(), tuple())`. Since all keys in `booleanAttributes` are lowercase, `get(name.upper(), ())` always returns `()` for element-specific attrs.

### Trigger Condition

- Must use `minimize_boolean_attributes=True`
- Must use an element-specific boolean attribute (not a global one like `contenteditable`)
- Element-specific boolean attrs include: `disabled`, `checked`, `readonly`, `required`, `multiple`, `autofocus` on `<input>`, `<select>`, `<button>`, etc.

### Strategy Design

- **Why default strategies miss it**: `minimize_boolean_attributes=True` is not the default. Must explicitly use this option AND use element-specific (not global) boolean attributes.
- **Trigger probability with default strategy**: ~3% (requires non-default serializer option + element-specific bool attr)
- **Trigger probability with targeted strategy**: 100% (always use `minimize_boolean_attributes=True` with input/disabled)

---

## Bug 4: Whitespace Collapsing (filters/whitespace.py)

**Location**: `html5lib/filters/whitespace.py` — `whitespace_filter`

**Correct behavior**: With `strip_whitespace=True`, `SpaceCharacters` tokens are collapsed to a single space `" "`.

**Bug**: `token["data"] = " "` changed to `token["data"] = "  "` (double space).

### Trigger Condition

- Must use `strip_whitespace=True` (or `HTMLSerializer(strip_whitespace=True)`)
- Input must contain text with whitespace tokens between words
- The serialized output will contain `"  "` (double space) instead of `" "` (single space)

### Strategy Design

- **Minimum trigger**: any text with at least 2 spaces between words, serialized with `strip_whitespace=True`
- **Why default strategies miss it**: `strip_whitespace=True` is not the default. The bug is only in the `SpaceCharacters` token path (not `Characters` token which uses `collapse_spaces()`).
- **Trigger probability with default strategy**: ~2% (must use non-default strip_whitespace + have multiple spaces)
- **Trigger probability with targeted strategy**: 100% (always use `strip_whitespace=True` with multi-space input)
