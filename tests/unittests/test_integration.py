import math

from pydtnsim.routing import cgr_basic as cgr
from pydtnsim.backend import QSim
from pydtnsim import Packet, Contact, ContactGraph, ContactPlan
from queue import Queue


def test_verify_capacity_calculation_consistency():
    """Test function that verifies that the capacity calculations in CGR and the
    Contact object correspond to each other.
    """
    # The following topology is tested in this test case:
    #      +---+
    #      | 2 |
    #      +-+-+
    #        |
    # [30:90]|
    #        |
    #      +-+-+
    #      | 1 |
    #      +---+

    # Create contact plan and add single contact
    contact_plan = ContactPlan(1, 20)
    contact_plan.add_contact('node1', 'node2', 30000, 90000)

    # Generate contact graph representation
    contact_graph = ContactGraph(contact_plan)

    # Create Simulation Environment (dummy, simulation will not be
    # executed)
    env = QSim()

    # Create a Contact object that represents the one edge of the contact
    # graph and should have the same capacity value calculated as the CGR
    # functions
    contact = Contact(30000, 90000, 1, 'node1', 'node2', delay=20)

    # Now generate possible routes
    route_list_node12 = cgr.load_route_list(contact_graph, 'node1', 'node2', 0)

    # There should be only one possible route
    assert len(route_list_node12) == 1
    assert route_list_node12[0].edt == 30000
    assert route_list_node12[0].capacity == 60000
    assert route_list_node12[0].to_time == 90000
    assert route_list_node12[0].transmission_plan == ([('node1', 'node2',
                                                        30000, 90000, 1, 20)])

    # Verify that the capacities that were calculated are equal (as no packet
    # has been enqueue yet, the capacity value can be checked)
    assert contact.capacity == route_list_node12[0].capacity
