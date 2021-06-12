from pydtnsim import Simulator
from pydtnsim import ContactPlan, ContactGraph, Contact
from pydtnsim.nodes import SimpleCGRNode
from pydtnsim.routing import cgr_basic
from pydtnsim.packet_generators import ContinuousPacketGenerator

def main():
    """Simulate basic scenario."""
    # Create simulation environment
    simulator = Simulator()
    
    # Generate empty contact plan
    contact_plan = ContactPlan(10, 50)

    # Add the contacts
    contact_plan.add_contact('node_a', 'node_b', 0, 100000)
    contact_plan.add_contact('node_a', 'node_b', 500000, 750000)
    contact_plan.add_contact('node_b', 'node_c', 0, 200000)
    contact_plan.add_contact('node_b', 'node_c', 350000, 400000)
    contact_plan.add_contact('node_b', 'node_c', 950000, 990000)
    
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
        
    # Generate network node objects and register them
    for planned_node in contact_plan.get_nodes():
        # Generate contact list of node
        contact_list = contact_plan.get_outbound_contacts_of_node(planned_node)
        # Create a dict that maps the contact identifiers to Contact simulation
        # objects
        contact_dict = simulator.get_contact_dict(contact_list)
        # Create a node simulation object
        SimpleCGRNode(planned_node, contact_dict, cgr_basic.cgr, contact_graph,
                      simulator, [])
                      
    # Generate packet generator 1 and register them
    generator1 = ContinuousPacketGenerator(
        10,          # Data Generation Rate: 10 Bytes per ms
        100000,      # Packet Size: 100 KB
        ['node_a'],  # From 'node_a'
        ['node_c'],  # To 'node_c'
        0,           # Start injection at simulation time 0s
        1000000)     # End injection at simulation end (1000s)

    # Generate packet generator 2 and register them
    generator2 = ContinuousPacketGenerator(
        10,          # Data Generation Rate: 10 Bytes per ms
        100000,      # Packet Size: 100 KB
        ['node_c'],  # From 'node_c'
        ['node_a'],  # To 'node_a'
        0,           # Start injection at simulation time 0s
        1000000)     # End injection at simulation end (1000s)

    # Register the generators as a generator objects in the simulation
    # environment
    simulator.register_generator(generator1)
    simulator.register_generator(generator2)

    # Run the simulation for 1000 seconds (1000000 ms)
    simulator.run_simulation(1000000)

if __name__ == "__main__":
    main()
