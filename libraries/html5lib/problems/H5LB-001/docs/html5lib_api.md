# html5lib 1.1 API Reference

html5lib is a Python library that parses HTML according to the WHATWG HTML5 specification.
Its parser is designed to handle malformed HTML the same way modern browsers do, with well-defined
error-recovery behavior described in the specification.

## Core Parse Functions

### `html5lib.parse(doc, treebuilder="etree", namespaceHTMLElements=True, **kwargs)`

Parses a complete HTML document and returns a tree.

```python
import html5lib

# Parse a string
tree = html5lib.parse('<html><body><p>Hello!</p></body></html>')

# Parse bytes
with open('page.html', 'rb') as f:
    tree = html5lib.parse(f)

# Use the etree treebuilder (returns xml.etree.ElementTree.Element)
tree = html5lib.parse('<p>Hi</p>', treebuilder='etree')
```

The `treebuilder` parameter selects the tree representation:
- `"etree"` (default) — `xml.etree.ElementTree`
- `"dom"` — `xml.dom.minidom.Document`
- `"lxml"` — `lxml.etree` (requires lxml)

### `html5lib.parseFragment(doc, container="div", treebuilder="etree", namespaceHTMLElements=True, **kwargs)`

Parses an HTML fragment (not a full document) and returns a tree rooted at a container element.

```python
# Parse a fragment; tree root is a <div> containing the parsed nodes
frag = html5lib.parseFragment('<p>Hello</p><p>World</p>')

# Serialize fragments back to HTML
from html5lib import serialize
html = serialize(frag, tree='etree')
```

### `html5lib.HTMLParser`

The `HTMLParser` class gives direct control over parsing:

```python
parser = html5lib.HTMLParser(tree=html5lib.getTreeBuilder('etree'))
tree = parser.parse('<p>content</p>')
errors = parser.errors  # list of parse errors encountered
```

## TreeBuilders

```python
builder = html5lib.getTreeBuilder('etree')
parser = html5lib.HTMLParser(tree=builder)
```

Supported builders: `'etree'`, `'dom'`, `'lxml'`, `'etree_lxml'`.

The `etree` builder returns `xml.etree.ElementTree.Element` objects. All elements use
Clark-notation namespaces, e.g., `{http://www.w3.org/1999/xhtml}p`.

## Serialization

### `html5lib.serialize(input, tree="etree", encoding=None, **serializer_opts)`

Serializes a parsed tree back to an HTML string.

```python
tree = html5lib.parse('<p>Hello <b>world</b></p>')
html = html5lib.serialize(tree)
# '<html><head></head><body><p>Hello <b>world</b></p></body></html>'
```

Parameters passed as `**serializer_opts` are forwarded to `HTMLSerializer`.

### `html5lib.serializer.HTMLSerializer`

`HTMLSerializer` controls output formatting. Key options (all can be passed to `serialize()`
as keyword arguments):

| Option | Default | Description |
|--------|---------|-------------|
| `minimize_boolean_attributes` | `True` | Shorten boolean attributes: `checked=""` → `checked` |
| `omit_optional_tags` | `True` | Omit start/end tags that are optional per HTML5 spec |
| `quote_attr_values` | `"legacy"` | When to quote attribute values: `"always"`, `"spec"`, or `"legacy"` |
| `quote_char` | `'"'` | Quote character for attributes |
| `strip_whitespace` | `False` | Normalize whitespace (collapse runs of spaces to one) |
| `inject_meta_charset` | `True` | Inject `<meta charset>` in head |
| `use_trailing_solidus` | `False` | Add `/` before `>` in void elements: `<br/>` |
| `escape_lt_in_attrs` | `False` | Escape `<` in attribute values |
| `sanitize` | `False` | Strip unsafe/unknown elements and attributes |
| `alphabetical_attributes` | `False` | Output attributes in alphabetical order |

**Boolean attribute minimization example:**

```python
import html5lib

frag = html5lib.parseFragment('<input type="checkbox" checked="checked" disabled="">')

# minimize_boolean_attributes=True (default)
s1 = html5lib.serialize(frag, tree='etree', minimize_boolean_attributes=True)
# expected: '<input checked disabled type="checkbox">'

# minimize_boolean_attributes=False
s2 = html5lib.serialize(frag, tree='etree', minimize_boolean_attributes=False)
# '<input checked="" disabled="" type="checkbox">'
```

**Optional tag omission example:**

```python
frag = html5lib.parseFragment('<p>hello</p><p>world</p>')
s1 = html5lib.serialize(frag, tree='etree', omit_optional_tags=True)
# '<p>hello<p>world'   (</p> is optional before another <p>)

s2 = html5lib.serialize(frag, tree='etree', omit_optional_tags=False)
# '<p>hello</p><p>world</p>'
```

Elements that implicitly close a `<p>` (making the `</p>` optional) include:
`address`, `article`, `aside`, `blockquote`, `datagrid`, `dialog`, `dir`, `div`, `dl`,
`fieldset`, `footer`, `form`, `h1`, `h2`, `h3`, `h4`, `h5`, `h6`, `header`, `hr`, `menu`,
`nav`, `ol`, `p`, `pre`, `section`, `table`, `ul`.

## Filters

Filters transform the token stream between parsing and serialization. They are applied as
wrappers around the tree walker.

```python
import html5lib
from html5lib.filters import whitespace, optionaltags, sanitizer

tree = html5lib.parse(html_input)
walker = html5lib.getTreeWalker('etree')
stream = walker(tree)

# Apply filters
stream = whitespace.Filter(stream)
stream = optionaltags.Filter(stream)

# Serialize the filtered stream
from html5lib.serializer import HTMLSerializer
result = HTMLSerializer().render(stream)
```

### `html5lib.filters.whitespace.Filter`

Collapses whitespace in the token stream except inside `<pre>`, `<textarea>`, and
RCDATA elements (`<script>`, `<style>`, etc.).

Behavior:
- **SpaceCharacters tokens** (whitespace-only text nodes between elements): normalized to
  a single space `' '`.
- **Characters tokens** (mixed-content text): runs of whitespace collapsed to a single space.

```python
html = '<p>a</p>   <p>b</p>'
# The three spaces between </p> and <p> are a SpaceCharacters token.
# After whitespace filter: becomes ' ' (single space)
```

This filter is activated automatically when `strip_whitespace=True` is passed to `serialize()`.

### `html5lib.filters.optionaltags.Filter`

Removes optional start and end tags from the token stream according to HTML5 optional-tag rules.

This filter is activated automatically when `omit_optional_tags=True` is passed to `serialize()`
(which is the default).

For `<p>` elements specifically: the end tag `</p>` is optional (and removed by this filter)
when the next element is one of the block-level elements listed above (h1 through h6, div, etc.).

### `html5lib.filters.sanitizer.Filter`

Strips unsafe HTML constructs (script elements, event handler attributes, etc.). Activated when
`sanitize=True` is passed to `serialize()`.

### `html5lib.filters.alphabeticalattributes.Filter`

Reorders attributes alphabetically. Activated when `alphabetical_attributes=True`.

## Pipeline: Using Multiple Filters

```python
import html5lib
from html5lib.filters import whitespace, optionaltags
from html5lib.serializer import HTMLSerializer

tree = html5lib.parseFragment('<p>hello   world</p>  <p>foo</p>')
walker = html5lib.getTreeWalker('etree')
stream = walker(tree)
stream = whitespace.Filter(stream)
stream = optionaltags.Filter(stream)
result = HTMLSerializer(
    omit_optional_tags=False,   # already applied manually above
    strip_whitespace=False       # already applied manually above
).render(stream)
```

## The HTML5 Parsing Algorithm

### Error Recovery

html5lib implements the full WHATWG error-recovery algorithm. Malformed HTML is repaired
in a well-defined way:

```python
# Unclosed tags are automatically closed
tree = html5lib.parseFragment('<p>unclosed paragraph')
result = html5lib.serialize(tree, tree='etree', omit_optional_tags=False)
# '<p>unclosed paragraph</p>'

# Overlapping tags are repaired
tree = html5lib.parseFragment('<b><i>text</b></i>')
result = html5lib.serialize(tree, tree='etree', omit_optional_tags=False)
# '<b><i>text</i></b>'
```

### Tree Construction Phases

The parser proceeds through insertion modes (initial, before html, in head, in body, etc.)
with specific rules for each. The "in body" mode handles most content.

### Adoption Agency Algorithm (AAA)

The adoption agency algorithm is triggered when a formatting end tag (e.g., `</b>`, `</i>`,
`</em>`, `</strong>`, `</a>`) is encountered but the current nesting context is mismatched.
It repairs the tree by reparenting nodes.

The algorithm iterates over the current formatting context and handles up to a bounded number
of nesting levels. The WHATWG spec limits the outer loop to prevent infinite processing on
pathological inputs. The inner loop (per outer iteration) also has a limit of 3 steps.

Key formatting elements that can trigger the AAA: `a`, `b`, `big`, `code`, `em`, `font`,
`i`, `nobr`, `s`, `small`, `strike`, `strong`, `tt`, `u`.

For deeply nested structures like:
```html
<b>text<div>layer1<div>layer2<div>layer3<div>layer4<div>layer5</b>
```
The parser repairs this so that each nested block level contains a clone of the formatting
element, preserving the author's intended text styling through the block structure.

## Key Properties That Should Hold

1. **Parse→serialize roundtrip**: `parse(serialize(parse(html))) == parse(html)` —
   parsing and re-serializing should be idempotent after the first parse.

2. **Boolean attribute minimization**: When `minimize_boolean_attributes=True`, known
   boolean attributes (like `checked`, `disabled`, `required`, `readonly`) must appear
   without `=""`, i.e., as bare attribute names.

3. **Optional tag omission correctness**: When `omit_optional_tags=True`, the output should
   not include end tags that the HTML5 spec marks as optional in context. For `<p>`, the
   end tag is optional before any of the block elements listed above.

4. **Whitespace normalization**: When `strip_whitespace=True` (or the whitespace filter is
   applied), whitespace-only text sequences between block elements should be collapsed to
   exactly one space `' '`.

5. **Tree structure preservation**: Malformed HTML is parsed and repaired deterministically.
   The number and nesting of elements in the repaired tree should follow the spec rules for
   the adoption agency algorithm.

## TreeWalker

The tree walker converts a parsed tree to a flat token stream for serialization:

```python
walker = html5lib.getTreeWalker('etree')
stream = walker(tree)
for token in stream:
    print(token['type'], token.get('name', ''), token.get('data', ''))
```

Token types: `StartTag`, `EndTag`, `EmptyTag`, `Characters`, `SpaceCharacters`,
`Comment`, `Doctype`, `ParseError`.

## Complete Example: Parse, Filter, and Serialize

```python
import html5lib
from html5lib.serializer import HTMLSerializer

# Parse
html_input = '<!DOCTYPE html><html><body><p>  hello   world  </p></body></html>'
tree = html5lib.parse(html_input)

# Serialize with options
output = html5lib.serialize(
    tree,
    tree='etree',
    omit_optional_tags=True,
    minimize_boolean_attributes=True,
    strip_whitespace=True,
    inject_meta_charset=False
)
print(output)
# '<p>hello world</p>'
```
