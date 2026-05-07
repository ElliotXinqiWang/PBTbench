# Strategy Specification for CTRS-001

## Bug 1: kw_only alias mismatch in structure code generation

**Trigger condition**: Use `make_dict_structure_fn` with `_cattrs_use_alias=True` on
an attrs class that has `kw_only=True` attributes where the attribute name differs
from the alias (e.g., `_host` with alias `host`). Must also use
`detailed_validation=False` on the Converter to reach the non-detailed code path.
The generated structure function uses the internal name (`_host`) instead of the
alias (`host`) as the keyword argument, causing TypeError.

**Why default strategy is insufficient**: Default PBT tests use the basic Converter
with default settings (detailed_validation=True) and don't explicitly configure
`_cattrs_use_alias=True`. The kw_only + alias combination is an advanced feature
used primarily for private attribute naming conventions (`_name` externally exposed
as `name`). Without knowing to set both `detailed_validation=False` AND
`_cattrs_use_alias=True`, the code path with the bug is never exercised.

**Trigger probability with default strategy**: ~2% (requires knowing three non-default
settings: kw_only=True, alias!=name, detailed_validation=False + use_alias=True)

**Minimum trigger input**: One attrs class with `kw_only=True` and at least one
attribute where `name != alias` (e.g., `_host` with `alias='host'`), structured
with `Converter(detailed_validation=False)` and a manually registered structure
hook created via `make_dict_structure_fn(cls, c, _cattrs_use_alias=True)`.

## Bug 2: omit_if_default comparison direction inversion

**Trigger condition**: Create a Converter with `omit_if_default=True`. Unstructure
an attrs object where at least one field has a non-default value. With the bug,
`!=` is replaced by `==`, so non-default fields are omitted and default fields are
kept. Structure the result back and the roundtrip fails.

**Why default strategy is insufficient**: The default Converter has
`omit_if_default=False`, so the comparison-inversion bug never triggers. Tests must
explicitly set `omit_if_default=True` AND verify that non-default field values
survive the roundtrip.

**Trigger probability with default strategy**: ~10% (requires explicitly setting
omit_if_default=True AND using non-default field values)

**Minimum trigger input**: One attrs class with at least one field having a default
value. Create an instance where that field has a non-default value. Unstructure with
`omit_if_default=True` and verify the non-default field is present.

## Bug 3: Converter copy loses custom function hooks

**Trigger condition**: Register a custom structure hook using
`register_structure_hook_func` on a Converter. Call `.copy()`. The copy's
FunctionDispatch gets only the default handlers (the last N, via `[-skip:]` instead
of `[:-skip]`), discarding the custom hook. Any structuring that relied on the
custom hook falls back to the default behavior.

**Why default strategy is insufficient**: Most tests use a single Converter instance
and don't test `.copy()`. Even when copy is tested, basic type hooks (registered via
`register_structure_hook`) use the singledispatch path, not FunctionDispatch. Only
hooks registered via `register_structure_hook_func` (which uses FunctionDispatch)
are affected by the copy_to bug.

**Trigger probability with default strategy**: ~5% (requires using .copy() AND
register_structure_hook_func AND verifying the hook is preserved)

**Minimum trigger input**: Register one hook via `register_structure_hook_func`,
copy the converter, verify the copy uses the custom hook by structuring an object
and checking the result differs from default behavior.

## Bug 4: Tagged union custom tag_generator ignored during unstructuring

**Trigger condition**: Use `configure_tagged_union` with a custom `tag_generator`
that returns something different from `cl.__name__` (e.g., `lambda t: t.__name__.lower()`).
The structuring side correctly uses the custom tag, but the unstructuring side stores
`cl.__name__` instead of `tag_generator(cl)`, producing a mismatched tag. Roundtrip
fails because the tag in the unstructured dict doesn't match what the structuring
side expects.

**Why default strategy is insufficient**: The default `tag_generator` is
`lambda t: t.__name__`, which produces the same result as `cl.__name__`. The bug
only triggers when a CUSTOM tag_generator produces different output from the default.
Most union tests use the default tag_generator or don't use tagged unions at all.

**Trigger probability with default strategy**: ~8% (requires using
configure_tagged_union with a custom tag_generator that differs from default)

**Minimum trigger input**: Two attrs classes in a Union. Call
`configure_tagged_union(union, converter, tag_generator=lambda t: t.__name__.lower())`.
Unstructure one member and check the `_type` tag value.
