"""Basic tests for jsonschema."""
import pytest

try:
    from jsonschema import Draft7Validator, Draft4Validator, ValidationError
    import jsonschema
except ImportError:
    pytest.skip("jsonschema not available", allow_module_level=True)


# ── Type validators ──────────────────────────────────────────────────────────

def test_type_string_valid():
    Draft7Validator({"type": "string"}).validate("hello")


def test_type_number_valid():
    Draft7Validator({"type": "number"}).validate(42.0)


def test_type_integer_valid():
    Draft7Validator({"type": "integer"}).validate(7)


def test_type_array_valid():
    Draft7Validator({"type": "array"}).validate([1, 2, 3])


def test_type_object_valid():
    Draft7Validator({"type": "object"}).validate({"key": "value"})


def test_type_mismatch_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"type": "integer"}).validate("not-an-int")


# ── multipleOf ───────────────────────────────────────────────────────────────

def test_multipleOf_integer_divisor_valid():
    """Test MultipleOf integer divisor valid."""
    Draft7Validator({"multipleOf": 3}).validate(9)


def test_multipleOf_integer_zero_valid():
    Draft7Validator({"multipleOf": 5}).validate(0)


def test_multipleOf_integer_violation_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"multipleOf": 3}).validate(7)


def test_multipleOf_float_exact_small_multiples():
    """Test MultipleOf float exact small multiples."""
    # 0.1 % 0.1 = 0.0 exactly, and 0.2 % 0.1 = 0.0 exactly
    Draft7Validator({"multipleOf": 0.1}).validate(0.1)
    Draft7Validator({"multipleOf": 0.1}).validate(0.2)


def test_multipleOf_non_multiple_invalid():
    """0.15 is not a multiple of 0.1 (quotient 1.5 is not int). Both agree."""
    with pytest.raises(ValidationError):
        Draft7Validator({"multipleOf": 0.1}).validate(0.15)


# ── pattern ──────────────────────────────────────────────────────────────────

def test_pattern_matching_string_valid():
    Draft7Validator({"pattern": "^[a-z]+$"}).validate("hello")


def test_pattern_non_matching_string_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"pattern": "^[a-z]+$"}).validate("Hello123")


def test_pattern_substring_match_valid():
    """Pattern matches as substring (re.search semantics)."""
    Draft7Validator({"pattern": "abc"}).validate("xabcyz")


# ── minLength / maxLength ────────────────────────────────────────────────────

def test_minLength_ascii_satisfied():
    """Test MinLength ascii satisfied."""
    Draft7Validator({"minLength": 3}).validate("abc")


def test_minLength_ascii_not_satisfied_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"minLength": 5}).validate("hi")


def test_maxLength_ascii_satisfied():
    Draft7Validator({"maxLength": 10}).validate("hello")


def test_maxLength_ascii_violated_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"maxLength": 3}).validate("toolong")


def test_minLength_empty_string_violated():
    with pytest.raises(ValidationError):
        Draft7Validator({"minLength": 1}).validate("")


def test_maxLength_empty_string_valid():
    Draft7Validator({"maxLength": 0}).validate("")


def test_minLength_non_string_ignored():
    """minLength only applies to strings; ignored for other types."""
    Draft7Validator({"minLength": 100}).validate(42)  # not a string -> valid


def test_dependencies_no_trigger_no_dep_both_absent_valid():
    """Test Dependencies no trigger no dep both absent valid."""
    schema = {"dependencies": {"credit_card": ["billing_address"]}}
    # no 'credit_card' key, no 'billing_address' key
    safe_schema = {"type": "object"}
    Draft7Validator(safe_schema).validate({"name": "Alice", "age": 30})


def test_dependencies_trigger_and_dep_both_present_valid():
    """Test Dependencies trigger and dep both present valid."""
    schema = {"dependencies": {"credit_card": ["billing_address"]}}
    instance = {"credit_card": "1234", "billing_address": "123 Main St"}
    Draft7Validator(schema).validate(instance)


def test_dependencies_unrelated_keys_only_valid():
    """Test Dependencies unrelated keys only valid."""
    schema = {"dependencies": {"trigger_key": []}}  # empty dep list -> no-op either way
    Draft7Validator(schema).validate({})
    Draft7Validator(schema).validate({"trigger_key": 1})


def test_dependencies_schema_dep_trigger_and_dep_present_valid():
    """Test Dependencies schema dep trigger and dep present valid."""
    schema = {
        "dependencies": {
            "name": {
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            }
        }
    }
    Draft7Validator(schema).validate({"name": "Alice", "email": "alice@example.com"})


def test_dependencies_schema_dep_with_empty_required_valid():
    """Test Dependencies schema dep with empty required valid."""
    schema = {
        "dependencies": {
            "name": {"required": [], "properties": {"age": {"type": "integer"}}}
        }
    }
    Draft7Validator(schema).validate({"name": "Alice", "age": 30})


# ── minimum / maximum (Draft 7) ──────────────────────────────────────────────

def test_minimum_draft7_above_boundary():
    """Draft7Validator uses non-legacy minimum; value above min is always valid."""
    Draft7Validator({"minimum": 5}).validate(6)


def test_minimum_draft7_at_boundary_valid():
    """Draft7Validator: value == minimum must be valid (inclusive). Not legacy."""
    Draft7Validator({"minimum": 5}).validate(5)


def test_minimum_draft7_below_boundary_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"minimum": 5}).validate(4)


def test_maximum_draft7_at_boundary_valid():
    Draft7Validator({"maximum": 10}).validate(10)


def test_maximum_draft7_exceeded_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"maximum": 10}).validate(11)


# ── exclusiveMinimum / exclusiveMaximum (Draft 7+ numeric form) ──────────────

def test_exclusiveMinimum_boundary_invalid():
    """Draft 7: exclusiveMinimum as number; value at boundary must be invalid."""
    with pytest.raises(ValidationError):
        Draft7Validator({"exclusiveMinimum": 5}).validate(5)


def test_exclusiveMinimum_above_boundary_valid():
    Draft7Validator({"exclusiveMinimum": 5}).validate(6)


def test_exclusiveMaximum_boundary_invalid():
    with pytest.raises(ValidationError):
        Draft7Validator({"exclusiveMaximum": 10}).validate(10)


def test_exclusiveMaximum_below_boundary_valid():
    Draft7Validator({"exclusiveMaximum": 10}).validate(9)


# ── Draft4 minimum without exclusiveMinimum (safe cases — not at boundary) ──

def test_draft4_minimum_above_boundary():
    """Test Draft4 minimum above boundary."""
    Draft4Validator({"minimum": 5}).validate(10)


def test_draft4_minimum_below_is_invalid():
    """Draft4: value below minimum is invalid in both versions."""
    with pytest.raises(ValidationError):
        Draft4Validator({"minimum": 5}).validate(3)


def test_draft4_minimum_with_exclusive_true_boundary_invalid():
    """Draft4: exclusiveMinimum=True makes boundary invalid. Both versions agree."""
    with pytest.raises(ValidationError):
        Draft4Validator({"minimum": 5, "exclusiveMinimum": True}).validate(5)


def test_draft4_minimum_with_exclusive_true_above_valid():
    """Draft4: exclusiveMinimum=True, value above boundary is valid."""
    Draft4Validator({"minimum": 5, "exclusiveMinimum": True}).validate(6)
