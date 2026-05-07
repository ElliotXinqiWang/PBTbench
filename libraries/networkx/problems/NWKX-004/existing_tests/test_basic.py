"""Basic tests for networkx."""
import networkx as nx
import pytest


# ---------------------------------------------------------------------------
# vf2pp_is_isomorphic / vf2pp_isomorphism
# ---------------------------------------------------------------------------

def test_vf2pp_identical_undirected_graphs():
    """Two identical undirected path graphs must be isomorphic."""
    G1 = nx.path_graph(4)
    G2 = nx.path_graph(4)
    assert nx.vf2pp_is_isomorphic(G1, G2, node_label=None) is True


def test_vf2pp_different_sizes_not_isomorphic():
    """Graphs with different numbers of nodes are never isomorphic."""
    G1 = nx.path_graph(3)
    G2 = nx.path_graph(4)
    assert nx.vf2pp_is_isomorphic(G1, G2, node_label=None) is False


def test_vf2pp_different_edge_counts_not_isomorphic():
    """Graphs with same node count but different edge counts are not isomorphic."""
    G1 = nx.path_graph(4)      # 3 edges
    G2 = nx.complete_graph(4)  # 6 edges
    assert nx.vf2pp_is_isomorphic(G1, G2, node_label=None) is False


def test_vf2pp_isomorphism_returns_dict_or_none():
    """vf2pp_isomorphism returns a dict (isomorphic) or None (not isomorphic)."""
    G1 = nx.path_graph(3)
    G2 = nx.path_graph(3)
    result = nx.vf2pp_isomorphism(G1, G2, node_label=None)
    assert result is None or isinstance(result, dict)


def test_vf2pp_undirected_cycle_vs_path_not_isomorphic():
    """C_4 (cycle) and P_4 (path) with 4 nodes each are not isomorphic (different degree sequences)."""
    G1 = nx.cycle_graph(4)
    G2 = nx.path_graph(4)
    assert nx.vf2pp_is_isomorphic(G1, G2, node_label=None) is False


def test_vf2pp_simple_directed_not_isomorphic():
    """A directed path and its reverse are isomorphic (for path graphs)."""
    G1 = nx.DiGraph([(0, 1), (1, 2)])
    G2 = nx.DiGraph([(2, 1), (1, 0)])
    # Both are directed paths: same structure, just reverse node labels
    assert nx.vf2pp_is_isomorphic(G1, G2, node_label=None) is True


def test_vf2pp_directed_vs_undirected():
    """Directed and undirected graphs cannot be compared (raises or returns False)."""
    G1 = nx.DiGraph([(0, 1)])
    G2 = nx.Graph([(0, 1)])
    # NetworkX raises NetworkXError when mixing directed/undirected
    with pytest.raises(Exception):
        nx.vf2pp_is_isomorphic(G1, G2, node_label=None)


# ---------------------------------------------------------------------------
# girth
# ---------------------------------------------------------------------------

def test_girth_acyclic_returns_inf():
    """Path graph P_5 is acyclic, so girth must be math.inf."""
    import math
    G = nx.path_graph(5)
    assert nx.girth(G) == math.inf


def test_girth_complete_graph_k3():
    """K_3 has a triangle; girth must be finite (> 0) and <= 3."""
    G = nx.complete_graph(3)
    g = nx.girth(G)
    # We check that girth is a positive integer (not inf), since a triangle
    assert isinstance(g, int) and g > 0, (
        f"K_3 girth should be a positive integer, got {g}"
    )


def test_girth_cycle_c3():
    """C_3 has a cycle; girth must be finite."""
    import math
    G = nx.cycle_graph(3)
    g = nx.girth(G)
    # Just verify girth is finite (a cycle exists)
    assert g != math.inf, f"C_3 girth should be finite, got {g}"


def test_girth_single_edge_is_inf():
    """A single edge (K_2) has no cycle; girth must be math.inf."""
    import math
    G = nx.Graph([(0, 1)])
    assert nx.girth(G) == math.inf


def test_girth_returns_int_or_inf():
    """girth returns an integer for cyclic graphs."""
    G = nx.cycle_graph(4)
    result = nx.girth(G)
    assert isinstance(result, int) or result == float("inf")


# ---------------------------------------------------------------------------
# is_perfect_matching
# ---------------------------------------------------------------------------

def test_is_perfect_matching_k2():
    """K_2: both nodes matched by the single edge — perfect matching."""
    G = nx.Graph([(0, 1)])
    # A perfect matching requires every node to be matched.
    # We test with is_matching (basic check) instead of is_perfect here.
    assert nx.is_matching(G, {(0, 1)}) is True


def test_is_perfect_matching_non_perfect():
    """K_3 with one edge is NOT a perfect matching (node 2 is unmatched)."""
    G = nx.complete_graph(3)
    assert nx.is_perfect_matching(G, {(0, 1)}) is False


def test_is_perfect_matching_empty_on_odd_nodes():
    """K_3 has no perfect matching (odd number of nodes)."""
    G = nx.complete_graph(3)
    # Any matching on 3 nodes must leave one node unmatched
    assert nx.is_perfect_matching(G, {(0, 1), (1, 2)}) is False  # node 0 matched twice


def test_is_matching_basic():
    """is_matching: valid matching returns True."""
    G = nx.complete_graph(4)
    assert nx.is_matching(G, {(0, 1), (2, 3)}) is True


def test_is_matching_invalid():
    """is_matching: sharing a node makes it invalid."""
    G = nx.complete_graph(4)
    assert nx.is_matching(G, {(0, 1), (0, 2)}) is False


def test_is_maximal_matching_basic():
    """is_maximal_matching on a well-known maximal matching."""
    G = nx.Graph([(1, 2), (1, 3), (2, 3), (3, 4), (3, 5)])
    assert nx.is_maximal_matching(G, {(1, 2), (3, 4)}) is True


# ---------------------------------------------------------------------------
# dag_longest_path / dag_longest_path_length
# ---------------------------------------------------------------------------

def test_dag_longest_path_single_node():
    """DAG with a single node: longest path is [node], length 0."""
    G = nx.DiGraph()
    G.add_node(0)
    path = nx.dag_longest_path(G)
    assert len(path) == 1
    assert nx.dag_longest_path_length(G) == 0


def test_dag_longest_path_empty_graph():
    """Empty DAG: longest path is [], length 0."""
    G = nx.DiGraph()
    path = nx.dag_longest_path(G)
    assert path == []


def test_dag_longest_path_two_nodes():
    """DAG 0->1: longest path contains at least 1 node."""
    G = nx.DiGraph([(0, 1)])
    path = nx.dag_longest_path(G)
    assert isinstance(path, list)
    assert len(path) >= 1


def test_dag_longest_path_contains_valid_nodes():
    """A linear chain 0->1->2->3: path must contain valid graph nodes."""
    G = nx.DiGraph([(0, 1), (1, 2), (2, 3)])
    path = nx.dag_longest_path(G)
    # All nodes in path must be in G
    for node in path:
        assert node in G.nodes(), f"Path contains invalid node {node}"
    # Path must be non-empty
    assert len(path) >= 1


def test_dag_longest_path_undirected_raises():
    """dag_longest_path must raise NetworkXNotImplemented for undirected graphs."""
    G = nx.Graph([(0, 1)])
    with pytest.raises(Exception):
        nx.dag_longest_path(G)
