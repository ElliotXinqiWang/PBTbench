# Strategy Specification for CTRS-004

## Bug 1: BaseConverter.copy() loses custom unstructure hooks

**Trigger condition**: Register a custom unstructure hook via
`register_unstructure_hook_func` (which uses FunctionDispatch internally). Call
`.copy()` on the converter. Use the copy to unstructure objects. The custom hook
is silently dropped because the wrong skip count is used in `copy_to`.

**Why default strategy is insufficient**: Most PBT tests use a single converter
instance and never call `.copy()`. Even when `.copy()` is tested, tests may only
check structure hooks (registered via `register_structure_hook`) which use the
singledispatch path and are not affected by the bug. The bug specifically affects
`register_unstructure_hook_func` (FunctionDispatch path) combined with `.copy()`.

**Trigger probability with default strategy**: ~3% (requires `.copy()` +
`register_unstructure_hook_func` + verifying hook is preserved)

**Minimum trigger input**: Register one hook via `register_unstructure_hook_func`
that transforms output (e.g., doubles a field). Copy the converter. Verify the
copy produces the transformed output, not the default.

## Bug 2: make_dict_unstructure_fn inverts _cattrs_use_alias for key names

**Trigger condition**: Call `make_dict_unstructure_fn(..., _cattrs_use_alias=True)`
(or use `Converter(use_alias=True)`) on a class where at least one field has an
alias different from its name (e.g., `_host` with `alias='host'`). The generated
function uses internal attribute names (`_host`) as dict keys instead of aliases
(`host`).

**Why default strategy is insufficient**: The default `_cattrs_use_alias` behavior
depends on the converter setting. By default, `use_alias=False`, so the bug
condition (`_cattrs_use_alias=True`) is not exercised. The aliased-attribute pattern
(private name `_x` with public alias `x`) is an advanced feature most tests don't
cover.

**Trigger probability with default strategy**: ~5% (requires `use_alias=True` AND
alias != name)

**Minimum trigger input**: One attrs class with attribute `_host` and `alias='host'`.
Create a Converter with `use_alias=True` (or pass `_cattrs_use_alias=True` to
`make_dict_unstructure_fn`). Unstructure an instance. Assert the result dict has
key `host` (the alias), not `_host` (the internal name).

## Bug 3: include_subclasses loses subclass fields in typed containers

**Trigger condition**: After calling `include_subclasses(BaseClass, converter)`,
unstructure a container typed as `List[BaseClass]` that contains subclass instances.
The subclass fields (not present in BaseClass) are silently dropped.

**Why this happens**: The `unstruct_hook` for each class uses `isinstance(val, _cl)`
instead of `val.__class__ is _cl`. When the Animal hook processes a Dog instance
(because the list is `List[Animal]`), `isinstance(dog, Animal)` is True, so the
Animal base hook is used — dropping Dog's breed field. The correct `val.__class__
is _cl` would be False for a Dog, dispatching to the full Dog hook.

**Why default strategy is insufficient**: Most tests unstructure instances directly
(by their exact type), not through typed containers. The bug only manifests when
unstructuring through a base-class-typed collection, which requires:
1. Using `include_subclasses`
2. Having a container class with `List[BaseClass]`
3. Putting subclass instances in the container

**Trigger probability with default strategy**: ~2% (requires include_subclasses +
heterogeneous typed container + subclass instances)

**Minimum trigger input**: Base class `Animal(name)`, subclass `Dog(Animal, breed)`,
container class `Zoo(animals: List[Animal])`. After `include_subclasses(Animal, c)`,
unstructure `Zoo([Dog('Rex', 'Lab')])`. Assert `breed` is present in the result.

## Bug 4: omit_if_default + rename uses original key instead of renamed key

**Trigger condition**: Use `make_dict_unstructure_fn` with
`_cattrs_omit_if_default=True` AND at least one field with a `rename` override.
Unstructure an object where the renamed field has a non-default value. The output
dict uses the original attribute name, not the renamed key.

**Why default strategy is insufficient**: This requires combining two non-default
settings: `omit_if_default=True` AND explicit rename overrides. The rename override
feature is an advanced API (`override(rename='new_name')`). Most PBT tests don't
use explicit renames.

**Trigger probability with default strategy**: ~3% (requires omit_if_default=True +
non-default field value + rename override on that field)

**Minimum trigger input**: One attrs class with a field with a default (e.g.,
`host="localhost"`). Call `make_dict_unstructure_fn(cls, c, _cattrs_omit_if_default=True,
host=override(rename="server_host"))`. Unstructure an instance with `host="prod.com"`.
Assert the result has key `server_host`, not `host`.
