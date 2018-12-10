import math

from pydtnsim.routing import dijkstra


def simple_direct_neighbor_function(contact_graph, node, destination,
                                    current_distance, set_visited,
                                    suppressed_contacts, lookahead_time):
    """Function that is used by the dijkstra implementation and that provides
    the adjecent nodes of a given node (i.e. the neighbors) and the
    corresponding weight (distance) of the specific neighbors return.
    """
    return contact_graph[node]


def test_dijkstra_one_node_graph():
    """Test function that execution on a graph with a single node (i.e. source
    node)."""
    graph = dict()
    graph['node1'] = frozenset()
    route, dist = dijkstra.get_best_route('node1', 'node1', graph,
                                          simple_direct_neighbor_function, 0)
    assert route == []
    assert dist == 0


def test_dijkstra_two_node_graph():
    """Test function that execution on a graph with two nodes and one "optimal"
    path."""
    graph = dict()
    graph['node1'] = frozenset([('node2', 42)])
    graph['node2'] = frozenset()
    route, dist = dijkstra.get_best_route('node1', 'node2', graph,
                                          simple_direct_neighbor_function, 0)
    assert route == ['node1', 'node2']
    assert dist == 42


def test_dijkstra_no_path_available():
    """Test function that execution on a graph with a three nodes and no path
    from source to dest available."""
    graph = dict()
    graph['node1'] = frozenset([('node2', 42)])
    graph['node2'] = frozenset()
    graph['node3'] = frozenset()
    route, dist = dijkstra.get_best_route('node1', 'node3', graph,
                                          simple_direct_neighbor_function, 0)
    assert route is None
    assert dist == math.inf


def test_dijkstra_complex_graph():
    """Test function that execution on a graph with multiple nodes."""
    graph = dict()
    graph['node1'] = frozenset([('node2', 10), ('node3', 4), ('node4', 2)])
    graph['node2'] = frozenset()
    graph['node3'] = frozenset([('node5', 16), ('node6', 3)])
    graph['node4'] = frozenset()
    graph['node5'] = frozenset([('node7', 8)])
    graph['node6'] = frozenset([('node7', 7)])
    graph['node7'] = frozenset([('node8', 11)])
    graph['node8'] = frozenset()
    route, dist = dijkstra.get_best_route('node1', 'node8', graph,
                                          simple_direct_neighbor_function, 0)
    assert route == ['node1', 'node3', 'node6', 'node7', 'node8']
    assert dist == 25


def test_dijkstra_complex_graph_with_loops():
    """Test function that execution on a graph with multiple nodes and multiple
    loops."""
    graph = dict()
    graph['node1'] = frozenset([('node2', 10), ('node3', 4), ('node4', 2)])
    graph['node2'] = frozenset()
    graph['node3'] = frozenset([('node5', 16), ('node6', 3)])
    graph['node4'] = frozenset()
    graph['node5'] = frozenset([('node7', 8)])
    graph['node6'] = frozenset([('node7', 7), ('node4', 1), ('node6', 1)])
    graph['node7'] = frozenset([('node8', 11), ('node6', 1)])
    graph['node8'] = frozenset()
    route, dist = dijkstra.get_best_route('node1', 'node8', graph,
                                          simple_direct_neighbor_function, 0)
    assert route == ['node1', 'node3', 'node6', 'node7', 'node8']
    assert dist == 25
