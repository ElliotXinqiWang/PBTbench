# Strategy Specification — NWKX-001

## Bug 1: `topological_generations` wrong traversal direction

**File**: `networkx/algorithms/dag.py`
**Injected change**: `G.neighbors(node)` → `G.predecessors(node)`

### Why default strategies don't work

A default random DiGraph generator (e.g. `st.integers` edges added at random)
would most likely generate graphs with only 1–2 levels, or a single source
node.  For a graph with a single source node and no other structure, the bug
manifests immediately: `G.predecessors(source) == []` for any source
(in-degree 0) node, so the algorithm yields only the first generation and
then stops — raising `NetworkXUnfeasible` for non-trivial DAGs.

### Targeted strategy

```python
@st.composite
def dag_with_multiple_generations(draw):
    n = draw(st.integers(min_value=4, max_value=12))
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    # Force diamond: 0->1, 0->2, 1->3, 2->3 (3+ generations, in-degree≥2 at node 3)
    G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])
    # Optional random edges (i<j to guarantee acyclicity)
    ...
    return G
```

**Trigger probability with default strategy**: ~100% for any DAG with ≥2 levels,
because the predecessors of level-0 nodes are always empty.

**Boundary**: Any DAG with at least 1 edge triggers the bug (1 edge = 2 levels).
A graph with only isolated nodes does NOT trigger the bug (single generation,
no propagation needed).

**Why the property catches it**: `set().union(*list(nx.topological_generations(G))) == set(G.nodes())`
The buggy function raises `NetworkXUnfeasible` for any multi-level DAG, which
the test catches as an `AssertionError`.

---

## Bug 2: `clustering` wrong denominator

**File**: `networkx/algorithms/cluster.py`
**Injected change**: `d * (d - 1)` → `d * (d + 1)` (unweighted undirected path)

### Why default strategies don't work

Random graphs are unlikely to produce complete subgraphs where the exact value
of the clustering coefficient is predictable.  The bug only matters when the
expected value is known, which requires structured input.

### Targeted strategy

```python
n = st.integers(min_value=4, max_value=10)
G = nx.complete_graph(n)
# Expected: clustering(G, v) == 1.0 for all v
```

**Trigger probability with default strategy**: Near 0% — random graphs rarely
have a clustering coefficient that is both non-zero and predictable to 1.0.

**Boundary**: The bug triggers for any node with degree ≥ 2 in a graph with
triangles.  For K_n with n ≥ 4:
- Correct:  `t / (d*(d-1)) = 2*(n-2) / ((n-1)*(n-2)) = 1.0`
- Buggy:    `t / (d*(d+1)) = 2*(n-2) / ((n-1)*(n))   < 1.0`

K_3 is also affected (degree 2, giving `2/(2*3) = 0.333` instead of 1.0).

---

## Bug 3: `diameter` returns `min` instead of `max`

**File**: `networkx/algorithms/distance_measures.py`
**Injected change**: `max(e.values())` → `min(e.values())`

### Why default strategies don't work

For complete graphs (diameter = 1 = radius), `min == max`, so the bug is
invisible.  The bug only manifests when diameter > radius, which requires
non-uniform eccentricity values.

### Targeted strategy

```python
n = st.integers(min_value=3, max_value=10)
G = nx.path_graph(n)
# diameter(P_n) = n-1
# radius(P_n)   = ceil((n-1)/2)
# For n >= 3: n-1 > ceil((n-1)/2)
```

**Trigger probability with default strategy**: 0% for complete graphs (where
diameter = radius = 1).  For path graphs P_n (n ≥ 3), the bug is always
visible.

**Boundary**: Any connected graph where diameter ≠ radius will trigger this.
Path graphs are the simplest family with this property.  P_3: diameter=2,
radius=1 (min=1≠2=max); P_4: diameter=3, radius=2.

---

## Bug 4: `is_eulerian` uses `degree` instead of `out_degree`

**File**: `networkx/algorithms/euler.py`
**Injected change**: `G.out_degree(n)` → `G.degree(n)` in directed graph branch

### Why default strategies don't work

The bug only affects directed graphs.  For undirected graphs, the separate
code path (`all(d % 2 == 0 for v, d in G.degree())`) is used and is unaffected.
Random directed graphs are rarely Eulerian, so finding one that should be
True but returns False requires deliberate construction.

### Targeted strategy

```python
@st.composite
def directed_eulerian_cycle(draw):
    n = draw(st.integers(min_value=3, max_value=10))
    G = nx.DiGraph()
    for i in range(n):
        G.add_edge(i, (i + 1) % n)
    # Each node: in_degree=1, out_degree=1, degree=2
    # Correct check: in(1)==out(1) → True
    # Buggy check:   in(1)==degree(2) → False
    return G
```

**Trigger probability with default strategy**: ~0% because random directed
graphs are almost never Eulerian, so the True → False flip is invisible.
You need to construct an Eulerian graph deliberately.

**Boundary**: The bug triggers for any directed Eulerian graph where each node
has in_degree = out_degree = k for k ≥ 1 (since degree = 2k ≠ k).
The simplest case is a directed cycle (k=1).
