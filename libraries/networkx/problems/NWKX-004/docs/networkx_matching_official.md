# NetworkX 3.4.2 — Matching Algorithms

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/matching.html
> Version: NetworkX 3.4.2

## Overview

A **matching** in a graph is a set of edges in which no two edges share a common endpoint. Matchings are fundamental in combinatorial optimization.

---

## API Reference

### `is_matching(G, matching)`

Return True if `matching` is a valid matching of G.

A matching in a graph is a set of edges in which no two distinct edges share a common endpoint. Each node is incident to at most one edge in the matching. The edges are said to be independent.

**Parameters:**
- `G` : NetworkX graph
- `matching` : dict or set. A dictionary or set representing a matching. If a dictionary, it must have `matching[u] == v` and `matching[v] == u` for each edge (u, v). If a set, elements must be of the form `(u, v)`.

**Returns:** `bool`

---

### `is_maximal_matching(G, matching)`

Return True if `matching` is a maximal matching of G.

A **maximal matching** is a matching where no additional edge can be added without violating the matching property. (Note: maximal != maximum.)

**Returns:** `bool`

**Example:**
```python
>>> G = nx.Graph([(1, 2), (1, 3), (2, 3), (3, 4), (3, 5)])
>>> nx.is_maximal_matching(G, {(1, 2), (3, 4)})
True
```

---

### `is_perfect_matching(G, matching)`

Return True if `matching` is a perfect matching for G.

A **perfect matching** in a graph is a matching in which **exactly one edge is incident upon each vertex**. That is, every vertex of G is matched.

**Parameters:**
- `G` : NetworkX graph
- `matching` : dict or set representing the matching.

**Returns:** `bool` — Whether the given set or dictionary represents a valid perfect matching in the graph.

**Example:**
```python
>>> G = nx.Graph([(1, 2), (1, 3), (2, 3), (2, 4), (3, 5), (4, 5), (4, 6)])
>>> my_match = {1: 2, 3: 5, 4: 6}
>>> nx.is_perfect_matching(G, my_match)
True
```

**Key requirement**: A perfect matching exists only in graphs with an even number of nodes. For a perfect matching M on graph G with n nodes, |M| must equal n/2.

---

### `max_weight_matching(G, maxcardinality=False, weight='weight')`

Returns a maximum weighted matching of G.

---

### `min_weight_matching(G, weight='weight')`

Returns a minimum weight maximal matching of G.

---

### `maximal_matching(G)`

Find a maximal matching in the graph using a greedy algorithm.

---

## Mathematical Properties of Perfect Matchings

**Definition**: A perfect matching is a set M of edges such that every vertex of G is an endpoint of exactly one edge in M.

**Necessary condition**: |V(G)| must be even.

**Sufficient + known cases**:
- Complete graph K_n (n even): always has a perfect matching. Simple construction: pair nodes as (0,1), (2,3), ..., (n-2, n-1).
- Cycle graph C_n (n even): the alternating edges form a perfect matching.
- Complete bipartite graph K_{n,n}: always has a perfect matching.

**Key property for testing**: For any even complete graph K_{2k}, the matching {(0,1), (2,3), ..., (2k-2, 2k-1)} is always a perfect matching. `is_perfect_matching(K_{2k}, matching)` must return True.

```python
import networkx as nx

# K4 perfect matching
G = nx.complete_graph(4)
matching = {(0, 1), (2, 3)}
assert nx.is_perfect_matching(G, matching) == True

# K6 perfect matching
G = nx.complete_graph(6)
matching = {(0, 1), (2, 3), (4, 5)}
assert nx.is_perfect_matching(G, matching) == True
```
