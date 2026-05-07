# pypdf 6.9.0 — PdfWriter, PdfReader and Page-Structure API

## Overview

pypdf is a pure-Python library for reading, writing, splitting, merging, and
transforming PDF files entirely in memory.  The two primary classes are
`PdfWriter` (for creating or modifying PDFs) and `PdfReader` (for parsing
existing ones).  All I/O is performed through Python file-like objects or
`io.BytesIO` buffers; no files on disk are needed.

```python
import io
from pypdf import PdfWriter, PdfReader
```

---

## PdfWriter

### Construction

```python
writer = PdfWriter()
```

Creates an empty PDF document.  The document contains no pages and no metadata
until objects are explicitly added.

### Adding pages

```python
page = writer.add_blank_page(width=595, height=842)   # A4 in points
page = writer.insert_page(src_page, index=0)           # insert at position
```

`add_blank_page(width, height)` appends a new empty page and returns a
`PageObject`.  `insert_page(page, index)` inserts a copy of an existing
`PageObject` at the given position (0-based).

### Writing to a stream

```python
buf = io.BytesIO()
writer.write(buf)          # writes the complete PDF; returns (bool, IO)
buf.seek(0)
```

`write(stream)` serialises the entire document — all pages, resources, the
cross-reference table, and the trailer — to the supplied stream in one call.
The stream must be open in binary mode.  The same call also accepts a `Path`
or file-path string.

### Page count and access

```python
n = len(writer.pages)          # number of pages (same as writer.get_num_pages())
page = writer.pages[i]         # zero-based indexed access
```

`writer.pages` is a list-like view; `writer.pages[i]` returns the `PageObject`
at position `i`.

---

## Adding and Appending Content

### _merge_content_stream_to_page

```python
writer._merge_content_stream_to_page(page, new_content_data: bytes)
```

Appends `new_content_data` (a raw PDF content-stream fragment in bytes) to the
given page's `/Contents` entry.

**Invariant**: PDF content streams are an ordered sequence of drawing
operators.  Operators are processed by the renderer **in the order they appear**
in the byte stream.  Later operators are drawn on top of earlier ones.
Repeated calls to `_merge_content_stream_to_page` must therefore preserve
**append order**: content added in call N must appear *after* content added in
call N-1 in the resulting byte stream.  A PBT property can verify this by
checking that the byte offset of each chunk in the merged stream is
monotonically increasing in call order.

The function handles two cases internally:

1. **No existing `/Contents`**: the new data becomes the sole stream.
2. **Existing `/Contents` is a `StreamObject`**: the existing data and the new
   data are concatenated (existing first, new second) into a fresh stream.
3. **Existing `/Contents` is an `ArrayObject`**: the new data is wrapped in a
   new `StreamObject` appended to the array.

---

## Metadata

### add_metadata

```python
writer.add_metadata({
    "/Title":   "My Document",
    "/Author":  "Alice",
    "/Subject": "Testing",
    "/Creator": "my-app",
})
```

Stores entries in the PDF's `/Info` dictionary.  Standard keys are prefixed
with `/`.  Values are stored as PDF text strings.

### Reading metadata after roundtrip

```python
buf = io.BytesIO()
writer.write(buf)
buf.seek(0)
reader = PdfReader(buf)
meta = reader.metadata
print(meta.title)    # same as writer added under /Title
print(meta.author)   # same as writer added under /Author
```

`DocumentInformation` properties (`title`, `author`, `subject`, `creator`,
`producer`, `creation_date`, `modification_date`, `keywords`) each return
`Optional[str]`.  The raw (un-decoded) bytes are available via `*_raw`
variants.

**Roundtrip invariant**: for any string value `v`, `add_metadata({"/Title": v})`
followed by write/read should produce `reader.metadata.title == v`.

---

## Page Labels

Page labels define how page numbers are displayed to the user (e.g., Roman
numerals for a preface, then Arabic from page 1 for the main body).  They are
stored in the PDF's `/PageLabels` number tree.

### set_page_label

```python
writer.set_page_label(
    page_index_from: int,  # first page of the labeled range (0-based)
    page_index_to:   int,  # last page of the labeled range (inclusive)
    style: Optional[str] = None,   # /D /R /r /A /a
    prefix: Optional[str] = None,  # label prefix string
    start: Optional[int] = 0,      # value of the first label in the range
)
```

Assigns a label format to the page range `[page_index_from, page_index_to]`.
Ranges are non-overlapping; calling `set_page_label` on a range that
overlaps an existing one replaces the overlapping portion.

**Style codes**:

| Code | Meaning                             |
|------|-------------------------------------|
| `/D` | Decimal Arabic numerals (1, 2, 3…)  |
| `/R` | Uppercase Roman numerals (I, II, …) |
| `/r` | Lowercase Roman numerals (i, ii, …) |
| `/A` | Uppercase letters (A, B, … Z, AA, …)|
| `/a` | Lowercase letters (a, b, … z, aa, …)|

The `start` parameter sets the numeric value for the first page in the range.
Default is 1.  For example, `start=5` makes the first page of the range show
label "5" (for `/D` style).

**Update invariant**: calling `set_page_label` a second time with the same
`page_index_from` **updates** the label format for that range.  After the
second call, `index2label(reader, page_index_from)` must return a label
consistent with the *new* style and start value, not the old one.

### index2label

```python
from pypdf._page_labels import index2label

label = index2label(reader, page_index)  # returns str, e.g. "iv" or "5"
```

Translates a zero-based page index to its display label string.  This function
traverses the `/PageLabels` number tree, finds the applicable label range, and
applies the range's style formula.

**Range-boundary invariant**: if page `k` is the *first page* of a label range
(i.e., `k` equals a start key in the Nums array), then `index2label(reader, k)`
must return the label computed by **that range's** formula — not the formula of
the preceding range.  For example, if the decimal range starts at page index 4,
then `index2label(reader, 4)` should return `"1"` (or the specified `start`
value), not the Roman numeral that would be computed by the preceding range.

### Direct use of get_label_from_nums

```python
from pypdf._page_labels import get_label_from_nums
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject

nums = ArrayObject([
    NumberObject(0), DictionaryObject({NameObject("/S"): NameObject("/r")}),
    NumberObject(4), DictionaryObject({NameObject("/S"): NameObject("/D"),
                                       NameObject("/St"): NumberObject(1)}),
])
root = DictionaryObject({NameObject("/Nums"): nums})
label = get_label_from_nums(root, 4)   # should return "1"
label = get_label_from_nums(root, 5)   # should return "2"
```

`get_label_from_nums` takes a dict containing a `/Nums` array and a page index.
The Nums array is a flat key-value sequence: `[key0, label_dict0, key1,
label_dict1, …]` sorted by key in ascending order.  Each `label_dict` has
optional entries `/S` (style), `/P` (prefix), and `/St` (start value).

---

## Named Destinations

Named destinations allow hyperlinks and bookmarks to refer to pages by a
symbolic name rather than a page number.

### add_named_destination

```python
ref = writer.add_named_destination(title: str, page_number: int)
```

Creates a GoTo destination pointing to `page_number` (0-based) and stores it
in the PDF's name tree under the string `title`.

### The name-tree sort-order invariant

The PDF specification (ISO 32000-1 §7.9.6) requires that name tree leaf
arrays be **sorted in lexicographic order by key**.  This is mandatory because
PDF viewers perform binary search on name trees to resolve destinations.

**Sort invariant**: after adding N named destinations with distinct titles, the
array returned by `writer.get_named_dest_root()` must satisfy:

```python
names = [str(arr[i]) for i in range(0, len(arr), 2)]
assert names == sorted(names)
```

This invariant must hold regardless of the order in which destinations were
added to the writer.

### Reading named destinations after roundtrip

```python
buf = io.BytesIO()
writer.write(buf)
buf.seek(0)
reader = PdfReader(buf)
dests = reader.named_destinations   # dict[str, Destination]
for name, dest in dests.items():
    print(name, dest.page_number)
```

`reader.named_destinations` is an `Optional[dict[str, Destination]]` where
each value has a `.page_number` property.

**Roundtrip invariant**: `set(reader.named_destinations.keys())` must equal
the set of titles that were added via `add_named_destination`.

---

## PdfReader

### Construction

```python
reader = PdfReader(stream)          # stream: BytesIO or file-like
reader = PdfReader(stream, strict=False)
```

Parses a PDF document from `stream`.

### Page access

```python
n = len(reader.pages)
page = reader.pages[i]          # PageObject
```

### Metadata access

```python
meta = reader.metadata           # Optional[DocumentInformation]
if meta:
    print(meta.title, meta.author, meta.creator)
```

---

## Working with PageObject

A `PageObject` is a dictionary-like object (`DictionaryObject` subclass).  Key
entries include:

| Key           | Type             | Meaning                             |
|---------------|------------------|-------------------------------------|
| `/Type`       | NameObject       | Always `/Page`                      |
| `/MediaBox`   | ArrayObject      | `[llx, lly, urx, ury]` in user units|
| `/Contents`   | StreamObject or ArrayObject | Content stream(s)          |
| `/Resources`  | DictionaryObject | Fonts, XObjects, etc.               |
| `/Parent`     | IndirectObject   | Parent `/Pages` node                |

### Content streams

A PDF content stream is a sequence of operands and operators encoded as bytes.
Operators are applied in document order.  Example operators:

```
BT              % Begin text
/F1 12 Tf       % Set font
100 700 Td      % Move to (100, 700)
(Hello) Tj      % Show string
ET              % End text
```

When multiple streams are concatenated, they are processed left-to-right.
**Order matters**: an operator in stream 2 is processed after all operators in
stream 1.

---

## Typical PBT patterns for pypdf

### Pattern 1: write-read roundtrip
```python
writer = PdfWriter()
# ... add pages, content, metadata ...
buf = io.BytesIO()
writer.write(buf)
buf.seek(0)
reader = PdfReader(buf)
# assert properties of reader match what was written
```

### Pattern 2: page label roundtrip
```python
writer = PdfWriter()
for _ in range(10): writer.add_blank_page(200, 200)
writer.set_page_label(0, 3, style="/r")
writer.set_page_label(4, 9, style="/D", start=1)
buf = io.BytesIO(); writer.write(buf); buf.seek(0)
reader = PdfReader(buf)
assert index2label(reader, 0) == "i"
assert index2label(reader, 4) == "1"
```

### Pattern 3: named destination ordering
```python
writer = PdfWriter()
for _ in range(5): writer.add_blank_page(200, 200)
for i, t in enumerate(["delta", "alpha", "gamma"]):
    writer.add_named_destination(t, i)
arr = writer.get_named_dest_root()
names = [str(arr[i]) for i in range(0, len(arr), 2)]
assert names == sorted(names)   # ["alpha", "delta", "gamma"]
```

### Pattern 4: content append order
```python
writer = PdfWriter()
page = writer.add_blank_page(200, 200)
writer._merge_content_stream_to_page(page, b"FIRST_OP")
writer._merge_content_stream_to_page(page, b"SECOND_OP")
data = page["/Contents"].get_object().get_data()
assert data.find(b"FIRST_OP") < data.find(b"SECOND_OP")
```

### Pattern 5: multi-step label update
```python
writer = PdfWriter()
for _ in range(6): writer.add_blank_page(200, 200)
writer.set_page_label(0, 5, style="/r")
writer.set_page_label(0, 5, style="/D", start=10)   # update same range
buf = io.BytesIO(); writer.write(buf); buf.seek(0)
reader = PdfReader(buf)
# After update, page 0 should carry decimal label "10", not Roman "i"
assert index2label(reader, 0) == "10"
```

---

## Key invariants for PBT authors

1. **Page label update**: after `set_page_label(k, ...)` is called twice with
   the same `k`, `index2label(reader, k)` reflects the **second** call's style
   and start value.

2. **Page label boundary**: `index2label(reader, k)` where `k` is a range-start
   key returns a label from **that range**, not the preceding range.

3. **Content stream order**: a series of `_merge_content_stream_to_page` calls
   must produce a stream where each call's payload appears in **ascending byte
   offset** order matching the call order.

4. **Named destination sort**: `writer.get_named_dest_root()` stores titles in
   **ascending lexicographic order** after any sequence of `add_named_destination`
   calls.

5. **Metadata roundtrip**: `writer.add_metadata({"/Title": v})` followed by
   write/read yields `reader.metadata.title == v`.

6. **Page count invariant**: `len(reader.pages) == len(writer.pages)` after a
   write/read roundtrip on a document that has not been modified between the
   two operations.
