""" Testfile for the dtnnode.py implementations """

from pydtnsim.nodes import SimpleCGRNode
from pydtnsim import Packet, Simulator


def test_simplenode_create_object():
    """Verify the correct instantiation of a node object."""
    sim = Simulator()
    node1 = SimpleCGRNode("TestNode1", None, __routing_algo, None, sim, [])
    assert node1.identifier == "TestNode1"


def test_simplenode_routing():
    """Verify basic routing functionality."""
    sim = Simulator()
    node1 = SimpleCGRNode("TestNode1", "contact_list", __routing_algo,
                          "topology", sim, [])
    packet = Packet("source_node", "end_node", 1)
    node1.route_packet(packet, 0)


def __routing_algo(packet, source_node, contact_graph, route_list,
                   contact_list, current_time, limbo, hotspots):
    """Routing algorithm function."""
    assert packet.source_node == "source_node"
    assert packet.end_node == "end_node"
    assert source_node == "TestNode1"
    assert contact_graph == "topology"
    assert contact_list == "contact_list"
    assert isinstance(route_list, dict)
    assert isinstance(limbo, list)
    assert current_time == 0
