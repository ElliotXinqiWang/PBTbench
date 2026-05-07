# NetworkX 3.4.2 — Directed Acyclic Graphs (DAG) Algorithms

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/dag.html
> Version: NetworkX 3.4.2
> Built with: Sphinx 8.1.3 | PyData Sphinx Theme 0.15.4

## Overview

"Algorithms for directed acyclic graphs (DAGs)." The documentation emphasizes that "most of these functions are only guaranteed to work for DAGs" and notes that "these functions do not check for acyclic-ness, so it is up the user to check for that."

---

## Function Index

### Node Relationship Functions

| Function | Description |
|----------|-------------|
| `ancestors(G, source)` | "Returns all nodes having a path to `source` in `G`" |
| `descendants(G, source)` | "Returns all nodes reachable from `source` in `G`" |

### Topological Sorting Functions

| Function | Description |
|----------|-------------|
| `topological_sort(G)` | "Returns a generator of nodes in topologically sorted order" |
| `topological_generations(G)` | "Stratifies a DAG into generations" |
| `all_topological_sorts(G)` | "Returns a generator of all topological sorts of the directed graph G" |
| `lexicographical_topological_sort(G[, key])` | "Generate the nodes in the unique lexicographical topological sort order" |

### DAG Validation and Properties

| Function | Description |
|----------|-------------|
| `is_directed_acyclic_graph(G)` | "Returns True if the graph `G` is a directed acyclic graph (DAG) or False if not" |
| `is_aperiodic(G)` | "Returns True if `G` is aperiodic" |

### Closure and Reduction Functions

| Function | Description |
|----------|-------------|
| `transitive_closure(G[, reflexive])` | "Returns transitive closure of a graph" |
| `transitive_closure_dag(G[, topo_order])` | "Returns the transitive closure of a directed acyclic graph" |
| `transitive_reduction(G)` | "Returns transitive reduction of a directed graph" |

### Path and Structure Analysis Functions

| Function | Description |
|----------|-------------|
| `antichains(G[, topo_order])` | "Generates antichains from a directed acyclic graph (DAG)" |
| `dag_longest_path(G[, weight, ...])` | "Returns the longest path in a directed acyclic graph (DAG)" |
| `dag_longest_path_length(G[, weight, ...])` | "Returns the longest path length in a DAG" |
| `dag_to_branching(G)` | "Returns a branching representing all (overlapping) paths from root nodes to leaf nodes in the given directed acyclic graph" |

### V-Structure and Collider Functions

| Function | Description |
|----------|-------------|
| `compute_v_structures(G)` | "Yields 3-node tuples that represent the v-structures in `G`" |
| `colliders(G)` | "Yields 3-node tuples that represent the colliders in `G`" |
| `v_structures(G)` | "Yields 3-node tuples that represent the v-structures in `G`" |

---

## Detailed Function Documentation

### `topological_generations(G)`

**Description:** "Stratifies a DAG into generations."

A topological generation represents a node collection where ancestors of nodes in each generation appear in previous generations, and descendants appear in following generations. Nodes are guaranteed placement in the earliest possible generation.

**Parameters:**

- **G** (NetworkX digraph): A directed acyclic graph (DAG)

**Yields:**

- **sets of nodes**: Returns an iterator yielding sets of nodes representing each generation

**Raises:**

- **NetworkXError**: Raised if the graph G is undirected, as "Generations are defined for directed graphs only"
- **NetworkXUnfeasible**: Raised if G is not a directed acyclic graph (DAG), indicating no topological generations exist; also raised if G is modified while the returned iterator is being processed
- **RuntimeError**: Raised if G is modified during iterator processing

**Notes:**

The generation assignment relates to max-path-distance from a node to its farthest leaf node, obtainable via `enumerate(topological_generations(G))`.

**See Also:** `topological_sort`

**Example:**

```python
>>> DG = nx.DiGraph([(2, 1), (3, 1)])
>>> [sorted(generation) for generation in nx.topological_generations(DG)]
[[2, 3], [1]]
```

---

### `topological_sort(G)`

**Description:** Produces a generator yielding nodes arranged in topologically sorted order. In such an arrangement, if a directed edge goes from node u to node v, then u will appear before v in the sequence.

**Parameters:**

- **G** (NetworkX digraph): A directed acyclic graph (DAG)

**Returns:** Generator of nodes yielding nodes in topologically sorted order

**Raises:**

- **NetworkXError**: Raised when the input graph is undirected
- **NetworkXUnfeasible**: Raised if the graph contains cycles or is modified during iteration
- **RuntimeError**: Raised if the graph is modified while the iterator is being processed

**Notes:**

The algorithm is based on "Introduction to Algorithms: A Creative Approach" by Manber, U. (1989).

The topological sort is a nonunique permutation — multiple valid orderings may exist for the same graph.

**Examples:**

```python
DG = nx.DiGraph([(1, 2), (2, 3)])

# Reverse topological order
list(reversed(list(nx.topological_sort(DG))))
# Returns: [3, 2, 1]

# Converting edge-based dependencies to node-based
list(nx.topological_sort(nx.line_graph(DG)))
# Returns: [(1, 2), (2, 3)]
```

**See Also:** `is_directed_acyclic_graph()`, `lexicographical_topological_sort()`

---

### `dag_longest_path(G, weight='weight', default_weight=1, topo_order=None)`

**Description:** "Returns the longest path in a directed acyclic graph (DAG)." If edges contain weight attributes, those values are used in the calculation.

**Parameters:**

| Parameter | Type | Default | Details |
|-----------|------|---------|---------|
| **G** | NetworkX DiGraph | required | A directed acyclic graph (DAG) |
| **weight** | str, optional | `'weight'` | Edge data key to use for weight |
| **default_weight** | int, optional | `1` | Weight assigned to edges without weight attribute |
| **topo_order** | list or tuple, optional | None | Pre-computed topological order for G |

**Returns:** `list` — The longest path as a sequence of nodes

**Raises:**

- **NetworkXNotImplemented**: Raised if G is not a directed graph

**Examples:**

```python
DG = nx.DiGraph([(0, 1, {"cost": 1}), (1, 2, {"cost": 1}),
                  (0, 2, {"cost": 42})])
nx.dag_longest_path(DG)           # Returns [0, 1, 2]
nx.dag_longest_path(DG, weight="cost")  # Returns [0, 2]

DG = nx.DiGraph([(0, 1), (0, 2)])
nx.dag_longest_path(DG, topo_order=[0, 1, 2])  # Returns [0, 1]
nx.dag_longest_path(DG, topo_order=[0, 2, 1])  # Returns [0, 2]
```

**See Also:** `dag_longest_path_length`

---

### `is_directed_acyclic_graph(G)`

**Description:** "Returns True if the graph `G` is a directed acyclic graph (DAG) or False if not"

---

### `ancestors(G, source)`

**Description:** "Returns all nodes having a path to `source` in `G`"

---

### `descendants(G, source)`

**Description:** "Returns all nodes reachable from `source` in `G`"

---

### `transitive_closure(G, reflexive=False)`

**Description:** "Returns transitive closure of a graph"

---

### `transitive_reduction(G)`

**Description:** "Returns transitive reduction of a directed graph"

---

### `antichains(G, topo_order=None)`

**Description:** "Generates antichains from a directed acyclic graph (DAG)"
