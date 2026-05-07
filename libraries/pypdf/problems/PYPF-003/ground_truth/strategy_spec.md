# Strategy Specification — PYPF-003

## Bug 1: `inc_parent_counter_outline` subtraction error

**Location**: `pypdf/generic/_data_structures.py:754`

**Trigger condition**: Add at least 2 outline items as children of an open parent item. The parent item's `/Count` will be wrong (not equal to the number of children added).

**Why default strategy is insufficient**: A baseline that only adds flat (root-level) outline items with 1 item total might accidentally pass. You need at least 2 items so the alternating error becomes detectable (with 1 child: count = -1 ≠ 1; with 2 children starting from -1: abs(-1)=1 → 1-1=0 ≠ 2).

**Trigger probability with default strategy**: ~100% for `n_children >= 2` because the wrong `/Count` value is always wrong. However, if the test only uses exactly 1 item at root level (flat), the error (-1) is still detectable (≠ 1).

**Ground truth strategy**:
- `n_children = st.integers(min_value=2, max_value=8)`
- Add parent item at root, then add `n_children` children under it
- Assert `parent_obj.get("/Count") == n_children`

**Minimum trigger example**:
```python
writer = PdfWriter()
writer.add_blank_page(width=612, height=792)
parent = writer.add_outline_item("P", 0)
writer.add_outline_item("C1", 0, parent=parent)
writer.add_outline_item("C2", 0, parent=parent)
assert int(parent.get_object().get("/Count")) == 2  # fails: gets 0
```

---

## Bug 2: `_get_bounding_rectangle` uses `min` for `x_max`

**Location**: `pypdf/annotations/_markup_annotations.py:37`

**Trigger condition**: Create a `Polygon` or `PolyLine` annotation with at least 2 vertices that have different x-coordinates. The `/Rect` right coordinate will be the minimum x, not the maximum.

**Why default strategy is insufficient**: A test using a single vertex or vertices all at the same x-coordinate would not detect the bug. The strategy must generate vertices with genuinely different x-coordinates.

**Trigger probability with default strategy**: ~100% for any non-degenerate polygon (all vertices at same x = degenerate case). For random vertices in a plane, probability that all vertices share x ≈ 0%, so nearly any polygon triggers.

**Ground truth strategy**:
- Generate 3-8 vertices with `st.floats(0, 500)` x-coordinates
- `assume(max(xs) > min(xs))` to ensure spread
- Assert `float(polygon["/Rect"][2]) == max(vx for vx, _ in vertices)`

**Minimum trigger example**:
```python
poly = Polygon(vertices=[(0, 0), (100, 50), (50, 100)])
rect = list(poly["/Rect"])
assert rect[2] == 100  # fails: gets 0
```

---

## Bug 3: `RectangleObject.scale` uses `self.top` for bottom coordinate

**Location**: `pypdf/generic/_rectangle.py:37`

**Trigger condition**: Call `page.scale(sx, sy)` or `rect.scale(sx, sy)` on any rectangle where `bottom != top` (any non-degenerate rectangle). The resulting `bottom` coordinate will equal `original_top * sy` instead of `original_bottom * sy`.

**Why default strategy is insufficient**: If `bottom == top` (degenerate zero-height rectangle), the bug is invisible. For standard PDF pages where `bottom=0`, the bug produces `bottom = top * sy` (nonzero), which is dramatically wrong. Any test on a real page with a standard mediabox will trigger.

**Trigger probability with default strategy**: ~100% for any standard-sized page (bottom=0 is universal for letter/A4). The bottom becomes `top * sy` instead of 0.

**Ground truth strategy**:
- `bottom = st.floats(0, 200)`, `top = st.floats(400, 900)`, `sy = st.floats(0.1, 4.0)`
- Create a `RectangleObject((0, bottom, 100, top)).scale(1.0, sy)`
- Assert `scaled.bottom == bottom * sy`

**Minimum trigger example**:
```python
from pypdf.generic._rectangle import RectangleObject
r = RectangleObject((0, 0, 100, 500))
s = r.scale(1.0, 2.0)
assert float(s.bottom) == 0.0  # fails: gets 1000.0 (= 500 * 2)
```

---

## Bug 4: `page.scale()` uses `sy` instead of `sx` for annotation `rect[2]`

**Location**: `pypdf/_page.py:1540`

**Trigger condition**: Call `page.scale(sx, sy)` on a page that has at least one annotation with a `/Rect`, where `sx != sy`. The right x-coordinate (`rect[2]`) of each annotation will be scaled by `sy` instead of `sx`.

**Why default strategy is insufficient**: If `sx == sy` (uniform scaling), the bug is invisible because `x * sx == x * sy`. The test must use non-uniform scaling (`sx != sy`).

**Trigger probability with default strategy**: For random `sx` and `sy`: probability that `sx == sy` ≈ 0%, so nearly any non-uniform scale triggers. But the baseline might use `scale_by(factor)` which calls `scale(factor, factor)` (uniform, doesn't trigger).

**Ground truth strategy**:
- `sx = st.floats(0.5, 4.0)`, `sy = st.floats(0.5, 4.0)`, `assume(abs(sx - sy) > 0.05)`
- Add a `Rectangle` annotation, call `page.scale(sx, sy)`
- Assert `float(ann_obj["/Rect"][2]) == original_x2 * sx`

**Minimum trigger example**:
```python
writer = PdfWriter()
page = writer.add_blank_page(width=612, height=792)
writer.add_annotation(0, PdfRect(rect=(100, 100, 300, 400)))
writer.pages[0].scale(2.0, 3.0)
ann = writer.pages[0].annotations[0].get_object()
assert float(ann["/Rect"][2]) == 600.0  # fails: gets 900.0 (= 300 * 3 instead of * 2)
```
