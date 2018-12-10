import math
import pytest

from pydtnsim.routing import cgr_anchor
from pydtnsim.routing import cgr_basic
from pydtnsim.routing import scgr

from pydtnsim.backend import QSim

from pydtnsim.routing.cgr_basic import Route, Neighbor

from pydtnsim import Contact, ContactPlan, ContactGraph, Packet
from pydtnsim import ContactIdentifier
from pydtnsim.monitors import MonitorNotifier

testdata = [(cgr_basic), (cgr_anchor)]

testdata_routing = [(cgr_basic), (cgr_anchor), (scgr)]


class DummySimulator():
    def __init__(self):
        self.env = QSim()
        self.notifier = MonitorNotifier(self.env)


@pytest.mark.parametrize("mod", testdata)
def test_load_route_list(mod):
    """Test function that tests the route-finding capabilities of the
    load_route_list function and tests the correctness.
    """
    # First, create an contact plan that is then converted to the contact graph
    # representation and later processed by load_route_list

    # The following topology is tested in this test case:
    #               +---+
    #               | 4 |
    #     [20;30]+--+---+--+[70:80]
    #            |         |
    #          +-+-+     +-+-+
    #          | 2 |     | 3 |
    #          +-+-+     +-+-+
    #            |         |
    #     [10;20]+--+---+--+[40:50]
    #               | 1 |
    #               +---+
    contact_plan = ContactPlan(1000, 0)

    contact_plan.add_contact('node1', 'node2', 10, 20)
    contact_plan.add_contact('node1', 'node3', 40, 50)
    contact_plan.add_contact('node2', 'node4', 20, 30)
    contact_plan.add_contact('node3', 'node4', 70, 80)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    # Now generate a route list for possible routes from node1 to node4
    route_list_node14 = mod.load_route_list(contact_graph, 'node1', 'node4', 0)

    # Make sure that two routes were found
    assert len(route_list_node14) == 2

    # Assert characteristics of the found routes
    route1 = route_list_node14[0]
    assert route1.transmission_plan == ([('node1', 'node2', 10, 20, 1000, 0),
                                         ('node2', 'node4', 20, 30, 1000, 0)])

    assert route1.edt == 20
    assert route1.capacity == 10000
    assert route1.to_time == 20

    route2 = route_list_node14[1]
    assert route2.transmission_plan == ([('node1', 'node3', 40, 50, 1000, 0),
                                         ('node3', 'node4', 70, 80, 1000, 0)])

    assert route2.edt == 70
    assert route2.capacity == 10000
    assert route2.to_time == 50


@pytest.mark.parametrize("mod", testdata)
def test_load_route_list_unavailable_route(mod):
    """Test function that tests that no route is found.
    """
    # First, create an contact plan that is then converted to the contact graph
    # representation and later processed by load_route_list

    # The following topology is tested in this test case:
    #    +---+         +---+         +---+         +---+
    #    | 1 +---------+ 2 +---------+ 3 +---------+ 4 |
    #    +---+  35:40  +---+  20:40  +---+  20:25  +---+

    contact_plan = ContactPlan(1000, 0)

    contact_plan.add_contact('node1', 'node2', 35, 40)
    contact_plan.add_contact('node2', 'node3', 20, 40)
    contact_plan.add_contact('node3', 'node4', 20, 25)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    # Now generate a route list for possible routes from node1 to node4
    route_list_node14 = mod.load_route_list(contact_graph, 'node1', 'node4', 0)

    # Make sure that two routes were found
    assert len(route_list_node14) == 0


@pytest.mark.parametrize("mod", testdata)
def test_load_route_list_no_route(mod):
    """Test function that tests the route-finding capabilities of the
    load_route_list function and tests that no route is found if contacts on
    route do not add up.
    """
    # First, create an contact plan that is then converted to the contact graph
    # representation and later processed by load_route_list

    # The following topology is tested in this test case:
    #           +---+
    #           | 5 |
    # [20;30]+--+---+--+[70:80]
    #        |         |
    #      +-+-+     +-+-+
    #      | 3 |     | 4 |
    #      +-+-+     +-+-+
    #        |         |
    # [10;20]+--+---+--+[40:50]
    #           | 2 |
    #           +-+-+
    #             |
    #             |[50:60]
    #             |
    #           +-+-+
    #           | 1 |
    #           +---+

    contact_plan = ContactPlan(1000, 0)

    # Add contacts
    contact_plan.add_contact('node1', 'node2', 50, 60)
    contact_plan.add_contact('node2', 'node3', 10, 20)
    contact_plan.add_contact('node2', 'node4', 40, 50)
    contact_plan.add_contact('node3', 'node5', 20, 30)
    contact_plan.add_contact('node4', 'node5', 70, 80)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    # Now generate a route list for possible routes from node1 to node4
    route_list_node15 = mod.load_route_list(contact_graph, 'node1', 'node5', 0)

    # Make sure that two routes were found
    assert len(route_list_node15) == 0


@pytest.mark.parametrize("mod", testdata)
def test_load_route_list_anchoring_first_contact(mod):
    """Test function that tests the route-finding capabilities, in particular
    the correct behaviour when the anchoring mechanism is involved and the
    limiting contact is the first contact of the route.
    """
    # First, create an contact plan that is then converted to the contact graph
    # representation and later processed by load_route_list

    # The following topology is tested in this test case:
    #           +---+
    #           | 5 |
    # [0:100]+--+---+--+[0:100]
    #        |         |
    #      +-+-+     +-+-+
    #      | 3 |     | 4 |
    #      +-+-+     +-+-+
    #        |         |
    # [0:100]+--+---+--+[0:100]
    #           | 2 |
    #           +-+-+
    #             |
    #             |[30:70]
    #             |
    #           +-+-+
    #           | 1 |
    #           +---+

    contact_plan = ContactPlan(1000, 0)

    # Add contacts
    contact_plan.add_contact('node1', 'node2', 30, 70)
    contact_plan.add_contact('node2', 'node3', 0, 100)
    contact_plan.add_contact('node2', 'node4', 0, 100)
    contact_plan.add_contact('node3', 'node5', 0, 100)
    contact_plan.add_contact('node4', 'node5', 0, 100)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    # Now generate a route list for possible routes from node1 to node4
    route_list_node15 = mod.load_route_list(contact_graph, 'node1', 'node5', 0)

    # Make sure that only route is found (as both possible routes run through
    # the identical first limiting contact and thus only one route suffices)
    assert len(route_list_node15) == 1

    # Check that the route is correct
    route = route_list_node15[0]
    assert route[0] == [('node1', 'node2', 30, 70, 1000, 0),
                        ('node2', 'node3', 0, 100, 1000, 0),
                        ('node3', 'node5', 0, 100, 1000, 0)] \
           or route[0] == [('node1', 'node2', 30, 70, 1000, 0),
                           ('node2', 'node4', 0, 100, 1000, 0),
                           ('node4', 'node5', 0, 100, 1000, 0)]

    assert route.edt == 30
    assert route.capacity == 40000
    assert route.to_time == 70


@pytest.mark.parametrize("mod", testdata)
def test_load_route_list_anchoring_intermediate_contact(mod):
    """Test function that tests the route-finding capabilities, in particular
    the correct behaviour when the anchoring mechanism is involved and the
    limiting contact is the first contact of the route.
    """

    # First, create an contact plan that is then converted to the contact graph
    # representation and later processed by load_route_list

    # The following topology is tested in this test case:
    #           +---+
    #           | 8 |
    # [0:100]+--+---+--+[30:90]
    #        |         |
    #      +-+-+     +-+-+
    #      | 6 |     | 7 |
    #      +-+-+     +-+-+
    #        |         |
    # [0:100]+--+---+--+[30:90]
    #           | 5 |
    #           +-+-+
    #             |
    #             |[30:70]
    #             |
    #           +-+-+
    #           | 4 |
    # [30:90]+--+---+--+[0:100]
    #        |         |
    #      +-+-+     +-+-+
    #      | 2 |     | 3 |
    #      +-+-+     +-+-+
    #        |         |
    # [30:90]+--+---+--+[0:100]
    #           | 1 |
    #           +---+

    contact_plan = ContactPlan(1000, 0)

    # Add contacts
    contact_plan.add_contact('node1', 'node2', 30, 90)
    contact_plan.add_contact('node1', 'node3', 0, 100)
    contact_plan.add_contact('node2', 'node4', 30, 90)
    contact_plan.add_contact('node3', 'node4', 0, 100)
    contact_plan.add_contact('node4', 'node5', 30, 70)
    contact_plan.add_contact('node5', 'node6', 0, 100)
    contact_plan.add_contact('node5', 'node7', 30, 90)
    contact_plan.add_contact('node6', 'node8', 0, 100)
    contact_plan.add_contact('node7', 'node8', 30, 90)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    # Now generate a route list for possible routes from node1 to node4
    route_list_node18 = mod.load_route_list(contact_graph, 'node1', 'node8', 0)

    # Make sure that only route is found (as both possible routes run through
    # the identical intermediate limiting contact and thus only one route is
    # returned)
    assert len(route_list_node18) == 1

    # Check that the route is correct
    route = route_list_node18[0]

    assert route.edt == 30
    assert route.capacity == 40000
    assert route.to_time == 70


def generate_test_graph(remove_edge26=False):
    """Helper function to generate a contact graph for many testcases."""

    # The following topology is tested in this test case:
    #           +---+
    #           | 8 |
    # [0:100]+--+---+--+[30:90]
    #        |         |
    #      +-+-+     +-+-+
    #      | 6 |     | 7 |
    #      +-+-+     +-+-+
    #        |         |
    #        |         |
    # [10:40]|         |[40:80]
    #        |         |
    #        |         |
    #      +-+-+     +-+-+
    #      | 2 |     | 3 |
    #      +-+-+     +-+-+
    #        |         |
    # [30:90]+--+---+--+[0:100]
    #           | 1 |
    #           +---+

    contact_plan = ContactPlan(1000, 0)
    # Create list of all nodes
    contact_plan.add_contact('node1', 'node2', 30, 90)
    contact_plan.add_contact('node1', 'node3', 0, 100)
    contact_plan.add_contact('node3', 'node7', 40, 80)
    contact_plan.add_contact('node6', 'node8', 0, 100)
    contact_plan.add_contact('node7', 'node8', 30, 90)

    # Only add edge between node2 and node6 if required
    if not remove_edge26:
        contact_plan.add_contact('node2', 'node6', 10, 40)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    return contact_graph


@pytest.mark.parametrize("mod", testdata)
def test_proximate_nodes_base(mod):
    """Test function that tests the identify_proximate_node_list."""

    # First, create an contact plan that is then converted to the contact graph
    # representation and later processed by identify_proximate_node_list

    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Route bundle from node1 to node 8 with size 1 and no deadline
    bundle = Packet('node1', 'node8', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 1000, 0)] = Contact(
        30, 90, 1000, 'node1', 'node2')

    contact_list[('node1', 'node3', 0, 100, 1000, 0)] = Contact(
        0, 100, 1000, 'node1', 'node3')

    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1')

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] \
        .register_simulator(dummy)

    # Now generate a proximate node list
    proximate_nodes = mod.identify_proximate_node_list(
        'node1', bundle, contact_graph, route_list, [], 0, contact_list)

    # Make sure that two routes are found
    assert len(proximate_nodes) == 2

    # Check individual EDT and hops
    node1 = proximate_nodes[0]
    assert node1.route.edt == 30
    assert node1.route.hops == 3

    node2 = proximate_nodes[1]
    assert node2.route.edt == 40
    assert node2.route.hops == 3


@pytest.mark.parametrize("mod", testdata)
def test_proximate_nodes_past_route(mod):
    """Test function that verifys that identify_proximate_node_list() ignores
    routes thats' feasibility ended in the past.
    """
    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Route bundle from node1 to node 8 with size 1 and no deadline
    bundle = Packet('node1', 'node8', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 1000, 0)] = Contact(
        30, 90, 1000, 'node1', 'node2')

    contact_list[('node1', 'node3', 0, 100, 1000, 0)] = Contact(
        0, 100, 1000, 'node1', 'node3')

    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1')

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] \
        .register_simulator(dummy)

    # Now generate a proximate node list with current time set to 50
    proximate_nodes = mod.identify_proximate_node_list(
        'node1', bundle, contact_graph, route_list, [], 50, contact_list)

    # Make sure that only one route is found, (1->2->6->8) has already expired
    # at t=50
    assert len(proximate_nodes) == 1

    # Assert that the correct proximate node (and route) is returned
    assert proximate_nodes[0].route.transmission_plan == ([('node1', 'node3',
                                                            0, 100, 1000, 0),
                                                           ('node3', 'node7',
                                                            40, 80, 1000, 0),
                                                           ('node7', 'node8',
                                                            30, 90, 1000, 0)])
    assert proximate_nodes[0].contact == (('node1', 'node3', 0, 100, 1000, 0))


@pytest.mark.parametrize("mod", testdata)
def test_proximate_nodes_edt_after_deadline(mod):
    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Route bundle from node1 to node 8 with size 1 and deadline set to 35
    bundle = Packet('node1', 'node8', 1, 35)

    # Route bundle from node1 to node 8 with size 1 and deadline set to 30
    bundle2 = Packet('node1', 'node8', 1, 30)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 1000, 0)] = Contact(
        30, 90, 1000, 'node1', 'node2')

    contact_list[('node1', 'node3', 0, 100, 1000, 0)] = Contact(
        0, 100, 1000, 'node1', 'node3')

    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1')

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] \
        .register_simulator(dummy)

    # Now generate a proximate node list with current time set to 0
    proximate_nodes = mod.identify_proximate_node_list(
        'node1', bundle, contact_graph, route_list, [], 0, contact_list)

    # Make sure that only one route is found, (1->3->7->8) will not reach the
    # target within the deadline
    assert len(proximate_nodes) == 1

    # Assert that the correct proximate node (and route) is returned
    assert proximate_nodes[0].route.transmission_plan == ([('node1', 'node2',
                                                            30, 90, 1000, 0),
                                                           ('node2', 'node6',
                                                            10, 40, 1000, 0),
                                                           ('node6', 'node8',
                                                            0, 100, 1000, 0)])
    assert proximate_nodes[0].contact == (('node1', 'node2', 30, 90, 1000, 0))

    # Now generate a proximate node list with current time set to 0
    proximate_nodes2 = mod.identify_proximate_node_list(
        'node1', bundle2, contact_graph, route_list, [], 0, contact_list)

    # Make sure that only one route is found, (1->3->7->8) will not reach the
    # target within the deadline
    assert not proximate_nodes2


@pytest.mark.parametrize("mod", testdata)
def test_proximate_nodes_route_capacity(mod):
    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Create bundle from node1 to node 8 with size 40 and deadline set to
    # infinity
    bundle = Packet('node1', 'node8', 40000, math.inf)

    # Create bundle from node1 to node 8 with size 41 and deadline set to
    # infinity
    bundle2 = Packet('node1', 'node8', 41000, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 1000, 0)] = Contact(
        30, 90, 1000, 'node1', 'node2')

    contact_list[('node1', 'node3', 0, 100, 1000, 0)] = Contact(
        0, 100, 1000, 'node1', 'node3')

    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1')

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] \
        .register_simulator(dummy)

    # Now generate a proximate node list for 'bundle'
    proximate_nodes = mod.identify_proximate_node_list(
        'node1', bundle, contact_graph, route_list, [], 0, contact_list)

    # Make sure that routes are found as the bundle is not exceeding the
    # capacities of the routes' contacts
    assert len(proximate_nodes) == 1

    # Now generate a proximate node list for 'bundle2'
    proximate_nodes = mod.identify_proximate_node_list(
        'node1', bundle2, contact_graph, route_list, [], 0, contact_list)

    # Make sure that routes are not found as the bundle's size is larger than
    # the capacities of all available routes
    assert len(proximate_nodes) == 0

    # Enqueue that packet to trigger the capacity recalculation
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].cap_rem = 10000

    # Enqueue that packet to trigger the capacity recalculation
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].cap_rem = 40000

    # Now generate a proximate node list for 'bundle'
    proximate_nodes = cgr_basic.identify_proximate_node_list(
        'node1', bundle, contact_graph, route_list, [], 0, contact_list)

    # Make sure that one route is found as the bundle is still fitting into
    # the queue of the 1->3 contact
    assert len(proximate_nodes) == 1

    assert proximate_nodes[0].route.transmission_plan == ([('node1', 'node3',
                                                            0, 100, 1000, 0),
                                                           ('node3', 'node7',
                                                            40, 80, 1000, 0),
                                                           ('node7', 'node8',
                                                            30, 90, 1000, 0)])

    assert proximate_nodes[0].contact == ('node1', 'node3', 0, 100, 1000, 0)

    # Now generate a proximate node list for 'bundle2'
    proximate_nodes = cgr_basic.identify_proximate_node_list(
        'node1', bundle2, contact_graph, route_list, [], 0, contact_list)

    # Make sure that routes are not found as the bundle's size is larger than
    # the remaining capacities of all feasible contacts to neighbors
    assert not proximate_nodes


@pytest.mark.parametrize("mod", testdata)
def test_proximate_nodes_excluded_nodes(mod):
    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Route bundle from node1 to node 8 with size 1 and deadline set to
    # infinity
    bundle = Packet('node1', 'node8', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 1000, 0)] = Contact(
        30, 90, 1000, 'node1', 'node2')

    contact_list[('node1', 'node3', 0, 100, 1000, 0)] = Contact(
        0, 100, 1000, 'node1', 'node3')

    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1')

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, math.inf, 0)] \
        .register_simulator(dummy)

    # Now generate a proximate node list with ('node1', 'node2', 30, 90) being
    # in the excluded node list
    proximate_nodes = mod.identify_proximate_node_list(
        'node1', bundle, contact_graph, route_list, ['node2'], 0, contact_list)

    # Make sure that only one route is found, (1->3->7->8) will not reach the
    # target within the deadline
    assert len(proximate_nodes) == 1

    assert proximate_nodes[0].route.transmission_plan == ([('node1', 'node3',
                                                            0, 100, 1000, 0),
                                                           ('node3', 'node7',
                                                            40, 80, 1000, 0),
                                                           ('node7', 'node8',
                                                            30, 90, 1000, 0)])

    assert proximate_nodes[0].contact == ('node1', 'node3', 0, 100, 1000, 0)


def create_route(old_route):
    plan = list()
    for contact in old_route[0]:
        plan.append(
            ContactIdentifier(
                from_node=contact[0],
                to_node=contact[1],
                from_time=contact[2],
                to_time=contact[3],
                datarate=contact[4],
                delay=contact[5]))

    new_route = Route(
        transmission_plan=plan,
        edt=old_route[1][0],
        capacity=old_route[1][1],
        to_time=old_route[1][2],
        hops=len(old_route[0]),
        next_hop=plan[0])
    return new_route


@pytest.mark.parametrize("mod", testdata)
def test_proximate_nodes_optimize_proximate_node(mod):
    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Route bundle from node1 to node 8 with size 1 and deadline set to
    # infinity
    bundle = Packet('node1', 'node8', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create some fake routes that can later be used for optimizing the
    # proximate node values
    route_list['node8'] = []

    # First, add route with worse EDT (50)
    route_list['node8'].append(
        create_route(([('node1', 'node3', 0, 100, 10, 0),
                       ('node3', 'node4', 0, 100, 10, 0),
                       ('node4', 'node5', 30, 70, 10, 0)], (50, 40, 70))))
    # Then add route with better EDT (30)
    route_list['node8'].append(
        create_route(([('node1', 'node3', 0, 100, 10, 0),
                       ('node3', 'node4', 0, 100, 10, 0),
                       ('node4', 'node5', 30, 70, 10, 0)], (30, 40, 70))))

    # First, add route with 5 hops
    route_list['node8'].append(
        create_route(([('node1', 'node2', 30, 90, 10, 0),
                       ('node3', 'node4', 0, 100, 10, 0),
                       ('node3', 'node4', 0, 100, 10, 0),
                       ('node3', 'node4', 0, 100, 10, 0),
                       ('node4', 'node5', 30, 70, 10, 0)], (30, 40, 70))))

    # Then add route with only 4 hops
    route_list['node8'].append(
        create_route(([('node1', 'node2', 30, 90, 10, 0),
                       ('node3', 'node4', 0, 100, 10, 0),
                       ('node3', 'node4', 0, 100, 10, 0),
                       ('node4', 'node5', 30, 70, 10, 0)], (30, 40, 70))))

    # Create contact list object
    contact_list = dict()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 10, 0)] = Contact(
        30, 90, 10, 'node1', 'node2')

    contact_list[('node1', 'node3', 0, 100, 10, 0)] = Contact(
        0, 100, 10, 'node1', 'node3')

    contact_list[('node1', 'node1', 0, math.inf, 10, 0)] = Contact(
        0, math.inf, 10, 'node1', 'node1')

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 10, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 10, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, 10,
                  0)].register_simulator(dummy)

    # Now generate a proximate node list with ('node1', 'node2', 30, 90) being
    # in the excluded node list
    proximate_nodes = mod.identify_proximate_node_list(
        'node1', bundle, contact_graph, route_list, [], 0, contact_list)

    # Make sure that two feasible proximate nodes are found
    assert len(proximate_nodes) == 2

    # Assert that the proximate nodes are returned with the correct, optimized
    # characteristics
    assert proximate_nodes[0].contact == ('node1', 'node3', 0, 100, 10, 0)
    assert proximate_nodes[0].route.edt == 30
    assert proximate_nodes[0].route.hops == 3
    assert proximate_nodes[0].route.transmission_plan == ([('node1', 'node3',
                                                            0, 100, 10, 0),
                                                           ('node3', 'node4',
                                                            0, 100, 10, 0),
                                                           ('node4', 'node5',
                                                            30, 70, 10, 0)])

    assert proximate_nodes[1].contact == ('node1', 'node2', 30, 90, 10, 0)
    assert proximate_nodes[1].route.edt == 30
    assert proximate_nodes[1].route.hops == 4
    assert proximate_nodes[1].route.transmission_plan == ([
        ('node1', 'node2', 30, 90, 10, 0), ('node3', 'node4', 0, 100, 10, 0),
        ('node3', 'node4', 0, 100, 10, 0), ('node4', 'node5', 30, 70, 10, 0)
    ])


# Test function that tests the cgr function
@pytest.mark.parametrize("mod", testdata_routing)
def test_cgr_base(mod):
    # First, create an contact plan that is then converted to the contact
    # graph representation and later processed by cgr()

    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Route bundle from node1 to node 8 with size 1 and no deadline
    bundle = Packet('node1', 'node8', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create limbo list
    limbo = list()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 1000, 0)] = Contact(
        30, 90, 1000, 'node1', 'node2', debug=True)

    contact_list[('node1', 'node3', 0, 100, 1000, 0)] = Contact(
        0, 100, 1000, 'node1', 'node3', debug=True)

    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1', debug=True)

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] \
        .register_simulator(dummy)

    # Now run cgr for the bundle (with current time set to 0)
    mod.cgr(bundle, 'node1', contact_graph, route_list, contact_list, 0, limbo)

    # Make sure that the bundle is enqueue for the correct contact
    assert len(contact_list[('node1', 'node2', 30, 90, 1000, 0)] \
        .packet_queue) == 1
    assert len(contact_list[('node1', 'node3', 0, 100, 1000, 0)] \
        .packet_queue) == 0
    assert len(contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] \
        .packet_queue) == 0

    assert contact_list[('node1', 'node2', 30, 90, 1000, 0)] \
                        .packet_queue[0] == bundle


# Test function that tests the cgr function
@pytest.mark.parametrize("mod", testdata_routing)
def test_cgr_base_no_route(mod):
    # First, create an contact plan that is then converted to the contact
    # graph representation and later processed by cgr()

    # The following topology is tested in this test case:
    #    +---+         +---+         +---+         +---+
    #    | 1 +---------+ 2 +---------+ 3 +---------+ 4 |
    #    +---+  35:40  +---+  20:40  +---+  20:25  +---+

    contact_plan = ContactPlan(1000, 0)

    contact_plan.add_contact('node1', 'node2', 35, 40)
    contact_plan.add_contact('node2', 'node3', 20, 40)
    contact_plan.add_contact('node3', 'node4', 20, 25)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    # Route bundle from node1 to node 8 with size 1 and no deadline
    bundle = Packet('node1', 'node4', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create limbo list
    limbo = list()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 35, 40, 1000, 0)] = Contact(
        35, 40, 1000, 'node1', 'node2', debug=True)
    contact_list[('node2', 'node3', 20, 40, 1000, 0)] = Contact(
        20, 40, 1000, 'node2', 'node3', debug=True)
    contact_list[('node3', 'node4', 20, 25, 1000, 0)] = Contact(
        20, 25, 1000, 'node3', 'node4', debug=True)
    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1', debug=True)

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 35, 40, 1000, 0)].register_simulator(dummy)
    contact_list[('node2', 'node3', 20, 40, 1000, 0)].register_simulator(dummy)
    contact_list[('node3', 'node4', 20, 25, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] \
        .register_simulator(dummy)

    # Now run cgr for the bundle (with current time set to 0)
    mod.cgr(bundle, 'node1', contact_graph, route_list, contact_list, 0, limbo)

    # Make sure that the bundle is enqueue for the correct contact
    assert len(limbo) == 1
    assert len(contact_list[('node1', 'node2', 35, 40, 1000, 0)] \
        .packet_queue) == 0
    assert len(contact_list[('node2', 'node3', 20, 40, 1000, 0)] \
        .packet_queue) == 0
    assert len(contact_list[('node3', 'node4', 20, 25, 1000, 0)] \
        .packet_queue) == 0
    assert len(contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] \
        .packet_queue) == 0


def generate_neighbors(old_neigbors):
    new_neighbors = list()

    for neighbor in old_neigbors:
        tp = list()
        for hops in neighbor[3]:
            tp.append(
                ContactIdentifier(
                    from_node=hops[0],
                    to_node=hops[1],
                    from_time=hops[2],
                    to_time=hops[3],
                    datarate=hops[4],
                    delay=hops[5]))
        route = Route(
            transmission_plan=tp,
            edt=neighbor[1],
            capacity=1000,
            to_time=10000,
            hops=neighbor[2],
            next_hop=ContactIdentifier(*neighbor[0]))
        new_neighbor = Neighbor(
            contact=route.next_hop,
            node_id=route.next_hop.to_node,
            route=route)
        new_neighbors.append(new_neighbor)

    return new_neighbors


@pytest.mark.parametrize("mod", testdata)
def test_cgr_optimization(mod):
    # Route bundle from node1 to node 8 with size 1 and no deadline
    bundle = Packet('node1', 'node8', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create limbo list
    limbo = list()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 10, 100, 1000, 0)] = Contact(
        10, 100, 1000, 'node1', 'node2', debug=True)

    contact_list[('node1', 'node3', 10, 100, 1000, 0)] = Contact(
        20, 100, 1000, 'node1', 'node3', debug=True)

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 10, 100, 1000, 0)] \
        .register_simulator(dummy)
    contact_list[('node1', 'node3', 10, 100, 1000, 0)] \
        .register_simulator(dummy)

    # Create a fake proximate node list to isolate the cgr() function's
    # behaviour and test it
    proximate_nodes = [(('node1', 'node2', 10, 100, 1000, 0), 10, 2,
                        [('node1', 'node2', 10, 100, 1000, 0)]),
                       (('node1', 'node3', 10, 100, 1000, 0), 20, 2,
                        [('node1', 'node3', 10, 100, 1000, 0)])]
    proximate_nodes = generate_neighbors(proximate_nodes)

    # Now run cgr for the bundle (with current time set to 0)
    mod.cgr(
        bundle,
        'node1',
        None,
        route_list,
        contact_list,
        0,
        limbo,
        proximate_nodes=proximate_nodes)

    # Reset bundle so it can be routed from the same node again without
    # throwing an exception
    bundle.current_node = 'inserted'

    # Make sure that the bundle is enqueued in the queue with the best edt
    assert len(contact_list[('node1', 'node2', 10, 100, 1000, 0)] \
        .packet_queue) == 1
    assert not contact_list[('node1', 'node3', 10, 100, 1000, 0)] \
        .packet_queue
    assert contact_list[('node1', 'node2', 10, 100, 1000, 0)] \
        .packet_queue[0] == bundle

    # Alter proximate node list so that edt is equal and hops is the relevant
    # value
    proximate_nodes = [(('node1', 'node2', 10, 100, 1000, 0), 20, 3,
                        [('node1', 'node2', 10, 100, 1000, 0)]),
                       (('node1', 'node3', 10, 100, 1000, 0), 20, 2,
                        [('node1', 'node3', 10, 100, 1000, 0)])]
    proximate_nodes = generate_neighbors(proximate_nodes)

    # Now run cgr for the bundle (with current time set to 0)
    mod.cgr(
        bundle,
        'node1',
        None,
        route_list,
        contact_list,
        0,
        limbo,
        proximate_nodes=proximate_nodes)

    # Reset bundle so it can be routed from the same node again without
    # throwing an exception
    bundle.current_node = 'inserted'

    # Make sure that the bundle is enqueued in the queue with the best edt
    assert len(contact_list[('node1', 'node2', 10, 100, 1000,
                             0)].packet_queue) == 1
    assert len(contact_list[('node1', 'node3', 10, 100, 1000,
                             0)].packet_queue) == 1
    assert contact_list[('node1', 'node3', 10, 100, 1000, 0)] \
        .packet_queue[0] == bundle

    # Alter proximate node list so that edt and hops are equal and hash is the
    # deciding value
    proximate_nodes = [(('node1', 'node2', 10, 100, 1000, 0), 20, 4,
                        [('node1', 'node2', 10, 100, 1000, 0)]),
                       (('node1', 'node3', 10, 100, 1000, 0), 20, 4,
                        [('node1', 'node3', 10, 100, 1000, 0)])]
    proximate_nodes = generate_neighbors(proximate_nodes)

    # Now run cgr for the bundle (with current time set to 0)
    mod.cgr(
        bundle,
        'node1',
        None,
        route_list,
        contact_list,
        0,
        limbo,
        proximate_nodes=proximate_nodes)

    # Reset bundle so it can be routed from the same node again without
    # throwing an exception
    bundle.current_node = 'inserted'

    if hash('node2') > hash('node3'):
        node_a = ('node1', 'node2', 10, 100, 1000, 0)
        node_b = ('node1', 'node3', 10, 100, 1000, 0)
    else:
        node_b = ('node1', 'node2', 10, 100, 1000, 0)
        node_a = ('node1', 'node3', 10, 100, 1000, 0)

    # Make sure that the bundle is enqueued in the queue with the best edt
    if len(contact_list[node_a].packet_queue) == 1:
        assert len(contact_list[node_b].packet_queue) == 2
        assert contact_list[node_b].packet_queue[1] == bundle
    elif len(contact_list[node_a].packet_queue) == 2:
        assert len(contact_list[node_b].packet_queue) == 1
        assert contact_list[node_a].packet_queue[1] == bundle


# Testcase function that verifies the insertion of bundles that are not
# routable at the moment of routing into the limbo list


@pytest.mark.parametrize("mod", testdata)
def test_cgr_limbo(mod):
    # Route bundle from node1 to node 8 with size 1 and no deadline
    bundle = Packet('node1', 'node8', 1, math.inf)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create limbo list
    limbo = list()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    # Create a fake proximate node list to isolate the cgr() function's
    # behaviour and test it, no entries this time to force in insertion into
    # limbo
    proximate_nodes = []

    # Now run cgr for the bundle (with current time set to 0)
    mod.cgr(
        bundle,
        'node1',
        None,
        route_list,
        contact_list,
        0,
        limbo,
        proximate_nodes=proximate_nodes)

    # Make sure that the bundle is enqueued in the queue with the best edt
    assert len(limbo) == 1
    assert limbo[0] == bundle


# Test function that verifies the "flooding" mechanism for critical
# bundles in the cgr() function


@pytest.mark.parametrize("mod", testdata_routing)
def test_cgr_critical_bundle(mod):
    # First, create an contact plan that is then converted to the contact graph
    # representation and later processed by identify_proximate_node_list

    # Create contact graph of test topology
    contact_graph = generate_test_graph()

    # Route bundle from node1 to node 8 with size 1 and no deadline, but with
    # being critical
    bundle = Packet('node1', 'node8', 1000, math.inf, False, True)

    # Create empty route_list dictionary so route list for destination will be
    # regenerated
    route_list = dict()

    # Create contact list object
    contact_list = dict()

    # Create limbo list
    limbo = list()

    # Create Simulation Environment (dummy, will not be run)
    env = QSim()

    contact_list[('node1', 'node2', 30, 90, 1000, 0)] = Contact(
        30, 90, 1000, 'node1', 'node2', debug=True)

    contact_list[('node1', 'node3', 0, 100, 1000, 0)] = Contact(
        0, 100, 1000, 'node1', 'node3', debug=True)

    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] = Contact(
        0, math.inf, 1000, 'node1', 'node1', debug=True)

    # Add dummy simulator to the contacts
    dummy = DummySimulator()
    contact_list[('node1', 'node2', 30, 90, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node3', 0, 100, 1000, 0)].register_simulator(dummy)
    contact_list[('node1', 'node1', 0, math.inf, 1000, 0)] \
        .register_simulator(dummy)

    mod.cgr(bundle, 'node1', contact_graph, route_list, contact_list, 0, limbo)

    # Make sure that the bundle is enqueued in all feasible contacts to
    # neighbors
    assert len(contact_list[('node1', 'node2', 30, 90, 1000,
                             0)].packet_queue) == 1
    assert len(contact_list[('node1', 'node3', 0, 100, 1000,
                             0)].packet_queue) == 1

    contact_graph2 = generate_test_graph(True)

    # Route bundle from node1 to node 8 with size 1 and no deadline, but with
    # being critical
    bundle2 = Packet('node1', 'node8', 1, math.inf, False, True)

    # Reset route list
    route_list = dict()

    mod.cgr(bundle2, 'node1', contact_graph2, route_list, contact_list, 0,
            limbo)

    # Make sure that only neighbors are considered that can reach the
    # destination (based on the contact graph knowledge)
    assert len(contact_list[('node1', 'node2', 30, 90, 1000,
                             0)].packet_queue) == 1
    assert len(contact_list[('node1', 'node3', 0, 100, 1000,
                             0)].packet_queue) == 2
