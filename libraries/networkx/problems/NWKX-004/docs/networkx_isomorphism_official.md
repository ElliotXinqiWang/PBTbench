# NetworkX 3.4.2 — Graph Isomorphism (VF2++ Algorithm)

> Source: https://networkx.org/documentation/networkx-3.4.2/reference/algorithms/isomorphism.html
> Version: NetworkX 3.4.2

## Overview

Graph isomorphism determines whether two graphs G1 and G2 have the same structure, i.e., whether there exists a bijection f: V(G1) → V(G2) such that (u, v) is an edge in G1 if and only if (f(u), f(v)) is an edge in G2.

NetworkX implements the **VF2++ algorithm** for graph isomorphism testing, which is a highly efficient backtracking algorithm with improved pruning rules compared to VF2.

---

## API Reference

### `vf2pp_is_isomorphic(G1, G2, node_label=None, default_label=None)`

Examines whether G1 and G2 are isomorphic.

**Parameters:**
- `G1, G2` : NetworkX Graph or MultiGraph instances. The two graphs to check for isomorphism.
- `node_label` : str, optional. The name of the node attribute to be used when comparing nodes. Default is None (node attributes are not considered).
- `default_label` : scalar. Default value to use when a node doesn't have the node_label attribute. Default is None.

**Returns:**
- `bool` — True if the two graphs are isomorphic, False otherwise.

**Examples:**
```python
>>> G1 = nx.path_graph(4)
>>> G2 = nx.path_graph(4)
>>> nx.vf2pp_is_isomorphic(G1, G2, node_label=None)
True
```

---

### `vf2pp_isomorphism(G1, G2, node_label=None, default_label=None)`

Return an isomorphic mapping between G1 and G2 if it exists.

**Returns:**
- `dict or None` — Node mapping if the two graphs are isomorphic. None otherwise. The dict maps nodes of G1 to nodes of G2.

**Examples:**
```python
>>> G1 = nx.path_graph(4)
>>> G2 = nx.path_graph(4)
>>> nx.vf2pp_isomorphism(G1, G2, node_label=None)
{1: 1, 2: 2, 0: 0, 3: 3}
```

---

### `vf2pp_all_isomorphisms(G1, G2, node_label=None, default_label=None)`

Yields all possible mappings between G1 and G2.

**Yields:**
- `dict` — Isomorphic mapping between nodes in G1 and G2.

---

## Mathematical Properties of Isomorphism

A graph isomorphism between G1 and G2 is a bijection f: V(G1) → V(G2) satisfying:
1. **Edge preservation**: (u, v) ∈ E(G1) ⟺ (f(u), f(v)) ∈ E(G2)
2. **For directed graphs**: (u, v) ∈ E(G1) ⟺ (f(u), f(v)) ∈ E(G2) (direction preserved)

**Key properties:**
- Isomorphism is an equivalence relation: if G1 ≅ G2 and G2 ≅ G3, then G1 ≅ G3
- **Relabeling invariance**: If G2 is obtained from G1 by relabeling nodes (applying a permutation), then G1 and G2 are isomorphic
- Isomorphic graphs must have identical degree sequences
- For directed graphs, in-degree and out-degree sequences must both match

## Testing Strategy for Isomorphism

A fundamental property: if you take any graph G1 and relabel its nodes (apply any permutation), the result G2 must be recognized as isomorphic to G1.

```python
import networkx as nx
import random

G1 = nx.DiGraph()
G1.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])

# Any relabeling produces an isomorphic graph
nodes = list(G1.nodes())
shuffled = nodes.copy()
random.shuffle(shuffled)
mapping = dict(zip(nodes, shuffled))
G2 = nx.relabel_nodes(G1, mapping)

assert nx.vf2pp_is_isomorphic(G1, G2) == True  # must hold
```

This property is especially important for **directed graphs with multiple in-degree nodes** where the algorithm may need extensive backtracking.
