# NetworkX 3.4.2 — DAG Longest Path Algorithms

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/dag.html
> Version: NetworkX 3.4.2

## Overview

NetworkX provides algorithms for finding the longest path in a directed acyclic graph (DAG). These functions use dynamic programming via topological ordering.

---

## API Reference

### `dag_longest_path(G, weight='weight', default_weight=1, topo_order=None)`

Returns the longest path in a directed acyclic graph (DAG).

If G has edges with a `weight` attribute, those weights are used as edge weights (default_weight=1 for unweighted edges).

**Parameters:**
- `G` : NetworkX DiGraph — A directed acyclic graph (DAG)
- `weight` : str, optional — Edge data key to use for weight (default: 'weight')
- `default_weight` : int, optional — Weight for edges without a weight attribute (default: 1)
- `topo_order` : list or tuple, optional — A topological order for G (computed automatically if None)

**Returns:**
- `list` — Longest path as a list of nodes.

**Raises:**
- `NetworkXNotImplemented` — If G is not directed.

**Examples:**
```python
>>> DG = nx.DiGraph(
...     [(0, 1, {"cost": 1}), (1, 2, {"cost": 1}), (0, 2, {"cost": 42})]
... )
>>> nx.dag_longest_path(DG)
[0, 1, 2]
>>> nx.dag_longest_path(DG, weight="cost")
[0, 2]
```

**Notes:**
- For unweighted graphs, the longest path is the one with the most edges.
- The function returns a list of nodes from start to end of the longest path.
- If multiple paths share the maximum length, one is returned (implementation-defined).

---

### `dag_longest_path_length(G, weight='weight', default_weight=1)`

Returns the longest path length in a DAG.

**Returns:** `int` — Longest path length (sum of edge weights, or number of edges for unweighted).

**Examples:**
```python
>>> DG = nx.DiGraph(
...     [(0, 1, {"cost": 1}), (1, 2, {"cost": 1}), (0, 2, {"cost": 42})]
... )
>>> nx.dag_longest_path_length(DG)
2
>>> nx.dag_longest_path_length(DG, weight="cost")
42
```

---

## Mathematical Properties of Longest Paths in DAGs

**Definition**: The longest path in a DAG is a path from any source to any sink that maximizes the total edge weight (or number of edges for unweighted graphs).

**Known values for common DAGs:**

| Graph | Longest Path | Length |
|-------|--------------|--------|
| Linear chain 0→1→2→...→n | [0, 1, 2, ..., n] | n |
| Binary tree of depth d | root to any leaf | d |
| Complete DAG (all i<j edges) | [0, 1, 2, ..., n] | n |

**Key property for linear chains**: For a linear chain G with nodes 0, 1, ..., n connected as 0→1→2→...→n:
- `dag_longest_path_length(G) == n` (n edges)
- `dag_longest_path(G)` returns a path of n+1 nodes

**Key invariant**: The longest path length equals `len(dag_longest_path(G)) - 1` for unweighted graphs.

**Relationship**: `dag_longest_path_length(G)` computes the total weight along the path returned by `dag_longest_path(G)`.

```python
import networkx as nx

# Linear chain: longest path = full chain
n = 5
G = nx.DiGraph()
for i in range(n):
    G.add_edge(i, i+1)

assert nx.dag_longest_path_length(G) == n
assert len(nx.dag_longest_path(G)) == n + 1

# The length formula
path = nx.dag_longest_path(G)
length = nx.dag_longest_path_length(G)
assert length == len(path) - 1  # for unweighted graphs
```
