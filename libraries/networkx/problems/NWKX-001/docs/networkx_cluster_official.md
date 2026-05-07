# NetworkX 3.4.2 — Clustering Algorithms

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/clustering.html
> Version: NetworkX 3.4.2

## Overview

The clustering module provides "algorithms to characterize the number of triangles in a graph."

Module: `networkx.algorithms.cluster`

---

## Function Index

| Function | Description |
|----------|-------------|
| `triangles(G[, nodes])` | Computes the number of triangles that include a node as a vertex |
| `transitivity(G)` | Computes graph transitivity, the fraction of all possible triangles present in G |
| `clustering(G[, nodes, weight])` | Computes the clustering coefficient for nodes |
| `average_clustering(G[, nodes, weight, count_zeros])` | Computes the average clustering coefficient for the graph |
| `square_clustering(G[, nodes])` | Computes the squares clustering coefficient for nodes |
| `generalized_degree(G[, nodes])` | Computes the generalized degree of nodes |

---

## Detailed Function Documentation

### `triangles(G, nodes=None)`

**Description:** Computes the number of triangles that include a node as a vertex.

**Parameters:**

- **G** (graph): A NetworkX graph object
- **nodes** (node, iterable of nodes, or None, default=None):
  - Single node: returns triangle count for that node
  - Iterable of nodes: computes triangle count for each node
  - None: computes triangle count across all nodes in the graph

**Returns:**

- **out** (dict or int):
  - Returns a dictionary with nodes as keys and triangle counts as values when `nodes` is a container
  - Returns an integer representing the triangle count when `nodes` specifies a single node

**Notes:**

> "Self loops are ignored."

**Examples:**

```python
G = nx.complete_graph(5)
nx.triangles(G, 0)
# Output: 6

nx.triangles(G)
# Output: {0: 6, 1: 6, 2: 6, 3: 6, 4: 6}

list(nx.triangles(G, [0, 1]).values())
# Output: [6, 6]
```

**Backend Support:** cugraph (GPU-accelerated), graphblas (OpenMP-enabled sparse linear algebra)

---

### `transitivity(G)`

**Description:** Calculates the graph transitivity, defined as "the fraction of all possible triangles present in G." The function identifies potential triangles by counting triads (two edges sharing a vertex).

**Parameters:**

- **G** (graph): The input network to analyze

**Returns:**

- **out** (float): The transitivity coefficient of the graph

**Formula:**

> T = 3 × (#triangles) / (#triads)

**Notes:**

- Self-loops in the graph are disregarded during computation
- Directed graphs are not currently supported by the standard implementation

**Example:**

```python
>>> G = nx.complete_graph(5)
>>> print(nx.transitivity(G))
1.0
```

---

### `clustering(G, nodes=None, weight=None)`

**Description:** Evaluates the clustering coefficient for specified nodes.

**Parameters:**

- **G**: A graph object
- **nodes**: Specifies which nodes to analyze
  - Single node: returns clustering coefficient for that node
  - Iterable of nodes: computes coefficient for each node
  - None (default): computes for all nodes in the graph
- **weight** (string or None, default=None):
  - Edge attribute name containing numerical weight values
  - If None, each edge has weight 1

**Returns:**

- **out** (float or dictionary): Either a float (for single node) or dictionary (for multiple nodes/all nodes) containing the clustering coefficient at specified nodes

**Clustering Coefficient Definitions:**

#### Unweighted Graphs

The clustering coefficient for node u is:

```
c_u = 2T(u) / [deg(u)(deg(u)-1)]
```

Where T(u) represents the number of triangles through node u and deg(u) is the node's degree.

#### Weighted Graphs

Uses geometric averaging of subgraph edge weights:

```
c_u = [1 / deg(u)(deg(u)-1)] × Σ(ŵ_uv × ŵ_uw × ŵ_vw)^(1/3)
```

Where normalized weights ŵ = w / max(w). This definition supports negative edge weights.

#### Directed Graphs

For directed graphs, the formula accounts for directed triangles:

```
c_u = T(u) / [2(deg_tot(u)(deg_tot(u)-1) - 2deg_↔(u))]
```

Where deg_tot(u) is the sum of in-degree and out-degree, and deg_↔(u) is reciprocal degree.

**Notes:**

- Self-loops are ignored in calculations
- Clustering coefficient equals 0 when deg(u) < 2
- Different formulations apply depending on graph type (directed/undirected) and weighting

**Example:**

```python
G = nx.complete_graph(5)
print(nx.clustering(G, 0))   # Output: 1.0
print(nx.clustering(G))
# Output: {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}
```

**References:**

1. Saramäki et al., Physical Review E 75, 027105 (2007)
2. Onnela et al., Physical Review E 71(6), 065103 (2005)
3. Costantini & Perugini, PLoS ONE 9(2), e88669 (2014)
4. Fagiolo, Physical Review E 76(2), 026107 (2007)

**Backend Support:** cugraph (GPU-accelerated, directed graphs and weight parameter not yet supported), graphblas (OpenMP-enabled sparse linear algebra)

---

### `average_clustering(G, nodes=None, weight=None, count_zeros=True)`

**Description:** Calculates the mean clustering coefficient across a network graph.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `G` | graph | required | The input graph to analyze |
| `nodes` | container of nodes | None | Subset of nodes for computing the average; None means all nodes |
| `weight` | string or None | None | Edge attribute for numerical weight values; if None, all edges have weight 1 |
| `count_zeros` | bool | True | When False, excludes nodes with zero clustering from calculation |

**Returns:**

- **avg** (float): The average clustering coefficient value

**Formula:**

The average clustering coefficient: C = (1/n) Σ(v ∈ G) c_v, where n is the number of nodes in G.

**Notes:**

- This implementation prioritizes memory efficiency over raw speed
- Self-loops are disregarded in calculations
- Alternative approach: use the `clustering()` function separately, then compute the mean manually

**Example:**

```python
>>> G = nx.complete_graph(5)
>>> print(nx.average_clustering(G))
1.0
```

**Backend Support:** cugraph (GPU-accelerated, limited support), graphblas (OpenMP-enabled sparse linear algebra)

---

### `square_clustering(G, nodes=None)`

**Description:** Determines the squares clustering coefficient for nodes.

**Parameters:**

- **G**: graph
- **nodes** (optional): node, iterable of nodes, or None

---

### `generalized_degree(G, nodes=None)`

**Description:** Evaluates the generalized degree measurement for nodes.

**Parameters:**

- **G**: graph
- **nodes** (optional): node, iterable of nodes, or None
