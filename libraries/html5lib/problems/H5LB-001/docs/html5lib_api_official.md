# html5lib 1.1 API Reference

html5lib is a pure-Python HTML5 parser and serializer implementing the WHATWG HTML5 specification (~14,000 lines). It produces a well-formed parse tree from any HTML5 input, including malformed or non-standard markup. This document describes the public API available to users.

---

## 1. Parsing HTML

### `html5lib.parse(doc, treebuilder="etree", namespaceHTMLElements=True, **kwargs)`

Parse an HTML document and return a tree.

**Parameters**:
- `doc` (str or file-like): The HTML content to parse.
- `treebuilder` (str): The tree representation to use. Options: `"etree"` (default), `"dom"`, `"lxml"`, `"soup"`.
- `namespaceHTMLElements` (bool): Whether to namespace HTML elements. Default is `True`. Set to `False` for element tags without namespace prefixes.

**Returns**: A tree root object (type depends on `treebuilder`).

**Example**:
```python
import html5lib
doc = html5lib.parse("<p>Hello <b>world</b>")
# Returns an ElementTree root with html/head/body structure
```

### `html5lib.parseFragment(doc, container="div", treebuilder="etree", namespaceHTMLElements=True, **kwargs)`

Parse an HTML fragment (not a full document).

**Parameters**:
- `doc` (str or file-like): The HTML fragment.
- `container` (str): The element to use as the fragment container. Default `"div"`.
- `treebuilder` (str): Same as `parse()`.
- `namespaceHTMLElements` (bool): Same as `parse()`.

**Returns**: A fragment root element.

**Example**:
```python
fragment = html5lib.parseFragment("<p>text <em>emphasized</em></p>")
```

---

## 2. Serialization

### `html5lib.serialize(input, tree="etree", encoding=None, **serializer_opts)`

Serialize a tree to HTML.

**Parameters**:
- `input`: The tree root to serialize.
- `tree` (str): The tree walker to use. Default `"etree"`.
- `encoding` (str or None): Output encoding. `None` returns a string.
- `**serializer_opts`: Additional options passed to `HTMLSerializer`.

**Returns**: str (if `encoding=None`) or bytes.

### `html5lib.serializer.HTMLSerializer`

The low-level serializer class. Create with serialization options, then call `.serialize(walker)`.

```python
from html5lib.serializer import HTMLSerializer

s = HTMLSerializer(
    omit_optional_tags=False,
    minimize_boolean_attributes=True,
    use_trailing_solidus=False,
    space_before_attributes=False,
    strip_whitespace=False,
    alphabetical_attributes=False,
    quote_attr_values="legacy",
    sanitize=False,
)
walker = html5lib.getTreeWalker("etree")
output = "".join(s.serialize(walker(doc)))
```

#### Serializer Options

**`omit_optional_tags`** (bool, default `False`):
When `True`, optional end tags (as defined by HTML5 spec) are omitted from output. For example:
- `</p>` before `</div>`, `</body>`, or before `<address>`, `<article>`, `<aside>`, `<blockquote>`, `<datagrid>`, `<dialog>`, `<dir>`, `<div>`, `<dl>`, `<fieldset>`, `<footer>`, `<form>`, `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>`, `<header>`, `<hr>`, `<menu>`, `<nav>`, `<ol>`, `<p>`, `<pre>`, `<section>`, `<table>`, `<ul>`
- `</li>` when followed by another `<li>`
- `</dt>`, `</dd>` in definition lists
- `</thead>`, `</tbody>`, `</tfoot>`, `</tr>`, `</th>`, `</td>` in tables

**`minimize_boolean_attributes`** (bool, default `True`):
When `True`, boolean attributes are serialized without `=""`. HTML5 defines two categories of boolean attributes:

1. **Global boolean attributes** (apply to all elements): `contenteditable`, `contextmenu`, `draggable`, `hidden`, `spellcheck`

2. **Element-specific boolean attributes**:
   - `<input>`: `disabled`, `checked`, `readonly`, `required`, `multiple`, `autofocus`, `ismap`
   - `<button>`, `<select>`, `<textarea>`, `<command>`, `<fieldset>`: `disabled`, `autofocus`
   - `<option>`: `disabled`, `selected`
   - `<optgroup>`: `disabled`
   - `<object>`: `typemustmatch`, `usemap`
   - `<img>`: `ismap`
   - `<audio>`, `<video>`, `<track>`: `autoplay`, `loop`, `controls`, `muted`, `default`
   - `<script>`: `async`, `defer`
   - `<details>`: `open`
   - `<dialog>`: `open`
   - `<ol>`: `reversed`

With `minimize_boolean_attributes=True`:
```python
# Input: <input disabled="" required="">
# Output: <input disabled required>
```

**`strip_whitespace`** (bool, default `False`):
When `True`, applies the whitespace filter which:
- Collapses runs of whitespace characters in `Characters` tokens to a single space
- Collapses `SpaceCharacters` tokens to a single space character `" "` (U+0020)
- Removes whitespace in contexts where it is not significant (e.g., between block elements)
- Preserves whitespace inside elements like `<pre>`, `<textarea>`, `<script>`, `<style>`, `<code>`

Example:
```python
doc = html5lib.parse("<p>hello   world</p>")
walker = html5lib.getTreeWalker("etree")
s = HTMLSerializer(strip_whitespace=True)
result = "".join(s.serialize(walker(doc)))
# Collapses "hello   world" → "hello world"
```

**`quote_attr_values`** (str, default `"legacy"`):
Controls attribute value quoting:
- `"legacy"`: Quote only when necessary (original html5lib behavior)
- `"always"`: Always quote attribute values
- `"spec"`: Quote according to the spec

**`use_trailing_solidus`** (bool, default `False`):
When `True`, void elements use XHTML-style closing slash: `<br />`.

**`alphabetical_attributes`** (bool, default `False`):
When `True`, attributes are output in alphabetical order.

---

## 3. Tree Walkers

Tree walkers convert a parsed tree into a stream of tokens for the serializer.

```python
walker_cls = html5lib.getTreeWalker("etree")
walker = walker_cls(doc)
```

Available walkers: `"etree"`, `"dom"`, `"lxml"`, `"soup"`.

### Walker Token Stream

The walker yields tokens as dicts with a `"type"` key:

| Type | Keys | Description |
|---|---|---|
| `"Doctype"` | `name`, `publicId`, `systemId` | DOCTYPE declaration |
| `"StartTag"` | `name`, `namespace`, `attributes` | Opening tag |
| `"EndTag"` | `name`, `namespace` | Closing tag |
| `"EmptyTag"` | `name`, `namespace`, `attributes` | Void element |
| `"Comment"` | `data` | HTML comment |
| `"Characters"` | `data` | Text content |
| `"SpaceCharacters"` | `data` | Whitespace-only text |

---

## 4. Filters

Filters are applied to the walker token stream before serialization. They are composable.

### Optional Tags Filter

```python
from html5lib.filters.optionaltags import Filter as OptionalTagsFilter
```

Removes optional start/end tags per HTML5 spec. Used internally by `HTMLSerializer` when `omit_optional_tags=True`.

**Optional end tags per HTML5 spec**:
- `</p>` is optional when followed by: `<address>`, `<article>`, `<aside>`, `<blockquote>`, `<datagrid>`, `<dialog>`, `<dir>`, `<div>`, `<dl>`, `<fieldset>`, `<footer>`, `<form>`, `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>`, `<header>`, `<hr>`, `<menu>`, `<nav>`, `<ol>`, `<p>`, `<pre>`, `<section>`, `<table>`, `<ul>`, and when the parent element is being closed (e.g., `</body>` closes `</p>`).

### Whitespace Filter

```python
from html5lib.filters.whitespace import Filter as WhitespaceFilter
```

Collapses whitespace in non-preserved contexts. Used when `strip_whitespace=True`.

**Preserved contexts** (whitespace is NOT collapsed): `<pre>`, `<textarea>`, `<script>`, `<style>`, `<code>`, `<listing>`, `<plaintext>`, `<xmp>`

**Collapsed behavior**:
- `Characters` tokens: `re.sub(r'[ \t\n\r\x0c]+', ' ', data)` — collapse any whitespace run to single space
- `SpaceCharacters` tokens: replaced with `" "` (single space character)

### Sanitize Filter

```python
from html5lib.filters.sanitizer import Filter as SanitizerFilter
```

Removes potentially dangerous markup (scripts, event handlers, etc.).

### Alphabetical Attributes Filter

```python
from html5lib.filters.alphabeticalattributes import Filter as AlphabeticalAttributesFilter
```

Sorts attributes alphabetically for deterministic output.

---

## 5. Tree Builders

Tree builders determine the output tree representation.

```python
tb = html5lib.getTreeBuilder("etree")
parser = html5lib.HTMLParser(tree=tb)
```

### etree (default)

Returns `xml.etree.ElementTree` compatible trees.

```python
import xml.etree.ElementTree as ET
doc = html5lib.parse("<p>text", treebuilder="etree", namespaceHTMLElements=False)
body = doc.find(".//body")
print(ET.tostring(body, encoding="unicode"))
```

### dom

Returns a `xml.dom.minidom` compatible tree.

---

## 6. The HTMLParser Class

```python
parser = html5lib.HTMLParser(
    tree=None,           # Tree builder class; defaults to etree
    strict=False,        # If True, raise ParseError on any parse error
    namespaceHTMLElements=True,
    debug=False
)
result = parser.parse(doc)           # Parse a full document
result = parser.parseFragment(doc)   # Parse a fragment
errors = parser.errors               # List of parse errors encountered
```

---

## 7. HTML5 Parser Behavior

html5lib faithfully implements the WHATWG HTML5 parsing algorithm. Key behaviors:

### Adoption Agency Algorithm (AAA)

The adoption agency algorithm handles mismatched/overlapping formatting tags. When an end tag is encountered for a formatting element (like `<b>`, `<i>`, `<em>`, `<strong>`, etc.) that has block-level elements inside it, the algorithm:

1. Finds the matching formatting element in the open elements stack
2. Finds the "furthest block" — the topmost block element below the formatting element
3. Moves the formatting element's content appropriately, placing a clone of the formatting element inside the block
4. Repeats up to 8 times to handle deep nesting

This means the AAA can run multiple outer iterations for HTML like:
```html
<b>text<div>block1<div>block2<p>para</b>
```
Each nesting level of unclosed block elements inside a formatting element requires one outer AAA iteration.

### Implied End Tags

Many end tags can be omitted and are implied by the parser:
- `</p>` is implied when a block-level element starts inside `<p>`
- `</li>` is implied when another `<li>` starts
- `</td>`, `</tr>`, etc. are implied in table contexts

### Active Formatting Elements (Noah's Ark Clause)

The parser maintains a list of active formatting elements. When the same formatting element appears more than 3 times consecutively, the earliest copy is discarded (Noah's Ark clause) to prevent infinite recursion in deeply nested structures.

---

## 8. Error Handling

html5lib does not raise exceptions for malformed HTML by default. Instead:
- Parse errors are recorded in `parser.errors`
- The parser always produces a valid tree
- Strict mode (`strict=True`) raises `html5lib.html5parser.ParseError`

---

## 9. Encoding Detection

```python
# From bytes with encoding detection
doc = html5lib.parse(b"<html><head><meta charset='utf-8'>...</html>")

# Explicit encoding
doc = html5lib.parse(b"...", override_encoding="latin-1")
```

---

## 10. Complete Example: Parse, Filter, Serialize

```python
import html5lib
from html5lib.serializer import HTMLSerializer

# Parse
doc = html5lib.parse("""
    <html>
    <body>
        <p class="intro">Hello   world</p>
        <input type="text" disabled="" required="">
        <h6>Section</h6>
    </body>
    </html>
""", treebuilder="etree", namespaceHTMLElements=False)

# Serialize with options
walker = html5lib.getTreeWalker("etree")
s = HTMLSerializer(
    omit_optional_tags=True,          # Omit optional tags like </p>
    minimize_boolean_attributes=True, # <input disabled required>
    strip_whitespace=True,            # Collapse whitespace
)
output = "".join(s.serialize(walker(doc)))
print(output)
# Produces compact, spec-compliant HTML with minimized boolean attrs
# and collapsed whitespace
```

---

## 11. Version and Compatibility

html5lib 1.1 requires Python 2.7 or 3.x (tested on 3.6+). It has no C extensions — the implementation is pure Python throughout, including the tokenizer, parser, and serializer.

The library implements the WHATWG HTML5 parsing specification as of 2017. For the full specification, see: https://html.spec.whatwg.org/
