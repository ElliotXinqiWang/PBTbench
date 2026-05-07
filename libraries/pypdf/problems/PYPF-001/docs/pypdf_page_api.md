# pypdf Page API Documentation

**pypdf version**: 6.9.0
**Source**: https://pypdf.readthedocs.io/

pypdf is a pure-Python PDF library capable of splitting, merging, cropping,
and transforming PDF pages, as well as reading and writing document metadata.

---

## Core Classes

### PdfWriter

`PdfWriter` creates new PDF files or modifies existing ones by managing a collection
of page objects.

```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
# Clone from existing PDF
writer = PdfWriter(clone_from="existing.pdf")
```

**Key methods:**

- `add_blank_page(width, height) -> PageObject` — Add a new blank page.
- `add_page(page) -> PageObject` — Copy a page from another document into this writer.
- `append(fileobj, pages=None, import_outline=True) -> None` — Append all (or selected)
  pages from another PDF.
- `write(stream) -> (bool, IO)` — Serialize the PDF to a stream or file.
- `pages` — List-like access to all pages: `writer.pages[0]`, `writer.pages[-1]`.
- `metadata` — Access or set document metadata (DocumentInformation).
- `add_metadata(infos: dict) -> None` — Update document metadata fields.

### PdfReader

`PdfReader` opens and parses existing PDF files.

```python
reader = PdfReader("file.pdf")
reader = PdfReader(io.BytesIO(pdf_bytes))
```

**Key properties:**

- `pages` — Sequence of `PageObject` instances.
- `metadata` — `DocumentInformation` with title, author, subject, keywords, etc.
- `named_destinations` — Dict of named destinations for links/bookmarks.

---

## PageObject

`PageObject` represents a single PDF page. Pages attached to a `PdfWriter` can be
modified; pages from a `PdfReader` should be treated as read-only.

### Rotation

PDF pages carry a `/Rotate` entry that specifies the clockwise rotation applied when
rendering. Valid values are **0, 90, 180, and 270** (multiples of 90 degrees).

#### `page.rotation` (property, read/write)

```python
r = page.rotation        # returns int: 0, 90, 180, or 270
page.rotation = 270      # set directly; input is rounded to nearest 90°, clamped to [0,360)
```

The setter normalizes any input value to the nearest 90-degree multiple in {0, 90, 180, 270}.
For example, `page.rotation = 91` stores 90; `page.rotation = 271` stores 270.

The setter formula ensures the stored value is always in the valid set {0, 90, 180, 270}:
any rotation of 0 maps to 0, 90 maps to 90, 180 maps to 180, 270 maps to 270.

#### `page.rotate(angle: int) -> PageObject`

```python
page.rotate(90)   # rotate 90° clockwise
page.rotate(270)  # rotate 270° clockwise (= 90° counter-clockwise)
```

Rotate the page clockwise by `angle` degrees. The angle must be a multiple of 90.
This method **accumulates** with the existing rotation: if the page already has
`/Rotate = 90` and you call `rotate(180)`, the result is `/Rotate = 270`.

Multiple calls to `rotate()` accumulate: `rotate(90)` followed by `rotate(90)` gives
`/Rotate = 180`.

**Invariant**: For any valid starting rotation `r` and any multiple-of-90 angle `a`,
the resulting rotation should equal `r + a` (before any PDF viewer normalization).
In particular, `rotate(270)` from `/Rotate = 0` should produce `/Rotate = 270`.

#### `page.transfer_rotation_to_content() -> None`

Apply the page's `/Rotate` value directly to the content stream (as a transformation
matrix), then reset `/Rotate` to 0. Useful before merging pages to normalize their
orientation. Uses the `rotation` setter internally.

---

### Page Merging

pypdf supports overlaying the content of one page onto another, combining their
content streams and resolving resource name conflicts.

#### `page.merge_page(page2, expand=False, over=True) -> None`

```python
page1.merge_page(page2)              # overlay page2 ON TOP of page1 (default)
page1.merge_page(page2, over=True)   # same: page2 drawn on top
page1.merge_page(page2, over=False)  # page2 drawn UNDER page1
```

Merge `page2`'s content stream into `page1`. Resource references (fonts, images,
extended graphics states) are merged from both pages.

**Compositing semantics** (critical invariant):

- `over=True` (default): `page2` content is drawn ON TOP of `page1`. In the merged
  content stream, page2's operations appear **after** page1's operations.
- `over=False`: `page2` content is drawn UNDER `page1`. In the merged content stream,
  page2's operations appear **before** page1's operations.

Formally, if `page1` has content bytes `C1` and `page2` has content bytes `C2`, then:
- After `merge_page(page2, over=True)`:  stream order = `[q C1 Q] [q C2 Q]`
- After `merge_page(page2, over=False)`: stream order = `[q C2 Q] [q C1 Q]`

This ordering directly determines visual layering: content appearing later in the
stream is drawn on top of content appearing earlier.

**Resource isolation** (critical invariant):

If both pages have a resource with the same name (e.g., both define font `/F1`),
pypdf must avoid collision. The convention is:
1. Keep `page1`'s `/F1` under the original name `/F1`.
2. Rename `page2`'s `/F1` to a unique name `/F1-0` (or `/F1-1`, etc.).
3. **Update all references** to `/F1` in `page2`'s content stream to the new name `/F1-0`.

After merging, every resource name used in the merged content stream must exist as a
key in the merged resource dictionary. Specifically, page2's content stream must use
the renamed key (`/F1-0`), not the original name (`/F1`).

**Graphics state isolation**: Each page's content stream is wrapped in `q`/`Q` operators
(save/restore graphics state) to prevent state leakage between pages.

#### Related merge variants

```python
page1.merge_transformed_page(page2, ctm)   # merge with a transformation matrix applied
page1.merge_scaled_page(page2, scale)       # merge with uniform scaling
page1.merge_rotated_page(page2, rotation)   # merge with rotation applied
page1.merge_translated_page(page2, tx, ty)  # merge with translation
```

All variants support the `over` and `expand` parameters.

---

### Content Stream Access

```python
content = page.get_contents()     # returns ContentStream or None
raw_bytes = content.get_data()    # bytes of the content stream
ops = content.operations          # list of (operands, operator) tuples
```

The content stream is a sequence of PDF graphics operators. Common operators:
- `BT`/`ET` — begin/end text object
- `Tf` — select font (e.g., `/F1 12 Tf`)
- `Tj` — show text
- `cm` — concatenate transformation matrix
- `q`/`Q` — save/restore graphics state

---

### Transformation

The `Transformation` class represents a 6-element PDF transformation matrix `(a,b,c,d,e,f)`.

```python
from pypdf import Transformation

t = Transformation()                    # identity
t = Transformation().translate(100, 50) # translate
t = Transformation().scale(2.0)         # scale uniformly
t = Transformation().rotate(45)         # rotate 45° counter-clockwise
t = t.transform(other)                  # compose two transformations

page.add_transformation(t)              # apply to page content
page.add_transformation(t, expand=True) # also expand the media box
```

`Transformation.rotate(angle)` uses standard mathematical (CCW) convention, where
the rotation matrix is:

```
( cos(θ)   sin(θ) )
(-sin(θ)   cos(θ) )
```

The `page.rotate(angle)` method (which modifies the `/Rotate` entry) uses clockwise
convention. These are two independent rotation mechanisms.

---

### Other PageObject Methods

- `page.scale(sx, sy)` — Scale page content and all page boxes.
- `page.scale_by(factor)` — Uniform scaling.
- `page.scale_to(width, height)` — Scale to fit given dimensions.
- `page.compress_content_streams()` — Compress content with zlib.
- `page.extract_text()` — Extract text as a string.
- `page.images` — Access embedded images.
- `page.annotations` — Access page annotations (links, comments, etc.).
- `page.mediabox` / `page.cropbox` — RectangleObject for page boundaries.

---

## DocumentInformation (Metadata)

The `DocumentInformation` class provides typed access to the PDF info dictionary.

```python
writer = PdfWriter()
meta = writer.metadata  # returns DocumentInformation or None

# Read fields
title = meta.title       # str or None
author = meta.author
subject = meta.subject
creator = meta.creator
producer = meta.producer
keywords = meta.get("/Keywords")

# Write fields (using add_metadata)
writer.add_metadata({
    "/Title": "My Document",
    "/Author": "Alice",
    "/Subject": "Testing",
    "/Keywords": "pdf python test",
    "/Creator": "MyApp",
})
```

`add_metadata` accepts any string-keyed dictionary and stores each value as a PDF string
object. All provided keys are written to the `/Info` dictionary. After calling
`writer.write(buf)` and reopening with `PdfReader(buf)`, all metadata fields set with
`add_metadata` should be recoverable via `reader.metadata`.

**Roundtrip invariant**: Any metadata field written via `add_metadata` must be readable
after a write→read cycle: `reader.metadata.get(key) == original_value`.

---

## Common Usage Patterns

### Pattern 1: Merge two PDFs

```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
writer.append("first.pdf")
writer.append("second.pdf")
with open("merged.pdf", "wb") as f:
    writer.write(f)
```

### Pattern 2: Overlay watermark on each page

```python
writer = PdfWriter()
watermark = PdfReader("watermark.pdf")

for page in PdfReader("content.pdf").pages:
    writer.add_page(page)
    # Watermark goes UNDER content (content is on top)
    writer.pages[-1].merge_page(watermark.pages[0], over=False)

writer.write("watermarked.pdf")
```

### Pattern 3: Rotate pages

```python
writer = PdfWriter()
writer.append("input.pdf")
# Rotate all pages 90° clockwise
for page in writer.pages:
    page.rotate(90)
# Accumulate: rotate 180° then 90° = 270°
page = writer.pages[0]
page.rotate(180)
page.rotate(90)
assert page.rotation == 270
```

### Pattern 4: Programmatic page with resources

```python
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject

writer = PdfWriter()
page = writer.add_blank_page(612, 792)

# Add a font resource
font = DictionaryObject()
font[NameObject("/Type")] = NameObject("/Font")
font[NameObject("/Subtype")] = NameObject("/Type1")
font[NameObject("/BaseFont")] = NameObject("/Helvetica")
page.get_object()  # ensure page is in writer

# Set content stream
stream = StreamObject()
stream.set_data(b"BT /F1 12 Tf 72 720 Td (Hello World) Tj ET")
page[NameObject("/Contents")] = writer._add_object(stream)
```

### Pattern 5: Verify resource consistency after merge

When merging pages with shared resource names, the merged page's content stream
must reference only names present in the merged resource dictionary:

```python
page1.merge_page(page2)
resources = page1["/Resources"].get_object()
fonts = resources.get("/Font", {}).get_object()
content = page1.get_contents().get_data()

# All font references in content must be defined in resources
import re
for ref in re.findall(rb"/([\w-]+)\s+\d", content):
    # Check references against merged resource keys
    pass
```

---

## Resource Dictionary Structure

PDF pages reference fonts, images, and other resources via a `/Resources` dictionary:

```
/Resources <<
  /Font <<
    /F1 <indirect reference to Font object>
    /F1-0 <indirect reference to another Font object>
  >>
  /XObject << ... >>
  /ExtGState << ... >>
>>
```

When merging two pages:
- If page1 has `/Font /F1` and page2 also has `/Font /F1` (different font objects),
  page2's font is stored as `/F1-0` in the merged resource dict.
- All `/F1` references in page2's content stream are renamed to `/F1-0`.
- This ensures each font reference in the merged stream resolves to the correct font.
- This rename process applies to all resource types: fonts, XObjects, ExtGState, etc.
