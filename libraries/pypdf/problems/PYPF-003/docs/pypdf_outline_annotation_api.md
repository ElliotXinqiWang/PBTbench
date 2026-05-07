# pypdf 6.9.0 — Outlines, Annotations, and Page Scaling API

This document covers the pypdf API for:
1. PDF outline trees (bookmarks/outlines)
2. Geometric annotations (Polygon, PolyLine, Rectangle, etc.)
3. Page scaling and box manipulation

---

## 1. Outline Items (Bookmarks)

### Overview

PDF outlines (historically called "bookmarks") provide a hierarchical navigation tree. Each item
is an `OutlineItem` (a `Destination` subclass) stored in a linked-list tree structure.

The outline tree is stored in the PDF catalog under `/Outlines`. Each node is a dictionary with:
- `/Title` — display text
- `/Dest` or `/A` — navigation destination
- `/Parent` — reference to the parent node
- `/First` — reference to the first child node
- `/Last` — reference to the last child node
- `/Next` — reference to the next sibling node
- `/Prev` — reference to the previous sibling node
- `/Count` — number of visible descendant items (positive = open, negative = closed)

### The `/Count` Invariant

The `/Count` field encodes both visibility and descendant count:

- A **positive** `/Count` on a node means the node is **open** and has that many visible
  descendant items (direct children plus all open grandchildren, recursively).
- A **negative** `/Count` means the node is **closed** (collapsed in a viewer). The absolute
  value is the total descendants.
- A **zero** `/Count` means no visible descendants.

For an open parent with `n` direct open children (each with 0 open descendants of their own),
the parent's `/Count` equals `n`.

**Key invariant**: After adding `n` items as direct children of an open parent, the parent's
`/Count` must equal `n`. After adding items to the outline root, the root's `/Count` must equal
the total number of top-level items.

### Adding Outline Items

```python
from pypdf import PdfWriter
from pypdf.generic import Fit

writer = PdfWriter()
page0 = writer.add_blank_page(width=612, height=792)
page1 = writer.add_blank_page(width=612, height=792)

# Add a top-level item (attached to root)
chapter1_ref = writer.add_outline_item(
    title="Chapter 1",
    page_number=0,          # zero-based page index
)

# Add a nested item (child of chapter1)
section_ref = writer.add_outline_item(
    title="Section 1.1",
    page_number=0,
    parent=chapter1_ref,    # reference to parent item
)

# Add another top-level item
chapter2_ref = writer.add_outline_item("Chapter 2", page_number=1)
```

**Signature**:
```python
def add_outline_item(
    title: str,
    page_number: Union[None, PageObject, IndirectObject, int],
    parent: Union[None, TreeObject, IndirectObject] = None,
    before: Union[None, TreeObject, IndirectObject] = None,
    color: Optional[Union[tuple[float, float, float], str]] = None,
    bold: bool = False,
    italic: bool = False,
    fit: Fit = PAGE_FIT,
    is_open: bool = True,
) -> IndirectObject
```

- `parent`: if `None`, adds at root level; otherwise, nests under the given item.
- `is_open`: if `True` (default), the outline item is expanded in viewers. This affects
  how the `/Count` of ancestor nodes is updated.
- Returns an `IndirectObject` referencing the new outline item.

### Reading Outlines

```python
from pypdf import PdfReader

reader = PdfReader(stream)
outline = reader.outline
# Returns a list; nested items appear as sublists:
# [item1, [child1, child2, ...], item2, ...]
```

The `reader.outline` property traverses the outline tree and returns a flat list where nested
children are represented as nested Python lists.

### Outline Tree Structure Invariants

1. **`/Count` consistency**: For an open item, `/Count` = number of visible descendants.
2. **Linked list integrity**: Every node's `/Next`/`/Prev` pointers must form a consistent
   doubly-linked list within its level.
3. **Parent references**: Every child's `/Parent` must point to the correct parent node.
4. **`/First`/`/Last` pointers**: The parent's `/First` points to the first child and `/Last`
   to the last child in the sibling linked list.

### Using `get_outline_root()`

```python
root = writer.get_outline_root()
# TreeObject — the root of the outline tree
root_count = int(root.get("/Count", 0))
# This should equal the number of top-level items added
```

### Supported `Fit` Types

When creating outline items, the `fit` parameter controls how the destination page is displayed:

| Fit type | Description |
|---|---|
| `Fit.fit()` | Fit entire page (default) |
| `Fit.xyz(left, top, zoom)` | Specific coordinates and zoom |
| `Fit.fit_horizontally(top)` | Fit width, scroll to top |
| `Fit.fit_vertically(left)` | Fit height, scroll to left |
| `Fit.fit_rectangle(left, bottom, right, top)` | Fit specific rectangle |

---

## 2. Annotations

### Overview

pypdf supports creating various annotation types via the `pypdf.annotations` module. Each
annotation is a dictionary subclassing `AnnotationDictionary` and ultimately stored in the
page's `/Annots` array.

### Adding Annotations to a Page

```python
from pypdf import PdfWriter
from pypdf.annotations import Rectangle, Highlight, Polygon, PolyLine, Text, FreeText, Line

writer = PdfWriter()
page = writer.add_blank_page(width=612, height=792)

ann = Rectangle(rect=(100, 200, 300, 400))
added = writer.add_annotation(page_number=0, annotation=ann)
```

**Signature**:
```python
def add_annotation(
    page_number: Union[int, PageObject],
    annotation: dict[str, Any],
) -> DictionaryObject
```

Returns the inserted `DictionaryObject`. The returned object has an `indirect_reference`
that can be used to create popup annotations referencing it.

### Annotation `/Rect` Invariant

Every annotation has a `/Rect` field — an `ArrayObject` of four numbers `[x1, y1, x2, y2]`
in user space coordinates (lower-left to upper-right):

- `x1` (index 0): left x-coordinate
- `y1` (index 1): bottom y-coordinate
- `x2` (index 2): right x-coordinate
- `y2` (index 3): top y-coordinate

**Invariant**: `x1 <= x2` and `y1 <= y2` (lower-left must be ≤ upper-right).

### Geometric Annotation Types

#### Rectangle (Square in PDF spec)

```python
from pypdf.annotations import Rectangle

ann = Rectangle(
    rect=(x1, y1, x2, y2),
    interior_color=None,  # Optional hex color string e.g. "ff0000"
)
```

The `/Rect` is set explicitly by the caller.

#### Ellipse (Circle in PDF spec)

```python
from pypdf.annotations import Ellipse

ann = Ellipse(
    rect=(x1, y1, x2, y2),
    interior_color=None,
)
```

#### Polygon

```python
from pypdf.annotations import Polygon

ann = Polygon(
    vertices=[(x0, y0), (x1, y1), (x2, y2), ...],  # at least 1 vertex
)
```

The `/Rect` is **automatically computed** as the bounding box of all vertices:
- `x_min` = minimum x among all vertices → `/Rect[0]`
- `y_min` = minimum y among all vertices → `/Rect[1]`
- `x_max` = maximum x among all vertices → `/Rect[2]`
- `y_max` = maximum y among all vertices → `/Rect[3]`

**Bounding box invariant**: For every vertex `(vx, vy)` in `vertices`,
`rect[0] <= vx <= rect[2]` and `rect[1] <= vy <= rect[3]`.

The `/Vertices` array stores the raw vertex coordinates as flat `[x0, y0, x1, y1, ...]`.

#### PolyLine

```python
from pypdf.annotations import PolyLine

ann = PolyLine(
    vertices=[(x0, y0), (x1, y1), ...],  # at least 1 vertex
)
```

Same `/Rect` bounding box behavior as `Polygon`. The `/Vertices` array stores the raw
coordinates. The bounding box must contain all vertices: `x_max = max(vx for vx, _ in vertices)`.

#### Line

```python
from pypdf.annotations import Line

ann = Line(
    p1=(x1, y1),
    p2=(x2, y2),
    rect=(xr1, yr1, xr2, yr2),  # bounding box (caller provided)
    text="",
)
```

#### Highlight

```python
from pypdf.annotations import Highlight
from pypdf.generic import ArrayObject, FloatObject

# quad_points is a flat array of 8 floats: 4 corners of the highlighted quadrilateral
quad = ArrayObject([FloatObject(v) for v in [x1, y1, x2, y1, x1, y2, x2, y2]])
ann = Highlight(
    rect=(x1, y1, x2, y2),
    quad_points=quad,
    highlight_color="ff0000",
)
```

#### Text (Note)

```python
from pypdf.annotations import Text

ann = Text(
    rect=(x1, y1, x2, y2),
    text="Annotation text content",
    open=False,
)
```

#### FreeText

```python
from pypdf.annotations import FreeText

ann = FreeText(
    text="Text to display",
    rect=(x1, y1, x2, y2),
    font="Helvetica",
    bold=False,
    italic=False,
    font_size="14pt",
    font_color="000000",
    border_color="000000",
    background_color="ffffff",
)
```

### Annotation Flags

```python
from pypdf.constants import AnnotationFlag

ann.flags = AnnotationFlag.PRINT  # visible when printed
ann.flags = AnnotationFlag.HIDDEN  # invisible
```

### Popup Annotations

```python
from pypdf.annotations import Popup

note = writer.add_annotation(0, Text(rect=(100, 100, 200, 200), text="Note"))
popup = Popup(
    rect=(200, 200, 400, 400),
    open=True,
    parent=note,  # link popup to its parent
)
writer.add_annotation(0, popup)
```

---

## 3. Page Scaling

### `PageObject.scale(sx, sy)`

Scale a page by independent horizontal and vertical factors:

```python
page = writer.pages[0]
page.scale(sx=2.0, sy=3.0)  # double width, triple height
```

This method:
1. Applies a transformation matrix `(sx, 0, 0, sy, 0, 0)` to the content stream.
2. Scales all page boxes (mediabox, cropbox, bleedbox, trimbox, artbox) using
   `box.scale(sx, sy)`.
3. Scales any annotation `/Rect` values: each coordinate at index `i` is multiplied
   by `sx` (for x-coords: indices 0 and 2) or `sy` (for y-coords: indices 1 and 3).

**Page box invariant after scale**: For each page box rectangle `B`:
- `B.left_after = B.left_before * sx`
- `B.bottom_after = B.bottom_before * sy`
- `B.right_after = B.right_before * sx`
- `B.top_after = B.top_before * sy`

**Annotation invariant after scale**: For each annotation rectangle `/Rect = [x1, y1, x2, y2]`:
- `rect[0]_after = rect[0]_before * sx`  (left x)
- `rect[1]_after = rect[1]_before * sy`  (bottom y)
- `rect[2]_after = rect[2]_before * sx`  (right x)
- `rect[3]_after = rect[3]_before * sy`  (top y)

### `RectangleObject.scale(sx, sy)`

The `RectangleObject` (used for page boxes) supports direct scaling:

```python
from pypdf.generic._rectangle import RectangleObject

rect = RectangleObject((x1, y1, x2, y2))
scaled = rect.scale(sx, sy)
# Returns a new RectangleObject with:
# scaled.left   = x1 * sx
# scaled.bottom = y1 * sy
# scaled.right  = x2 * sx
# scaled.top    = y2 * sy
```

The scaled rectangle must satisfy:
- `scaled.width == original.width * sx`
- `scaled.height == original.height * sy`
- `scaled.bottom == original.bottom * sy`  (not `original.top * sy`)

### `PageObject.scale_by(factor)`

Uniform scaling (same sx and sy):

```python
page.scale_by(2.0)  # equivalent to page.scale(2.0, 2.0)
```

### `PageObject.scale_to(width, height)`

Scale page to exact dimensions:

```python
page.scale_to(width=595.0, height=842.0)  # scale to A4
```

Internally computes `sx = width / mediabox.width`, `sy = height / mediabox.height`.

---

## 4. Page Box Properties

pypdf exposes five page boxes as `RectangleObject` properties:

```python
page.mediabox  # /MediaBox — full page boundary (required)
page.cropbox   # /CropBox — visible region (fallback to mediabox)
page.bleedbox  # /BleedBox — printing bleed area
page.trimbox   # /TrimBox — final trimmed size
page.artbox    # /ArtBox — meaningful content area
```

Each is a `RectangleObject` with:
- `rect.left`   — left x (index 0)
- `rect.bottom` — bottom y (index 1)
- `rect.right`  — right x (index 2)
- `rect.top`    — top y (index 3)
- `rect.width`  — `right - left`
- `rect.height` — `top - bottom`
- `rect.lower_left` — `(left, bottom)` tuple
- `rect.upper_right` — `(right, top)` tuple

**Standard page coordinates**: PDF uses a coordinate system with origin at lower-left.
A standard US Letter page has `mediabox = (0, 0, 612, 792)`.

### Accessing Page Geometry

```python
reader = PdfReader(buf)
page = reader.pages[0]
mb = page.mediabox
print(f"Width: {mb.width}, Height: {mb.height}")
print(f"Lower-left: {mb.lower_left}")  # (0, 0) for standard pages
print(f"Upper-right: {mb.upper_right}")  # (612, 792) for Letter
```

---

## 5. Writing and Reading PDF

Always use `io.BytesIO` for in-memory operations:

```python
import io
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
page = writer.add_blank_page(width=612, height=792)

# Add content, annotations, outlines...

buf = io.BytesIO()
writer.write(buf)
buf.seek(0)

reader = PdfReader(buf)
```

### Page Annotations Access

```python
# Reading annotations from a reader
page = reader.pages[0]
for ann_ref in (page.annotations or []):
    ann = ann_ref.get_object()
    subtype = ann.get("/Subtype")
    rect = ann.get("/Rect")
    print(f"Annotation type: {subtype}, rect: {list(rect)}")
```

```python
# Accessing annotations from a writer (after adding them)
page = writer.pages[0]
for ann_ref in (page.annotations or []):
    ann = ann_ref.get_object()
    rect = ann.get("/Rect")
    print(f"rect: {[float(rect[i]) for i in range(4)]}")
```

---

## 6. Common PBT Properties for pypdf

When writing property-based tests for pypdf, consider these invariants:

### Outline invariants
- **Count consistency**: `parent.get_object().get("/Count") == n_children` for open parent
  after adding `n_children` items.
- **Traversal completeness**: `len(reader.outline)` reflects the number of top-level items.
- **Nesting depth**: outline items added with `parent=X` appear as children of X.

### Annotation bounding box invariants
- **Polygon/PolyLine containment**: For every vertex `(vx, vy)`, `x_min_rect <= vx <= x_max_rect`
  and `y_min_rect <= vy <= y_max_rect`.
- **Rect ordering**: `rect[0] <= rect[2]` (left <= right) and `rect[1] <= rect[3]` (bottom <= top).

### Page scaling invariants
- **Box scaling**: `new_rect = old_rect.scale(sx, sy)` should satisfy `new_rect.bottom == old_rect.bottom * sy`.
- **Annotation scaling**: After `page.scale(sx, sy)`, each annotation's `rect[2] == original_rect[2] * sx`.
- **Proportional width/height**: `scaled.width == original.width * sx`.
