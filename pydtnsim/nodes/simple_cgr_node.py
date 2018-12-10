"""Module containing node implementations.

This module contains implementations (and helper functions) of dtn nodes. So
far, only a basic node implementation has been provided. There might be more
implementations later.
"""

from collections import OrderedDict


class SimpleCGRNode:
    """Node Implementation for a node using CGR routing and no service classes.

    The Node object represents the core of the simulated environment. It
    simulates the behaviour of a real-world DTN node. The node object is
    operating on datastructures that are provided by the Simulation Manager.

    Args:
        identifier (string): The identifier of the node.
        contact_dict (dict): A dict of all contacts originating from the node.
        routing_algorithm (func): The routing algorithm used for making routing
            decisions within the node.
        topology (dict): The topology information in the form of the contact
            graph.
        simulator (pydtnsim.Simulator): The simulator environment where this
            node is simulated.
        hot_spots (list): The list of hot spots active in the simulated
            scenario.
    """

    def __init__(self, identifier, contact_dict, routing_algorithm, topology,
                 simulator, hot_spots):
        self.identifier = identifier
        self.contact_dict = contact_dict
        self.routing_algorithm = routing_algorithm
        self.topology = topology
        self.route_list = OrderedDict()
        self.limbo = list()
        self.simulator = simulator
        self.hot_spots = hot_spots
        simulator.register_node(self)

    def route_packet(self, packet, time):
        """Determine next hop based on routing algorithm.

        Assigns a received packet to an available (and not overbooked) contact.

        """
        # Set packet completed and add to completed list when packet
        # destination is own identifier
        if self.identifier == packet.end_node:
            # Signal completion
            packet.set_completed(self.identifier)
            self.simulator.notifier.packet_destination_reached(
                packet, self.identifier)
            return

        self.routing_algorithm(packet, self.identifier, self.topology,
                               self.route_list, self.contact_dict, time,
                               self.limbo, self.hot_spots)

    def inject_packet(self, packet, time):
        """Perform initial routing operation and signal injection.

        Assigns the injected packet to an available (and not overbooked)
        contact.

        """
        # Signal injection to monitors
        self.simulator.notifier.packet_injected(packet, self.identifier)
        self.route_packet(packet, time)

    def is_connected_to(self, node_identifier):
        """Check if node is directly connected to another node.

        Helpful for determining if node is hot spot in ring road scenario.

        Args:
            node_identifier (string): Node that should be checked for direct
             contact.

        Returns:
            bool: True if directly connected, false otherwise.

        """
        # Iterate over contacts and check if node_identifier is a peer
        # in one of them
        for (_, peer, _, _, _) in self.contact_dict:
            if peer == node_identifier:
                return True

        return False
