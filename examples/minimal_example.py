"""Minimal Simulation Example."""

from pydtnsim import Simulator, ContactPlan, ContactGraph, Contact
from pydtnsim.nodes import SimpleCGRNode
from pydtnsim.packet_generators import BatchPacketGenerator

from pydtnsim.routing import cgr_basic


def main():
    """Simulate basic scenario."""
    # Create simulation environment
    simulator = Simulator()

    # Generate empy contact plan
    contact_plan = ContactPlan(1, 50)

    # Add a single contact from node_a to node_b from 0s to 10s to the plan
    contact_plan.add_contact('node_a', 'node_b', 0, 10000)

    # Convert contact plan to contact graph
    contact_graph = ContactGraph(contact_plan)

    # Generate contact objects and register them
    for planned_contact in contact_plan.get_contacts():
        # Create a Contact simulation object based on the ContactPlan
        # information
        contact = Contact(planned_contact.from_time, planned_contact.to_time,
                          planned_contact.datarate, planned_contact.from_node,
                          planned_contact.to_node, planned_contact.delay)
        # Register the contact as a generator object in the simulation
        # environment
        simulator.register_contact(contact)

    # Generate node objects and register them
    for planned_node in contact_plan.get_nodes():
        # Generate contact list of node
        contact_list = contact_plan.get_outbound_contacts_of_node(planned_node)
        # Create a dict that maps the contact identifiers to Contact simulation
        # objects
        contact_dict = simulator.get_contact_dict(contact_list)
        # Create a node simulation object
        SimpleCGRNode(planned_node, contact_dict, cgr_basic.cgr, contact_graph,
                      simulator, [])

    # Generate packet generator(s) and register them
    generator = BatchPacketGenerator(
        1,  # Create one packet
        1000,  # Packet Size: 1000 Bytes
        ['node_a'],  # From 'node_a'
        ['node_b'],  # To 'node_b'
        [0])  # At simulation time 0s
    # Register the generator as a generator object in the simulation
    # environment
    simulator.register_generator(generator)

    # Run the simulation for 20 seconds (20000 ms)
    simulator.run_simulation(20000)


if __name__ == "__main__":
    main()
