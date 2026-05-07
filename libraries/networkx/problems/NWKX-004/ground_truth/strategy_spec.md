# Strategy Specification for NWKX-004

## Bug 1: `vf2pp_is_isomorphic` — T2_in/T2 confusion in backtracking (L4)

**Location**: `networkx/algorithms/isomorphism/vf2pp.py:1046`
**Change**: `T2_in.add(popped_node2)` → `T2.add(popped_node2)`

### Trigger condition
The bug fires during backtracking in the VF2++ search when:
1. A node `popped_node2` is removed from the mapping
2. At least one successor of `popped_node2` in G2 is still in `reverse_mapping`

This requires a directed graph where the algorithm's backtracking causes a node to be un-mapped while its forward neighbor remains mapped. This happens in graphs with non-layered structure where multiple search paths exist and the first one fails.

### Strategy reasoning
- **Min nodes**: 8 (small graphs rarely require deep enough backtracking)
- **Trigger rate**: ~10-15% per random 8-15 node digraph with ~1.5n edges
- **Why default Hypothesis fails**: Hypothesis's small example preference generates graphs that are too sparse or too small to require the specific backtracking pattern

### Minimal triggering example
A 14-node directed graph with edges forming multiple converging paths:
`[(0,10),(2,12),(2,5),(4,0),(4,10),(4,12),(5,6),(6,0),(6,8),(7,11),(7,10),(8,13),(9,0),(9,10),(9,1),(10,2),(11,10),(12,6),(12,8),(13,3),(13,0)]`

---

## Bug 2: `girth()` — cycle length off-by-one (L3)

**Location**: `networkx/algorithms/cycles.py:1225`
**Change**: `length = du + du + 2 - delta` → `length = du + du + 1 - delta`

### Trigger condition
Any graph with at least one cycle. The bug reduces the computed length of every non-tree edge's cycle contribution by 1.

### Strategy reasoning
- **Trigger rate**: 100% for any cyclic graph
- **Simplest case**: `cycle_graph(n)` for any n >= 3
- **Why easy to detect**: `girth(cycle_graph(n)) == n-1` instead of `n`

---

## Bug 3: `is_perfect_matching()` — always returns False (L2)

**Location**: `networkx/algorithms/matching.py:258`
**Change**: `len(nodes) == len(G)` → `len(nodes) == len(G) + 1`

### Trigger condition
Any valid perfect matching. `len(nodes)` can never exceed `len(G)` (can't match more nodes than exist), so `len(nodes) == len(G) + 1` is always False.

### Strategy reasoning
- **Trigger rate**: 100% for any even complete graph with its canonical perfect matching
- **Simplest case**: `K_2` with matching `{(0,1)}`
- **Default strategy**: `st.integers(1,8)` → `k` → `K_{2k}` with pairing `{(2i,2i+1)}`

---

## Bug 4: `dag_longest_path()` — max → min returns shortest (L3)

**Location**: `networkx/algorithms/dag.py:1044`
**Change**: `v = max(dist, ...)` → `v = min(dist, ...)`

### Trigger condition
Any DAG with at least one edge. `min(dist)` picks the node with minimum accumulated distance (typically 0, i.e., a source node), causing path reconstruction to return a trivial single-node path.

### Strategy reasoning
- **Trigger rate**: 100% for any linear chain with n >= 2
- **Simplest case**: linear chain 0→1→2→...→n, expected length n, buggy returns 0
- **Default strategy**: `st.integers(2,15)` → linear chain of that length
