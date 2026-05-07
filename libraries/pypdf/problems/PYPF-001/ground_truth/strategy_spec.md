# Strategy Spec for PYPF-001

## Bug 1 (L4): _merge_page_writer over=False compositing order

**Trigger condition**: Call `page.merge_page(page2, over=False)` where `page` is
attached to a `PdfWriter` instance. The `over=False` parameter is non-default.

**Why default strategy is insufficient**: The default Hypothesis strategy would
test `merge_page(page2)` without specifying `over=False`, which goes through the
correct `new_content_array.append(page2content)` branch (over=True). The bug only
triggers when `over=False` is explicitly passed.

**Trigger probability with default strategy**: ~0% (parameter not included by default)

**Trigger probability with targeted strategy**: ~100% (any call with over=False and
non-empty content pages)

**Minimum trigger example**:
```python
writer = PdfWriter()
r1 = PdfReader(io.BytesIO(pdf1_bytes))
writer.append(r1)
page1 = writer.pages[0]
page2 = PdfReader(io.BytesIO(pdf2_bytes)).pages[0]
page1.merge_page(page2, over=False)
merged = page1.get_contents().get_data()
assert merged.index(marker2) < merged.index(marker1)
```

---

## Bug 2 (L3): rotate() modulo 270 instead of 360

**Trigger condition**: The cumulative rotation reaches exactly 270 degrees.
This happens with:
- `rotate(270)` from a page at 0 degrees
- `rotate(90)` applied three consecutive times from 0 degrees
- `rotate(180)` then `rotate(90)` from 0 degrees

**Why default strategy is insufficient**: Hypothesis default integer strategies
would generate many values, but `angle=270` from `initial_rotation=0` is just one
of many cases. The default `st.integers()` for angles typically focuses on small
values and wouldn't target exactly 270. Most test strategies would only try
`rotate(90)` once or twice, which gives 90 or 180 — both correct with the bug.

**Trigger probability with default strategy**: ~1/9 (only angle=270 or accumulated 270 triggers, among the angles 90/180/270)

**Trigger probability with targeted strategy**: ~100% (use `st.sampled_from([90, 180, 270])` for angle)

**Key insight**: The bug is `% 270`, which means the result is wrong ONLY when
`(current + angle)` is exactly divisible by 270 but not by 360. The only such
value in range [0, 540] is 270 itself.

**Minimum trigger example**:
```python
page = writer.add_blank_page(200, 200)
page.rotate(270)
assert page.rotation == 270  # Bug: returns 0
```

---

## Bug 3 (L3): _merge_resources rename map identity (no-op)

**Trigger condition**: Merge two pages where both pages have a resource dictionary
entry (font, XObject, etc.) with the **same name** but **different values**.

**Why default strategy is insufficient**: A default PBT that tests page merging
would typically use two pages from the same PDF or from PDFs that don't share
resource names. Only PDFs constructed to have overlapping resource names (e.g.,
both with `/F1` font) will trigger the bug.

**Trigger probability with default strategy**: ~0% (extremely unlikely that two
randomly chosen PDFs share resource names unless they're from the same document)

**Trigger probability with targeted strategy**: ~100% (explicitly create both pages
with a font named `/F1`)

**Key insight**: The bug affects the rename map: instead of mapping the original
name to the unique new name (`{"/F1": "/F1-0"}`), it maps the name to itself
(`{"/F1": "/F1"}`). The content stream is then "renamed" from "/F1" to "/F1"
(no change), while the resource dict stores page2's font under "/F1-0".

**Minimum trigger example**:
```python
# Both PDFs have a font resource named "/F1" but pointing to different font objects
pdf1 = make_pdf_with_font(b"BT /F1 12 Tf (PAGE1) Tj ET", font_name="/F1")
pdf2 = make_pdf_with_font(b"BT /F1 14 Tf (PAGE2) Tj ET", font_name="/F1")
# After merging: content should have /F1-0 for page2's font reference
assert b"/F1-0 " in merged_content_bytes
```

---

## Bug 4 (L2): rotation setter % 180 instead of % 360

**Trigger condition**: Directly assign `page.rotation = 180` or `page.rotation = 270`.

**Why default strategy is insufficient**: Many PBT approaches use `page.rotate(angle)`
(the method) instead of `page.rotation = angle` (the setter). The setter and the
rotate() method are independent code paths. The setter is used internally in
`transfer_rotation_to_content()` which calls `self.rotation = 0` — but 0 % 180 = 0
which is still correct! The bug only manifests for values 180 and 270.

**Trigger probability with default strategy**: ~25% (only 180 and 270 trigger, out of
{0, 90, 180, 270} valid values; but many strategies skip the setter entirely)

**Trigger probability with targeted strategy**: ~100% (use `st.sampled_from([0, 90, 180, 270])`)

**Key insight**: `(((180 + 45) // 90) * 90) % 360 = 180` (correct)
but `(((180 + 45) // 90) * 90) % 180 = 0` (bug: 180 % 180 = 0)
Similarly, 270 % 180 = 90 (bug), vs 270 % 360 = 270 (correct).

**Minimum trigger example**:
```python
page = writer.add_blank_page(200, 200)
page.rotation = 180
assert page.rotation == 180  # Bug: returns 0
```
