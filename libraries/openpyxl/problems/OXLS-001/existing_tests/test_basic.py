"""Basic tests for openpyxl."""
import pytest
from openpyxl.formula.translate import Translator, TranslatorError
from openpyxl.worksheet.cell_range import CellRange


# ─── Translator: basic formula translation ────────────────────────────────────

def test_translate_simple_cell_ref():
    """Translating a simple relative reference."""
    t = Translator("=A1", "A1")
    assert t.translate_formula("B2") == "=B2"


def test_translate_absolute_ref_unchanged():
    """Absolute references should not change."""
    t = Translator("=$A$1", "C5")
    assert t.translate_formula("D6") == "=$A$1"


def test_translate_mixed_ref():
    """Mixed absolute/relative references."""
    t = Translator("=$A1", "A1")
    assert t.translate_formula("A3") == "=$A3"


def test_translate_range_ref():
    """Translating a range reference."""
    t = Translator("=SUM(A1:B2)", "A1")
    assert t.translate_formula("C1") == "=SUM(C1:D2)"


def test_translate_col_range():
    """Translating a whole-column range like A:B."""
    t = Translator("=SUM(A:B)", "A1")
    result = t.translate_formula("C1")
    assert result == "=SUM(C:D)"


def test_translate_no_change_same_origin():
    """Translating to the same cell should produce the same formula."""
    formula = "=A1+B2"
    t = Translator(formula, "A1")
    assert t.translate_formula("A1") == formula


def test_translate_negative_col_delta():
    """Translating left."""
    t = Translator("=D5", "C4")
    assert t.translate_formula("A4") == "=B5"


def test_translate_out_of_range_raises():
    """TranslatorError raised when translation would go out of bounds."""
    t = Translator("=A1", "B2")
    with pytest.raises(TranslatorError):
        t.translate_formula("A2")


# ─── CellRange: construction ──────────────────────────────────────────────────

def test_cellrange_construction_from_string():
    cr = CellRange("B2:D5")
    assert cr.min_col == 2   # B
    assert cr.min_row == 2
    assert cr.max_col == 4   # D
    assert cr.max_row == 5


def test_cellrange_construction_kwargs():
    cr = CellRange(min_col=1, min_row=1, max_col=3, max_row=3)
    assert str(cr) == "A1:C3"


def test_cellrange_single_cell():
    cr = CellRange("C4")
    assert cr.min_col == cr.max_col == 3
    assert cr.min_row == cr.max_row == 4


def test_cellrange_size():
    cr = CellRange("A1:E5")
    assert cr.size == {"columns": 5, "rows": 5}


def test_cellrange_size_single():
    cr = CellRange("B3")
    assert cr.size == {"columns": 1, "rows": 1}


# ─── CellRange: shift ─────────────────────────────────────────────────────────

def test_shift_col_and_row():
    """Shift in both dimensions simultaneously."""
    cr = CellRange("A1:C3")
    cr.shift(col_shift=1, row_shift=1)
    assert str(cr) == "B2:D4"


def test_shift_zero():
    """Shift by zero should not change the range."""
    cr = CellRange("B2:D4")
    cr.shift(col_shift=0, row_shift=0)
    assert str(cr) == "B2:D4"


def test_shift_preserves_size():
    """Shift should preserve the range size."""
    cr = CellRange("A1:C3")
    original_size = cr.size.copy()
    cr.shift(col_shift=2, row_shift=2)
    assert cr.size == original_size


def test_shift_negative():
    """Shift with negative values (moving up/left)."""
    cr = CellRange("D4:F6")
    cr.shift(col_shift=-1, row_shift=-1)
    assert str(cr) == "C3:E5"


def test_shift_invalid_raises():
    cr = CellRange("A1:C3")
    with pytest.raises(ValueError):
        cr.shift(col_shift=-1, row_shift=0)


# ─── CellRange: expand ────────────────────────────────────────────────────────

def test_expand_left():
    """Expanding left decreases min_col."""
    cr = CellRange("C3:E5")
    orig_min_col = cr.min_col
    cr.expand(left=2)
    assert cr.min_col == orig_min_col - 2
    assert cr.max_col == 5  # max_col unchanged


def test_expand_right():
    """Expanding right increases max_col."""
    cr = CellRange("A1:C3")
    orig_max_col = cr.max_col
    cr.expand(right=2)
    assert cr.max_col == orig_max_col + 2
    assert cr.min_col == 1  # min_col unchanged


def test_expand_zero_noop():
    cr = CellRange("B2:D4")
    cr_str = str(cr)
    cr.expand(right=0, down=0, left=0, up=0)
    assert str(cr) == cr_str


# ─── CellRange: shrink ────────────────────────────────────────────────────────

def test_shrink_basic():
    cr = CellRange("A1:E5")
    cr.shrink(right=1, bottom=1)
    assert cr.max_col == 4
    assert cr.max_row == 4


# ─── CellRange: set operations ────────────────────────────────────────────────

def test_union_basic():
    a = CellRange("A1:B2")
    b = CellRange("D3:E4")
    u = a.union(b)
    assert str(u) == "A1:E4"


def test_union_commutative():
    a = CellRange("A1:C3")
    b = CellRange("B2:D4")
    assert a.union(b) == b.union(a)


def test_intersection_overlap():
    """Overlapping ranges intersect correctly."""
    a = CellRange("A1:C5")
    b = CellRange("B2:E6")
    result = a.intersection(b)
    assert str(result) == "B2:C5"


def test_isdisjoint_clearly_separate():
    """Ranges with a gap are clearly disjoint."""
    a = CellRange("A1:B2")
    b = CellRange("D1:E2")  # Gap at column C
    assert a.isdisjoint(b)


def test_isdisjoint_overlapping():
    """Overlapping ranges are not disjoint."""
    a = CellRange("A1:C3")
    b = CellRange("B2:D4")
    assert not a.isdisjoint(b)


def test_issubset():
    outer = CellRange("A1:E5")
    inner = CellRange("B2:D4")
    assert inner.issubset(outer)
    assert not outer.issubset(inner)


def test_equality():
    a = CellRange("B2:D4")
    b = CellRange("B2:D4")
    assert a == b


def test_inequality():
    a = CellRange("A1:C3")
    b = CellRange("A1:C4")
    assert a != b
