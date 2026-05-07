# BINT-001 Ground-Truth Strategy Specification

## Bug 1: `succ_item()` wrong candidate for left-left-leaf keys

### Bug Location
`bintrees/abctree.py` — `CPYTHON_ABCTree.succ_item()`, line 706

### Bug Description
```python
# Correct:
if (succ_node is None) or (node.key < succ_node.key):
    succ_node = node

# Buggy:
if (succ_node is None) or (node.key > succ_node.key):
    succ_node = node
```

The algorithm traverses the BST looking for `key`. When we go LEFT at a node
(because `key < node.key`), that node is a potential successor. The correct
code tracks the MINIMUM such candidate (smallest key > query = true successor).
The bug tracks the MAXIMUM candidate instead.

### Trigger Condition
The bug triggers when:
1. The tree has height >= 3 (n >= 5 for AVL)
2. The query key is reached via >= 2 consecutive left turns (key is in the
   "left-left" region of the root)
3. The target node has no right child (so the final answer comes only from
   the traversal candidates, not the right subtree minimum)

The minimum key always satisfies conditions 2 and 3: it is always a
left-left-...-left leaf with no right child. Querying `succ_item(min_key())`
therefore triggers the bug with ~96% probability when n in [5, 30].

### Wrong Behavior Example
Tree: [1, 2, 3, 4, 5, 6, 7, 8, 9] (AVL root = 4)
- succ_item(1): traversal goes 4→2→1 (two left turns)
- Candidates: {4, 2} (going left at both 4 and 2)
- Correct: keep min → succ_node = 2 → returns (2, 2)
- Buggy: keep max → succ_node = 4 → returns (4, 4) WRONG

### Strategy Requirements
- `keys: min_size=5` to ensure AVL height >= 3
- Test ALL consecutive pairs: `for i in range(len(sorted_keys)-1): assert succ_item(sorted_keys[i]) == sorted_keys[i+1]`
- Querying only `succ(min_key)` achieves ~96% trigger rate
- Testing all consecutive pairs catches more cases

### Trigger Probability
- Default random strategy (random keys, random query): ~30%
- Targeted (always query succ of min_key, n>=5): ~96%
- Testing all pairs: ~100% for n >= 5

---

## Bug 2: `prev_item()` wrong candidate for right-right-leaf keys

### Bug Location
`bintrees/abctree.py` — `CPYTHON_ABCTree.prev_item()`, line 744

### Bug Description
```python
# Correct:
if (prev_node is None) or (node.key > prev_node.key):
    prev_node = node

# Buggy:
if (prev_node is None) or (node.key < prev_node.key):
    prev_node = node
```

Symmetric to Bug 1. When going RIGHT (key > node.key), visited nodes are
predecessor candidates. Correct code keeps the MAXIMUM (true predecessor).
Bug keeps the MINIMUM instead.

### Trigger Condition
Symmetric: query `prev_item(max_key())` on tree with n >= 5.
The max key is always a right-right-...-right leaf with no left child.

### Strategy Requirements
Identical to Bug 1 but for prev_item:
- Test all consecutive pairs: `assert prev_item(sorted_keys[i+1]) == sorted_keys[i]`

---

## Bug 3: `iter_items()` excludes start_key

### Bug Location
`bintrees/abctree.py` — `CPYTHON_ABCTree._get_in_range_func()`, line 860

### Bug Description
```python
# Correct: start inclusive, end exclusive
return lambda x: start_key <= x < end_key

# Buggy: both exclusive
return lambda x: start_key < x < end_key
```

### Trigger Condition
Call `iter_items(k, k+N)` where k IS in the tree. The start key is silently
skipped. When start key is NOT in the tree, `<` and `<=` are equivalent.

### Strategy Requirements
- Use `start_key = sorted_keys[i]` (a key that EXISTS in tree)
- Check: `start_key in [k for k,v in t.iter_items(start_key, end_key)]`
- OR: compare full range against expected `[k for k in sorted_keys if start_key <= k < end_key]`

### Trigger Probability
- 100% whenever start_key is in the tree

---

## Bug 4: `floor_item()` returns wrong candidate for non-member queries

### Bug Location
`bintrees/abctree.py` — `CPYTHON_ABCTree.floor_item()`, line 777

### Bug Description
```python
# Correct: keep maximum candidate
if (prev_node is None) or (node.key > prev_node.key):
    prev_node = node

# Buggy: keep minimum candidate
if (prev_node is None) or (node.key < prev_node.key):
    prev_node = node
```

When the query key is NOT in the tree, the algorithm traverses right whenever
`key > node.key` (marking each such node as a floor candidate). The correct
code keeps the MAXIMUM candidate. The bug keeps the MINIMUM.

When the query key IS in the tree, the early return `if key == node.key: return`
fires before any candidates are accumulated, so the bug has no effect.

### Trigger Condition
- Query key is NOT in the tree
- Multiple keys in tree are less than the query (search visits >= 2 right turns)
- Example: tree=[1,3,5,7,9], floor(6): first right-turn at 1, then at 3, then at 5
  → candidates {1,3,5}; correct returns max=5, buggy returns min=1

### Strategy Requirements
- `query` should NOT be in keys: use `assume(query not in keys)` or query floats
- Tree should have `min_key < query <= max_key` so a floor exists
- Multiple keys below query (at least 2) are needed to observe wrong behavior

### Trigger Probability
- With random integer query in [0, 200] and random keys in [1, 199], min_size=5:
  ~70-80% of queries trigger the bug (query is in range and multiple keys < query)
