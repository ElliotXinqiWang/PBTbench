"""Basic tests for networkx."""
import networkx as nx
import pytest


# ---------------------------------------------------------------------------
# topological_generations
# ---------------------------------------------------------------------------

def test_topological_generations_single_node():
    """Single isolated node: exactly one generation containing that node."""
    G = nx.DiGraph()
    G.add_node(42)
    gens = list(nx.topological_generations(G))
    assert len(gens) == 1
    assert 42 in gens[0]


def test_topological_generations_multiple_isolated_nodes():
    """
    A DiGraph with no edges: every node has in-degree 0.
    They all form a single generation (no propagation needed).
    """
    G = nx.DiGraph()
    G.add_nodes_from([0, 1, 2, 3])
    gens = [sorted(g) for g in nx.topological_generations(G)]
    assert gens == [[0, 1, 2, 3]]


def test_topological_generations_node_count():
    """
    The total number of nodes across all generations must equal the number
    of nodes in the graph.  This is a basic sanity check that does not
    depend on multi-level propagation.
    """
    G = nx.DiGraph()
    G.add_nodes_from(range(5))
    all_in_gens = [node for gen in nx.topological_generations(G) for node in gen]
    assert len(all_in_gens) == 5
    assert set(all_in_gens) == set(G.nodes())


def test_topological_generations_undirected_raises():
    """topological_generations must raise NetworkXError for undirected graph."""
    G = nx.Graph([(0, 1)])
    with pytest.raises(nx.NetworkXError):
        list(nx.topological_generations(G))


# ---------------------------------------------------------------------------
# clustering
# ---------------------------------------------------------------------------

def test_clustering_triangle():
    """Test Clustering triangle."""
    G = nx.complete_graph(3)
    cc = nx.clustering(G)
    for v, val in cc.items():
        assert 0.0 < val <= 1.0, f"K_3 clustering[{v}] = {val}, expected in (0, 1]"


def test_clustering_star_graph():
    """
    Star graph S_4 (center connected to 4 leaves): the center has degree 4
    but no two neighbors are connected, so 0 triangles.  Clustering of
    center = 0.  Leaves have degree 1, clustering defined as 0.
    """
    G = nx.star_graph(4)  # nodes: 0 (center), 1-4 (leaves)
    cc = nx.clustering(G)
    # All nodes have zero triangles
    for v, val in cc.items():
        assert val == 0.0, f"Star: clustering[{v}] = {val}, expected 0.0"


def test_clustering_returns_dict_for_all_nodes():
    """clustering(G) with no node argument returns a dict keyed by all nodes."""
    G = nx.cycle_graph(5)
    cc = nx.clustering(G)
    assert isinstance(cc, dict)
    assert set(cc.keys()) == set(G.nodes())


def test_clustering_single_node_query():
    """clustering(G, v) for a single node returns a float."""
    G = nx.complete_graph(5)
    val = nx.clustering(G, 0)
    assert isinstance(val, float)


# ---------------------------------------------------------------------------
# diameter
# ---------------------------------------------------------------------------

def test_diameter_complete_graph():
    """K_n (n>=2) has diameter 1: all nodes are directly connected."""
    for n in [2, 3, 5, 10]:
        G = nx.complete_graph(n)
        assert nx.diameter(G) == 1, f"K_{n} diameter should be 1"


def test_diameter_cycle_graph():
    """
    Cycle graph C_n:
      - odd n: diameter = (n-1)//2
      - even n: diameter = n//2
    Test a few known values.
    """
    # C_4: diameter = 2
    assert nx.diameter(nx.cycle_graph(4)) == 2
    # C_5: diameter = 2
    assert nx.diameter(nx.cycle_graph(5)) == 2
    # C_6: diameter = 3
    assert nx.diameter(nx.cycle_graph(6)) == 3


def test_diameter_disconnected_raises():
    """diameter must raise NetworkXError for disconnected graphs."""
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2])
    G.add_edge(0, 1)
    # Node 2 is isolated
    with pytest.raises(nx.NetworkXError):
        nx.diameter(G)


def test_diameter_single_edge():
    """Graph with one edge: diameter = 1."""
    G = nx.Graph([(0, 1)])
    assert nx.diameter(G) == 1


# ---------------------------------------------------------------------------
# is_eulerian
# ---------------------------------------------------------------------------

def test_is_eulerian_undirected_complete_odd():
    """
    Complete graph K_n with odd n: every node has even degree (n-1 is even),
    and the graph is connected.  So K_n with odd n is Eulerian.
    """
    for n in [3, 5, 7]:
        G = nx.complete_graph(n)
        assert nx.is_eulerian(G), f"K_{n} (odd n) should be Eulerian"


def test_is_eulerian_undirected_path_is_not():
    """Path graph P_n (n >= 2): endpoints have degree 1 (odd), not Eulerian."""
    for n in [2, 3, 5]:
        G = nx.path_graph(n)
        assert not nx.is_eulerian(G), f"P_{n} should not be Eulerian"


def test_is_eulerian_undirected_cycle():
    """
    Cycle graph C_n: every node has degree 2 (even) and the graph is
    connected.  C_n is Eulerian for all n >= 3.
    """
    for n in [3, 4, 5, 6]:
        G = nx.cycle_graph(n)
        assert nx.is_eulerian(G), f"C_{n} should be Eulerian"


def test_is_eulerian_directed_not_strongly_connected():
    """
    A directed graph where in_degree == out_degree for all nodes but the
    graph is not strongly connected: is_eulerian must return False.
    Example: two separate directed cycles (0->1->0) and (2->3->2).
    Both conditions fail together.
    """
    G = nx.DiGraph([(0, 1), (1, 0), (2, 3), (3, 2)])
    assert not nx.is_eulerian(G)


def test_is_eulerian_directed_unbalanced():
    """
    Directed graph where one node has in_degree != out_degree.
    Not Eulerian.
    """
    G = nx.DiGraph([(0, 1), (0, 2)])  # node 0: out=2, in=0
    assert not nx.is_eulerian(G)
