# NetworkX 3.4.2 — Eulerian Algorithms

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/euler.html
> Version: NetworkX 3.4.2

## Overview

The Eulerian algorithms module provides functionality for working with Eulerian circuits and paths in graphs.

Module: `networkx.algorithms.euler`

---

## Function Index

| Function | Description |
|----------|-------------|
| `is_eulerian(G)` | Returns True if and only if G has an Eulerian circuit |
| `eulerian_circuit(G[, source, keys])` | Returns an iterator over the edges of an Eulerian circuit in G |
| `eulerize(G)` | Transforms a graph into an Eulerian graph |
| `is_semieulerian(G)` | Returns True iff G is semi-Eulerian |
| `has_eulerian_path(G[, source])` | Returns True iff G has an Eulerian path |
| `eulerian_path(G[, source, keys])` | Returns an iterator over the edges of an Eulerian path in G |

---

## Detailed Function Documentation

### `is_eulerian(G)`

**Description:** "Returns True if and only if `G` has an Eulerian circuit. An Eulerian circuit is a closed walk that includes each edge of a graph exactly once."

The function applies to both directed and undirected graphs. However, graphs with isolated vertices are not considered Eulerian. For disconnected or weakly connected graphs, the function returns `False`.

**Parameters:**

- **G** (NetworkX graph): Directed or undirected graph

**Returns:** `bool` — True if and only if the graph is Eulerian; otherwise False

**Notes:**

- **Isolated Vertices:** "Graphs with isolated vertices (i.e. vertices with zero degree) are not considered to have Eulerian circuits."
- **Connectivity:** For undirected graphs, the graph must be connected. For directed graphs, the graph must be strongly connected.

**Examples:**

```python
# Directed graph
nx.is_eulerian(nx.DiGraph({0: [3], 1: [2], 2: [3], 3: [0, 1]}))
# Returns: True

# Complete graph (odd number of nodes)
nx.is_eulerian(nx.complete_graph(5))
# Returns: True

# Petersen graph
nx.is_eulerian(nx.petersen_graph())
# Returns: False

# Handling isolated vertices
G = nx.Graph([(0, 1), (1, 2), (0, 2)])
G.add_node(3)  # isolated vertex
nx.is_eulerian(G)  # Returns: False

G.remove_nodes_from(list(nx.isolates(G)))
nx.is_eulerian(G)  # Returns: True
```

---

### `eulerian_circuit(G, source=None, keys=False)`

**Description:** "Returns an iterator over the edges of an Eulerian circuit in G." An "Eulerian circuit is a closed walk that includes each edge of a graph exactly once."

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **G** | NetworkX graph | required | A graph, either directed or undirected |
| **source** | node, optional | None | Starting node for the circuit |
| **keys** | bool | False | If False, edges are `(u, v)` format. If True, edges are `(u, v, k)` format for multigraphs |

**Returns:**

- **edges** (iterator): An iterator over edges in the Eulerian circuit

**Raises:**

- **NetworkXError**: Raised if the graph is not Eulerian

**Notes:**

This implementation operates in "linear time" and is adapted from graph theory research on Euler tours and matching problems.

**Examples:**

```python
>>> G = nx.complete_graph(3)
>>> list(nx.eulerian_circuit(G))
[(0, 2), (2, 1), (1, 0)]

>>> list(nx.eulerian_circuit(G, source=1))
[(1, 2), (2, 0), (0, 1)]

# Extract vertex sequence
>>> [u for u, v in nx.eulerian_circuit(G)]
[0, 2, 1]
```

**See Also:** `is_eulerian()`

---

### `has_eulerian_path(G, source=None)`

**Description:** "Return True iff `G` has an Eulerian path." An Eulerian path traverses each edge in a graph exactly once. When `source` is provided, the function checks if a path starting from that specific node exists.

**Parameters:**

- **G** (NetworkX Graph): The graph to analyze for an Eulerian path
- **source** (node, optional, default=None): Starting node for the path

**Returns:**

- **bool**: True if the graph contains an Eulerian path; False otherwise

**Conditions for Directed Graphs:**

An Eulerian path exists in a directed graph when:

- "at most one vertex has out_degree - in_degree = 1"
- "at most one vertex has in_degree - out_degree = 1"
- "every other vertex has equal in_degree and out_degree"
- All vertices belong to a single connected component of the underlying undirected graph

When `source` is specified, no other node can have out_degree - in_degree = 1 (the source itself may have this property).

**Conditions for Undirected Graphs:**

An Eulerian path exists in an undirected graph when:

- "exactly zero or two vertices have odd degree"
- All vertices belong to a single connected component

When `source` is specified, either an Eulerian circuit exists, or `source` has odd degree with the above conditions met.

**Important Note:**

Graphs containing isolated vertices (degree zero nodes) are considered to lack an Eulerian path, causing the function to return False.

**Examples:**

```python
>>> G = nx.Graph([(0, 1), (1, 2), (0, 2)])
>>> G.add_node(3)
>>> nx.has_eulerian_path(G)
False

>>> G.remove_nodes_from(list(nx.isolates(G)))
>>> nx.has_eulerian_path(G)
True
```

**See Also:** `is_eulerian()`, `eulerian_path()`

---

### `eulerian_path(G, source=None, keys=False)`

**Description:** Returns an iterator over the edges of an Eulerian path in a given graph.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **G** | NetworkX Graph | required | The graph to search for an Eulerian path |
| **source** | node or None | None | Starting node for the search; `None` searches all potential starting nodes |
| **keys** | bool | False | When `True`, yields 3-tuples `(u, v, edge_key)`; when `False`, yields 2-tuples `(u, v)` |

**Yields:**

Edge tuples representing the Eulerian path sequence. Format depends on the `keys` parameter:
- 2-tuple format: `(u, v)` when keys=False
- 3-tuple format: `(u, v, edge_key)` when keys=True

**Warnings:**

"If `source` provided is not the start node of an Euler path will raise error even if an Euler Path exists."

**See Also:** `has_eulerian_path()`, `is_eulerian()`

---

### `eulerize(G)`

**Description:** "Transforms a graph into an Eulerian graph." Modifies a graph structure to ensure it becomes Eulerian by adding edges as needed.

**Parameters:**

- **G** (NetworkX graph): Input graph

---

### `is_semieulerian(G)`

**Description:** "Returns True iff G is semi-Eulerian." A graph is semi-Eulerian if it has an Eulerian path but not an Eulerian circuit.

**Parameters:**

- **G** (NetworkX graph): Directed or undirected graph

**Returns:** `bool`
