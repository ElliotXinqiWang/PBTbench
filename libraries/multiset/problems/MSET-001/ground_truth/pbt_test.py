"""
Ground-truth PBT for MSET-001.

Property: After combine() reduces an element's multiplicity to exactly 0,
the element must be absent from the multiset: not in _elements, not in ms,
and not counted in len(ms).

Buggy behaviour: `new_multiplicity < 0` instead of `<= 0` means elements
that reach exactly 0 are left as ghost entries in _elements.
"""
from hypothesis import given, settings
from hypothesis import strategies as st
from multiset import Multiset


@settings(max_examples=500, deadline=None)
@given(
    element=st.text(min_size=1, max_size=5, alphabet="abcde"),
    n=st.integers(min_value=1, max_value=20),
)
def test_exact_cancellation_removes_element(element, n):
    """Combining with exact negation must remove the element entirely."""
    ms = Multiset({element: n})
    result = ms.combine({element: -n})

    assert element not in result, (
        f"After combine({{'{element}': -{n}}}), element '{element}' should be absent "
        f"but is still present with count {result[element]}"
    )
    assert result[element] == 0, (
        f"result['{element}'] should be 0 (absent) but is {result[element]}"
    )
    assert len(result) == 0, (
        f"After exact cancellation, len should be 0 but is {len(result)}"
    )


@settings(max_examples=500, deadline=None)
@given(
    element=st.text(min_size=1, max_size=5, alphabet="abcde"),
    n=st.integers(min_value=1, max_value=20),
    extra=st.integers(min_value=1, max_value=10),
)
def test_partial_reduction_keeps_element(element, n, extra):
    """Combining with less than full negation must keep element with reduced count."""
    ms = Multiset({element: n + extra})
    result = ms.combine({element: -n})

    assert element in result, (
        f"After partial reduce, '{element}' should remain with count {extra}"
    )
    assert result[element] == extra, (
        f"Expected count {extra}, got {result[element]}"
    )


@settings(max_examples=500, deadline=None)
@given(
    elems=st.dictionaries(
        st.text(min_size=1, max_size=3, alphabet="abcde"),
        st.integers(min_value=1, max_value=10),
        min_size=1, max_size=4,
    )
)
def test_internal_elements_invariant(elems):
    """All elements in _elements must have positive multiplicity."""
    ms = Multiset(elems)
    # Combine each element with its exact negation, one at a time
    for elem, count in elems.items():
        ms = ms.combine({elem: -count})

    for elem, mult in ms._elements.items():
        assert mult > 0, (
            f"Ghost element '{elem}' found with multiplicity {mult} in _elements"
        )
    assert len(ms) == 0, f"Expected empty multiset, got len={len(ms)}"
