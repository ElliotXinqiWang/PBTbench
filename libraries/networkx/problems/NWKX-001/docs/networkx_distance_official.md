# NetworkX 3.4.2 — Distance Measures

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/distance_measures.html
> Version: NetworkX 3.4.2

## Overview

The distance measures module provides "Graph diameter, radius, eccentricity and other properties" for network analysis.

Module: `networkx.algorithms.distance_measures`

---

## Function Index

| Function | Purpose |
|----------|---------|
| `barycenter(G[, weight, attr, sp])` | Computes the barycenter of a connected graph with optional edge weights |
| `center(G[, e, usebounds, weight])` | Identifies the center nodes of graph G |
| `diameter(G[, e, usebounds, weight])` | Determines the maximum shortest path length in G |
| `harmonic_diameter(G[, sp])` | Calculates the harmonic diameter of graph G |
| `eccentricity(G[, v, sp, weight])` | Computes the maximum distance from specified nodes |
| `effective_graph_resistance(G[, weight, ...])` | Returns the effective graph resistance metric |
| `kemeny_constant(G, *[, weight])` | Calculates the Kemeny constant of the graph |
| `periphery(G[, e, usebounds, weight])` | Identifies the peripheral nodes of graph G |
| `radius(G[, e, usebounds, weight])` | Determines the minimum eccentricity in G |
| `resistance_distance(G[, nodeA, nodeB, ...])` | Computes resistance distance between node pairs |

---

## Detailed Function Documentation

### `eccentricity(G, v=None, sp=None, weight=None)`

**Description:** "Returns the eccentricity of nodes in G." The eccentricity metric measures "the maximum distance from v to all other nodes in G."

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `G` | NetworkX graph | The input graph to analyze |
| `v` | node, optional | When specified, returns the eccentricity value for only this node |
| `sp` | dict of dicts, optional | Pre-computed all-pairs shortest path lengths organized as nested dictionaries |
| `weight` | string, function, or None | Defines how edge weights are handled: as string (edge attribute key), callable function (custom weight logic), or None (uniform weight of 1) |

**Weight Handling Notes:**

- Floating-point weights may introduce rounding errors; integer weights are recommended
- All weights should be positive values

**Returns:**

- **ecc** (dictionary): Maps each node to its eccentricity value

**Examples:**

```python
G = nx.Graph([(1, 2), (1, 3), (1, 4), (3, 4), (3, 5), (4, 5)])

# Eccentricity for all nodes
dict(nx.eccentricity(G))
# Output: {1: 2, 2: 3, 3: 2, 4: 2, 5: 3}

# Eccentricity for specific nodes
dict(nx.eccentricity(G, v=[1, 5]))
# Output: {1: 2, 5: 3}
```

---

### `diameter(G, e=None, usebounds=False, weight=None)`

**Description:** "Returns the diameter of the graph G. The diameter is the maximum eccentricity."

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| **G** | NetworkX graph | The input graph to analyze |
| **e** | eccentricity dictionary, optional | A precomputed dictionary of eccentricities to avoid recalculation |
| **usebounds** | boolean, optional | Whether to use bounds (see signature) |
| **weight** | string, function, or None | Specifies how edge weights are handled: string = edge attribute key; function = custom weight calc accepting (u, v, edge_attrs) → number; None (default) = all edges unit weight |

**Returns:**

- **d** (integer): The diameter value of the graph

**Notes:**

"Weights stored as floating point values can lead to small round-off errors in distances. Use integer weights to avoid this."

"Weights should be positive, since they are distances."

**Example:**

```python
G = nx.Graph([(1, 2), (1, 3), (1, 4), (3, 4), (3, 5), (4, 5)])
nx.diameter(G)
# Output: 3
```

**See Also:** `eccentricity()`

---

### `radius(G, e=None, usebounds=False, weight=None)`

**Description:** "Returns the radius of the graph G." The radius is defined as "the minimum eccentricity."

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| **G** | NetworkX graph | The input graph to analyze |
| **e** | dict, optional | A precomputed dictionary of eccentricity values |
| **usebounds** | bool, optional | Whether to use bounds |
| **weight** | string, function, or None | Edge weight specification. String = edge attribute key; function = custom weight accepting (u, v, edge_attrs) → number; None (default) = all edges equal weight |

**Returns:**

- **r** (integer): The radius value of the graph

**Notes:**

- Floating-point weights can introduce rounding errors; integer weights are recommended
- Weights should be positive values since they represent distances

**Example:**

```python
>>> G = nx.Graph([(1, 2), (1, 3), (1, 4), (3, 4), (3, 5), (4, 5)])
>>> nx.radius(G)
2
```

---

### `center(G, e=None, usebounds=False, weight=None)`

**Description:** "Identifies the center nodes of graph G."

The center of a graph is the set of nodes with eccentricity equal to the radius.

**Parameters:**

- **G** (NetworkX graph): Input graph
- **e** (eccentricity dict, optional): Precomputed eccentricities
- **usebounds** (bool, optional)
- **weight** (string, function, or None)

---

### `periphery(G, e=None, usebounds=False, weight=None)`

**Description:** "Identifies the peripheral nodes of graph G."

The periphery of a graph is the set of nodes with eccentricity equal to the diameter.

**Parameters:**

- **G** (NetworkX graph): Input graph
- **e** (eccentricity dict, optional): Precomputed eccentricities
- **usebounds** (bool, optional)
- **weight** (string, function, or None)

---

### `barycenter(G, weight=None, attr=None, sp=None)`

**Description:** Computes the barycenter of a connected graph with optional edge weights.

**Parameters:**

- **G** (NetworkX graph): Input graph
- **weight** (string or None, optional): Edge attribute for weights
- **attr** (string or None, optional): Attribute to store barycenter values on nodes
- **sp** (dict of dicts, optional): Pre-computed all-pairs shortest paths

---

### `resistance_distance(G, nodeA=None, nodeB=None, ...)`

**Description:** Computes resistance distance between node pairs.

---

### `effective_graph_resistance(G, weight=None, ...)`

**Description:** Returns the effective graph resistance metric.

---

### `kemeny_constant(G, *, weight=None)`

**Description:** Calculates the Kemeny constant of the graph.

---

### `harmonic_diameter(G, sp=None)`

**Description:** Calculates the harmonic diameter of graph G.
