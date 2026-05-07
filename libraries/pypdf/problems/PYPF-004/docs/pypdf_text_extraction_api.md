# pypdf Text Extraction API

This document describes the text extraction subsystem of pypdf 6.9.0, covering the
public API, character encoding pipeline, affine matrix composition, and font metrics.
It provides enough detail to write property-based tests for text extraction behavior
without reading the library source code.

---

## 1. Public API: Extracting Text from a PDF

```python
import pypdf

reader = pypdf.PdfReader("file.pdf")
for page in reader.pages:
    text = page.extract_text()          # default: all orientations
    text = page.extract_text(orientations=(0,))  # only 0-degree text
```

`extract_text(orientations=(0, 90, 180, 270))` returns a string containing the text
content of the page. The order is approximately top-to-bottom for normal PDFs.

---

## 2. ToUnicode CMap: Character Mapping

PDF fonts may include a `/ToUnicode` stream that maps glyph codes to Unicode characters.
pypdf parses this stream to decode text during extraction.

### CMap Format

A ToUnicode CMap is a PostScript-like stream with two sections:

**bfrange** (character ranges):
```
beginbfrange
<start_hex> <end_hex> <unicode_base_hex>
<start_hex> <end_hex> [ <unicode_1> <unicode_2> ... ]
endbfrange
```

- Non-list form: each code from `start` to `end` inclusive maps to consecutive
  Unicode values beginning at `unicode_base`. The range is **inclusive on both ends**:
  a range `<0041> <0043> <0041>` maps codes 0x41, 0x42, 0x43 to 'A', 'B', 'C'.
- List form: each code from `start` maps to the corresponding Unicode in the bracket list.

**bfchar** (individual character mappings):
```
beginbfchar
<glyph_hex> <unicode_hex>
endbfchar
```

- Maps a single glyph code to a Unicode codepoint.
- `glyph_hex` is typically 2 hex digits (1 byte) for simple fonts.
- `unicode_hex` is 2 hex digits (1 byte) for characters in the Latin-1 range, or
  **4 hex digits (2 bytes)** for characters in the Basic Multilingual Plane (U+0100+).
  4-digit hex targets are decoded as UTF-16-BE.

### Internal Representation

After parsing, `_parse_to_unicode(ft)` returns a tuple:
- `map_dict`: dict mapping glyph character (str) → Unicode string. Also has
  key `-1` whose value is the byte width (1 for single-byte fonts).
- `int_entry`: list of glyph code integers that have entries in the map.

```python
from pypdf._cmap import _parse_to_unicode
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

cmap_bytes = b"beginbfchar\n<41> <0041>\nendbfchar"
stream_obj = DecodedStreamObject()
stream_obj._data = cmap_bytes

ft = DictionaryObject()
ft[NameObject("/ToUnicode")] = stream_obj

map_dict, int_entry = _parse_to_unicode(ft)
# map_dict: {'A': 'A', -1: 1}
# int_entry: [65]
```

### Direct Access to Parsers

You can call the low-level parsers directly:

```python
from pypdf._cmap import parse_bfrange, parse_bfchar

# parse_bfrange: parse one line from a bfrange section
map_dict = {-1: 1}  # -1 holds the byte width
int_entry = []
result = parse_bfrange(line_bytes, map_dict, int_entry, None)
# result is None if the range is closed, or (a, b) tuple if multiline

# parse_bfchar: parse one line from a bfchar section
parse_bfchar(line_bytes, map_dict, int_entry)
```

---

## 3. Font Object and Character Widths

```python
from pypdf._font import Font, FontDescriptor

font = Font(
    name="Helvetica",
    encoding="charmap",         # or dict[int, str]
    character_map={},           # from _parse_to_unicode
    sub_type="Type1",
    font_descriptor=FontDescriptor(),
    character_widths={"A": 722, " ": 278, "default": 500},
    space_width=278,
)
```

### Key Font Attributes

- `font.encoding`: Either a Python codec string (e.g. `"charmap"`, `"utf-16-be"`) or
  a `dict[int, str]` mapping byte values to characters.
- `font.character_map`: Maps glyph characters to Unicode strings (from ToUnicode CMap).
  Used by `get_display_str` for the final character lookup.
- `font.character_widths`: Maps character strings to PDF glyph width units (1/1000 of a text unit).
  Always has a `"default"` key for unknown characters.
- `font.space_width`: Width of the space character. Used for detecting inter-word gaps.

### text_width()

```python
width = font.text_width("Hello")
# Returns sum of character_widths for each char, falling back to character_widths["default"]
```

### Default Width Calculation

`Font._add_default_width(current_widths, flags)` computes `current_widths["default"]`:
- If `current_widths` is empty → default = 500.
- If space width is known and font is **non-fixed-pitch** → default = **2 × space_width**.
- If space width is known and font is **fixed-pitch** → default = space_width (monospace).
- Otherwise → average of existing positive widths.

`FontFlags.FIXED_PITCH = 1` (bit 0). A typical proportional font uses `flags = 32`.

### Building a Font from a PDF Dictionary

```python
from pypdf._font import Font
from pypdf.generic import DictionaryObject, NameObject, ArrayObject, NumberObject

pdf_font_dict = DictionaryObject({
    NameObject("/Subtype"): NameObject("/Type1"),
    NameObject("/BaseFont"): NameObject("/Helvetica"),
    NameObject("/FirstChar"): NumberObject(32),
    NameObject("/Widths"): ArrayObject([NumberObject(278)] * 100),
    NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
})
font = Font.from_font_resource(pdf_font_dict)
```

---

## 4. Affine Matrix Composition

Text position in PDF is tracked with two 2D affine matrices:
- **cm_matrix**: current transformation matrix (graphics state)
- **tm_matrix**: text matrix (updated by text operators)

Each matrix is a 6-element list `[a, b, c, d, e, f]` representing:
```
| a  b  0 |
| c  d  0 |
| e  f  1 |
```
where `(e, f)` is the translation (position) component.

### mult(m, n)

```python
from pypdf._text_extraction import mult

result = mult(m, n)
# Computes the matrix product m × n (PDF convention: column vectors, left-to-right)
# result[0] = m[0]*n[0] + m[1]*n[2]
# result[1] = m[0]*n[1] + m[1]*n[3]
# result[2] = m[2]*n[0] + m[3]*n[2]
# result[3] = m[2]*n[1] + m[3]*n[3]
# result[4] = m[4]*n[0] + m[5]*n[2] + n[4]   (x-translation)
# result[5] = m[4]*n[1] + m[5]*n[3] + n[5]   (y-translation)
```

The translation components `(result[4], result[5])` reflect the full affine composition.
Note: `result[4]` uses `n[4]` (x-translation of n) and `result[5]` uses `n[5]`
(y-translation of n). These are **different indices**.

### orient(m)

```python
from pypdf._text_extraction import orient

direction = orient(m)
# Returns one of: 0, 90, 180, 270
# 0   → normal text (m[3] > 0)
# 180 → upside down (m[3] < 0)
# 90  → rotated 90° (m[1] > 0)
# 270 → rotated 270°
```

### Positioning and Newline Detection

`crlf_space_check` compares the current position to the previous position using `mult`:
```
m_prev = mult(tm_prev, cm_prev)
m      = mult(tm_matrix, cm_matrix)
delta_y = m[5] - m_prev[5]
```
If `|delta_y|` exceeds 80% of the font height, a newline is inserted.
If `delta_x` exceeds the space width threshold, a space is inserted.

---

## 5. Text Operators (Content Stream)

During `extract_text`, the content stream is scanned for PDF operators:

| Operator | Description | Effect on text state |
|---|---|---|
| `BT` | Begin Text | Resets tm_matrix to identity |
| `ET` | End Text | Flushes accumulated text |
| `Tf name size` | Set font | Sets current font and font_size |
| `Td tx ty` | Move text pos | tm_matrix[4] += tx*tm[0]+ty*tm[2]; tm_matrix[5] += tx*tm[1]+ty*tm[3] |
| `Tm a b c d e f` | Set text matrix | Replaces tm_matrix with [a,b,c,d,e,f] |
| `T*` | Next line | Moves by -TL units using tm_matrix |
| `TL leading` | Set leading | TL = leading × font_size × scale_x |
| `Tj string` | Show text | Decodes and adds text using current font |
| `cm a b c d e f` | Transform matrix | cm_matrix = mult([a,b,c,d,e,f], cm_matrix) |
| `q` | Save state | Pushes cm_matrix and font state |
| `Q` | Restore state | Pops from the graphics state stack |

---

## 6. CMap Parsing Pipeline

The full text extraction flow:

```
PDF content stream
  → Tj operator with raw glyph bytes
  → get_text_operands(): decode bytes using font.encoding
  → get_display_str(): remap chars using font.character_map
  → accumulated in TextExtraction.text
  → output string
```

The `font.character_map` is built from `_parse_to_unicode()`:
1. `prepare_cm(ft)` → pre-processes the ToUnicode stream bytes
2. `process_cm_line()` → dispatches to `parse_bfrange` or `parse_bfchar`
3. `parse_bfrange(line, map_dict, int_entry, multiline_rg)` → handles range entries
4. `parse_bfchar(line, map_dict, int_entry)` → handles individual char entries

---

## 7. Testing Patterns

### Testing CMap Parsing Directly

```python
from pypdf._cmap import _parse_to_unicode
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

def make_cmap_ft(cmap_bytes: bytes) -> DictionaryObject:
    stream_obj = DecodedStreamObject()
    stream_obj._data = cmap_bytes
    ft = DictionaryObject()
    ft[NameObject("/ToUnicode")] = stream_obj
    return ft

cmap = b"beginbfrange\n<20> <25> <0041>\nendbfrange"
map_dict, int_entry = _parse_to_unicode(make_cmap_ft(cmap))
assert 0x25 in int_entry  # range is inclusive
assert chr(0x20) in map_dict
```

### Testing Font Default Width

```python
from pypdf._font import Font

widths = {" ": 300}
Font._add_default_width(widths, flags=32)  # non-fixed-pitch
assert widths["default"] == 600  # 2 × space_width
```

### Testing Matrix Multiplication

```python
from pypdf._text_extraction import mult

m = [1.0, 0.0, 0.0, 1.0, 5.0, 10.0]
n = [1.0, 0.0, 0.0, 1.0, 20.0, 30.0]
result = mult(m, n)
assert result[4] == 25.0   # x-translation: 5*1 + 10*0 + 20
assert result[5] == 40.0   # y-translation: 5*0 + 10*1 + 30
```
