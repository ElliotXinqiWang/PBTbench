# NetworkX Graph Algorithm Documentation

NetworkX is a Python library for the creation, manipulation, and study of the
structure, dynamics, and functions of complex networks.  The library provides
~70 000 lines of code implementing hundreds of graph algorithms covering directed
and undirected graphs, multigraphs, and various graph-theoretic measures.

This document covers four algorithms that are the focus of this problem:

1. `topological_generations` — stratify a DAG into generations
2. `clustering` — compute clustering coefficients
3. `diameter` — compute the diameter of a graph
4. `is_eulerian` — test whether a graph has an Eulerian circuit

---

## 1. `networkx.topological_generations(G)`

### Description

Stratifies a directed acyclic graph (DAG) into *generations*.

A **topological generation** is a set of nodes such that:
- All ancestors of a node in generation k are in some generation < k.
- All descendants of a node in generation k are in some generation > k.
- Nodes are placed in the **earliest possible** generation they can belong to.

Equivalently, generation 0 contains all nodes with no incoming edges
(in-degree 0), generation 1 contains all nodes whose only predecessors are in
generation 0, and so on.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `G` | `nx.DiGraph` | A directed acyclic graph. |

### Yields

Sets of nodes, one set per generation, in topological order.

### Raises

- `NetworkXError` — if `G` is not a directed graph.
- `NetworkXUnfeasible` — if `G` contains a cycle (is not a DAG) or is
  modified during iteration.
- `RuntimeError` — if `G` is modified during iteration.

### Mathematical Definition

Let `indeg(v)` be the in-degree of node v.  Define the generation of v as:

```
gen(v) = 0                            if indeg(v) == 0
gen(v) = 1 + max(gen(u) : u → v)     otherwise
```

Generation k = `{ v : gen(v) == k }`.

### Guaranteed Properties

1. **Coverage**: `union(gen_0, gen_1, ..., gen_k) == V(G)`.  Every node in the
   graph appears in exactly one generation.
2. **Ordering**: If there is an edge u → v, then `gen(u) < gen(v)`.
3. **Earliness**: Each node is placed in the earliest generation consistent
   with the ordering constraint.

### Example

```python
>>> import networkx as nx
>>> DG = nx.DiGraph([(2, 1), (3, 1)])
>>> [sorted(gen) for gen in nx.topological_generations(DG)]
[[2, 3], [1]]
```

```python
>>> DG = nx.DiGraph([(0, 1), (0, 2), (1, 3), (2, 3)])
>>> [sorted(gen) for gen in nx.topological_generations(DG)]
[[0], [1, 2], [3]]
```

---

## 2. `networkx.clustering(G, nodes=None, weight=None)`

### Description

Computes the **clustering coefficient** for one or more nodes.

For an **unweighted undirected** graph, the clustering coefficient of node u is:

```
c(u) = 2 * T(u) / (deg(u) * (deg(u) - 1))
```

where:
- `T(u)` is the number of triangles through u (a triangle is a set of three
  mutually adjacent nodes that includes u).
- `deg(u)` is the degree of u.
- If `deg(u) < 2`, then `c(u) = 0` (no triangles possible).

The clustering coefficient measures the fraction of u's neighbours that are
also connected to each other.  It ranges from 0 (no neighbours are connected)
to 1 (all neighbours form a clique).

For **directed** graphs the formula is different (see below).

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `G` | `nx.Graph` or `nx.DiGraph` | The graph. |
| `nodes` | node, iterable, or None | If a single node, return a float. If an iterable, return a dict for those nodes. If None (default), return a dict for all nodes. |
| `weight` | string or None | Edge attribute name for weights. If None, all edges have weight 1. |

### Returns

- `float` — if `nodes` is a single node in `G`.
- `dict` — mapping node → clustering coefficient, otherwise.

### Directed Graph Formula

```
c(u) = T(u) / (2 * (deg_tot(u) * (deg_tot(u) - 1) - 2 * deg_recip(u)))
```

where `deg_tot` is in-degree + out-degree and `deg_recip` is the number of
reciprocal pairs (edges in both directions).

### Guaranteed Properties

1. **Range**: `0.0 <= c(u) <= 1.0` for all nodes u.
2. **Complete subgraph**: For a complete graph K_n (every pair of nodes
   connected), `c(u) = 1.0` for all u, for any n >= 3.
3. **Triangle-free**: If the graph contains no triangles (e.g. bipartite
   graphs, trees, stars), then `c(u) = 0.0` for all u.
4. **Monotonicity**: Adding edges to the neighbourhood of u can only increase
   or maintain its clustering coefficient.

### Example

```python
>>> G = nx.complete_graph(5)
>>> nx.clustering(G, 0)
1.0
>>> nx.clustering(G)
{0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}
```

```python
>>> G = nx.star_graph(4)  # Centre connected to 4 leaves, no triangles
>>> nx.clustering(G)
{0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
```

---

## 3. `networkx.diameter(G, e=None, usebounds=False, weight=None)`

### Description

Returns the **diameter** of the graph G.

**Definitions**:

- The **eccentricity** of a node v, `ecc(v)`, is the maximum shortest-path
  distance from v to any other node:

  ```
  ecc(v) = max { dist(v, u) : u in V(G) }
  ```

- The **diameter** of G is the maximum eccentricity over all nodes:

  ```
  diameter(G) = max { ecc(v) : v in V(G) }
  ```

- The **radius** of G is the minimum eccentricity:

  ```
  radius(G) = min { ecc(v) : v in V(G) }
  ```

Note that `radius(G) <= diameter(G)` always, with equality only for
*self-centred* graphs (e.g. complete graphs, where every node has the same
eccentricity).

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `G` | `nx.Graph` | A connected graph. |
| `e` | dict or None | Pre-computed eccentricity dictionary (optional). |
| `usebounds` | bool | Use a bound-based algorithm for efficiency (undirected only). |
| `weight` | string, function, or None | Edge weight attribute. |

### Returns

`int` — the diameter of the graph.

### Raises

- `NetworkXError` — if the graph is not connected (infinite path lengths exist).

### Known Values for Standard Graph Families

| Graph | Diameter | Radius |
|-------|----------|--------|
| Complete graph K_n | 1 | 1 |
| Path graph P_n | n - 1 | ceil((n-1)/2) |
| Cycle graph C_n | floor(n/2) | ceil(n/4) |
| Star graph S_n | 2 | 1 |

### Guaranteed Properties

1. **Diameter >= every eccentricity**: `diameter(G) >= ecc(v)` for all v in G.
2. **Diameter is an eccentricity**: There exists at least one node v such that
   `ecc(v) == diameter(G)`.
3. **Diameter >= radius**: `diameter(G) >= radius(G)`.
4. **Path graph**: `diameter(path_graph(n)) == n - 1` for n >= 1.

### Example

```python
>>> G = nx.Graph([(1, 2), (1, 3), (1, 4), (3, 4), (3, 5), (4, 5)])
>>> nx.diameter(G)
3
```

```python
>>> G = nx.path_graph(5)  # 0-1-2-3-4
>>> nx.diameter(G)        # distance from 0 to 4
4
```

---

## 4. `networkx.is_eulerian(G)`

### Description

Returns `True` if and only if `G` is **Eulerian**.

A graph is *Eulerian* if it contains an **Eulerian circuit**: a closed walk
that visits every edge exactly once.

### Necessary and Sufficient Conditions

**For undirected graphs** (Euler's theorem):

A connected undirected graph G is Eulerian if and only if every vertex has
**even degree**.

- Not connected → not Eulerian.
- Any vertex with odd degree → not Eulerian.

**For directed graphs**:

A strongly connected directed graph G is Eulerian if and only if every vertex
satisfies `in_degree(v) == out_degree(v)`.

- Not strongly connected → not Eulerian.
- Any vertex with `in_degree(v) != out_degree(v)` → not Eulerian.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `G` | `nx.Graph` or `nx.DiGraph` | A graph, either directed or undirected. |

### Returns

`bool` — True if G has an Eulerian circuit, False otherwise.

### Note on Isolated Vertices

Graphs with isolated vertices (degree 0) are **not** considered Eulerian by
this function, because an Eulerian circuit must use every edge and an isolated
vertex has no edges to traverse.

### Guaranteed Properties

1. **Directed cycle**: A directed cycle C_n (n >= 2) is Eulerian:
   each node has `in_degree == out_degree == 1`.
2. **Undirected cycle**: An undirected cycle C_n (n >= 3) is Eulerian:
   each node has degree 2 (even).
3. **Complete graph K_n with odd n**: Eulerian (each degree is n-1, which is even).
4. **Path graph P_n (n >= 2)**: Not Eulerian (endpoints have degree 1, odd).
5. **Complete bipartite graph K_{m,n}**: Eulerian if and only if both m and n
   are even.

### Example

```python
>>> nx.is_eulerian(nx.DiGraph({0: [3], 1: [2], 2: [3], 3: [0, 1]}))
True
>>> nx.is_eulerian(nx.complete_graph(5))
True
>>> nx.is_eulerian(nx.petersen_graph())
False
```

```python
# Directed cycle: each node has in_degree == out_degree == 1
>>> G = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
>>> nx.is_eulerian(G)
True
```
