# NetworkX 3.4.2 — Cycle Algorithms

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/cycles.html
> Version: NetworkX 3.4.2

## Overview

NetworkX provides several functions for finding and analyzing cycles in graphs.

---

## API Reference

### `girth(G)`

Returns the girth of the graph.

The **girth** of a graph is the length of its shortest cycle. If the graph is acyclic (has no cycles), returns `math.inf`.

**Parameters:**
- `G` : NetworkX Graph (undirected, non-multigraph)

**Returns:**
- `int or math.inf` — The length of the shortest cycle, or infinity if acyclic.

**Raises:**
- `NetworkXNotImplemented` — If G is directed or a multigraph.

**Examples:**
```python
>>> nx.girth(nx.chvatal_graph())
4
>>> nx.girth(nx.tutte_graph())
4
>>> nx.girth(nx.petersen_graph())
5
>>> nx.girth(nx.heawood_graph())
6
>>> nx.girth(nx.pappus_graph())
6
>>> nx.girth(nx.path_graph(5))
inf
```

**Notes:**
- The algorithm runs in time O(mn) on a graph with m edges and n nodes.
- The girth equals the length (number of edges/nodes) of the shortest cycle.
- A cycle of length k consists of k nodes and k edges.

---

### `cycle_basis(G, root=None)`

Returns a list of cycles which form a basis for cycles of G.

---

### `simple_cycles(G, length_bound=None)`

Find simple cycles of a graph.

---

### `minimum_cycle_basis(G, weight=None)`

Returns a minimum weight cycle basis for G.

---

## Mathematical Properties of Girth

**Definition**: The girth g(G) is the minimum length of any cycle in G.

**Known girth values for common graphs:**

| Graph | Girth |
|-------|-------|
| Complete graph K_3 | 3 |
| Complete graph K_n (n ≥ 3) | 3 |
| Cycle graph C_n | n |
| Complete bipartite K_{3,3} | 4 |
| Petersen graph | 5 |
| Heawood graph | 6 |
| Path graph P_n | ∞ (acyclic) |
| Tree | ∞ (acyclic) |

**Key property for cycle graphs**: `girth(cycle_graph(n)) == n`

The cycle graph C_n has exactly one cycle (the whole graph) of length n, so the girth equals n.

**Key property for complete graphs**: For K_n with n ≥ 3, every triple of nodes forms a triangle (3-cycle), so girth(K_n) == 3.

**Testing strategy for girth:**
```python
import networkx as nx

# Cycle graph: girth must equal n
for n in range(3, 15):
    G = nx.cycle_graph(n)
    assert nx.girth(G) == n, f"C_{n}: girth should be {n}"

# Complete graph K_n (n>=3): girth must equal 3 (triangle)
for n in range(3, 10):
    G = nx.complete_graph(n)
    assert nx.girth(G) == 3, f"K_{n}: girth should be 3"
```
