# bintrees API Documentation

bintrees is a pure-Python balanced binary search tree library providing three
tree types: `AVLTree` (AVL self-balancing), `RBTree` (Red-Black tree), and
`BinaryTree` (unbalanced). All share a common dict-like interface.

## Installation

```python
pip install bintrees
from bintrees import AVLTree, RBTree, BinaryTree
```

## Construction

```python
t = AVLTree()                              # empty tree
t = AVLTree({3: 'c', 1: 'a', 2: 'b'})    # from dict
t = AVLTree([(1, 'a'), (2, 'b')])          # from key-value pairs
```

## Basic Dict Interface

```python
t[key] = value          # insert or update
t[key]                  # lookup (raises KeyError if absent)
del t[key]              # delete
key in t                # membership test
len(t)                  # number of items
```

## Iteration

```python
t.keys()                # ascending key iterator
t.keys(reverse=True)    # descending key iterator
t.values()              # value iterator (ascending by key)
t.items()               # (key, value) iterator (ascending by key)
list(t.keys())          # always sorted in ascending order
```

## Min/Max

```python
t.min_item()            # (key, value) pair with minimum key; raises ValueError if empty
t.max_item()            # (key, value) pair with maximum key; raises ValueError if empty
t.min_key()             # minimum key; raises ValueError if empty
t.max_key()             # maximum key; raises ValueError if empty
```

## Successor and Predecessor

```python
t.succ_item(key)
```
Returns `(k, v)` where `k` is the **smallest key strictly greater than** `key`.
Raises `KeyError` if `key` is the maximum key in the tree, or if `key` is not
in the tree.

```python
t.prev_item(key)
```
Returns `(k, v)` where `k` is the **largest key strictly less than** `key`.
Raises `KeyError` if `key` is the minimum key in the tree, or if `key` is not
in the tree.

```python
t.succ_key(key)     # same as succ_item(key)[0]
t.prev_key(key)     # same as prev_item(key)[0]
```

## Floor and Ceiling

```python
t.floor_item(key)
```
Returns `(k, v)` where `k` is the **greatest key less than or equal to** `key`.
Raises `KeyError` if there is no such key (i.e., `key` is less than all keys).

```python
t.ceiling_item(key)
```
Returns `(k, v)` where `k` is the **smallest key greater than or equal to** `key`.
Raises `KeyError` if there is no such key (i.e., `key` is greater than all keys).

```python
t.floor_key(key)      # same as floor_item(key)[0]
t.ceiling_key(key)    # same as ceiling_item(key)[0]
```

## Range Iteration

```python
t.iter_items(start_key=None, end_key=None, reverse=False)
```
Iterates over `(key, value)` pairs where **`start_key <= key < end_key`**
(inclusive start, exclusive end).
- If `start_key` is `None`, iteration starts from the minimum key.
- If `end_key` is `None`, iteration continues to the maximum key (inclusive).
- `reverse=True` yields items in descending order.

```python
# Equivalent slicing methods:
t.key_slice(start, end)    # keys where start <= key < end
t.value_slice(start, end)  # values where start <= key < end
t.item_slice(start, end)   # (key, value) pairs where start <= key < end
t[start:end]               # TreeSlice object with keys in start <= key < end
```

## Heap-Style Operations

```python
t.pop_min()    # remove and return (key, value) with minimum key
t.pop_max()    # remove and return (key, value) with maximum key
t.nsmallest(n) # list of n smallest (key, value) pairs
t.nlargest(n)  # list of n largest (key, value) pairs
```

## Set Operations

```python
t.intersection(other)         # keys in both trees
t.union(other)                # keys in either tree
t.difference(other)           # keys in t but not other
t.symmetric_difference(other) # keys in exactly one tree
t.is_subset(other)            # all keys of t are in other
t.is_superset(other)          # all keys of other are in t
t.is_disjoint(other)          # no keys in common
```

## BST Invariant

All tree types maintain the **BST ordering invariant**: for any node with key K,
all keys in the left subtree are strictly less than K, and all keys in the right
subtree are strictly greater than K. This means `list(t.keys())` is always sorted
in ascending order.

For `AVLTree` specifically, the **AVL balance invariant** additionally holds:
for every node, the heights of its left and right subtrees differ by at most 1.
This guarantees O(log n) time for all operations.

## Key Types

Keys must support comparison operators (`<`, `>`, `==`). Integer and string keys
are fully supported. Mixing key types is not supported.

## Example

```python
from bintrees import AVLTree

t = AVLTree()
for k in [5, 3, 8, 1, 4, 7, 9, 2, 6]:
    t[k] = k * 10

print(list(t.keys()))         # [1, 2, 3, 4, 5, 6, 7, 8, 9]
print(t.succ_item(3))         # (4, 40)  — smallest key > 3
print(t.prev_item(7))         # (6, 60)  — largest key < 7
print(t.floor_item(6.5))      # (6, 60)  — largest key <= 6.5
print(t.ceiling_item(6.5))    # (7, 70)  — smallest key >= 6.5
print(list(t.iter_items(3, 7)))  # [(3,30),(4,40),(5,50),(6,60)]  3<=k<7
```
