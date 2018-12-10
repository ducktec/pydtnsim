"""Data Generator that creates and injects a number of packets at a given time.

The Data Generator is invoked by the Simulation Manager with the number of
required packets, the desired packet size and the injection time.

At the given time in the simulation period, it is injecting the packets all
at once.
"""

import math
from pydtnsim import Packet
from .base_packet_generator import BasePacketGenerator


class BatchPacketGenerator(BasePacketGenerator):
    """Packet Generatior injecting a number of packets all at once.

    Args:
        packet_number (int): Number of packets that should be injected.
        packet_size (int): Size of the packets that are created and injected.
        source_node_list (list): List of source nodes where packets should be
            inserted by the generator. Items are the string identifiers of the
            nodes.
        target_node_list (list): List of target nodes that should be adressed
            from all source nodes in `source_node_list`. Items are the string
            identifiers of the nodes.
        time (list): List of discrete points in time where batch insertion
            should take place. Can be multiple times, at each time the number
            of packets will be inserte for all source nodes to all target
            nodes.
    """

    def __init__(self, packet_number, packet_size, source_node_list,
                 target_node_list, time):
        # Call parent class init method
        super(BatchPacketGenerator, self).__init__()
        self.packet_number = packet_number
        self.packet_size = packet_size
        self.source_node_list = source_node_list
        self.target_node_list = target_node_list
        self.time = time
        self.simulator = None
        self.source = None
        self.dest = None

    def run(self):
        """Start the simulation by registering event."""
        # Retrieve the source node objects from the simulator environment
        self.source = self.simulator.get_node_dict(self.source_node_list)
        self.dest = self.simulator.get_node_dict(self.target_node_list)

        # Sort the injection times by ascending time
        self.time = sorted(self.time, key=int)

        # Register an event for the first point in time where the number
        # of packets should be injected.
        next_time = self.time.pop(0)
        self.simulator.env.register_event(next_time, self.rid,
                                          self.insert_next_packages)

    def insert_next_packages(self):
        """Simulate the insertion of package.

        Adds new event if end of generatio period has not been reached yet.

        """
        for source_node in self.source.values():
            for target_node in self.dest.values():
                for _ in range(int(self.packet_number)):
                    # Create packet from source to destination node
                    # that has an unique identifier
                    packet = Packet(
                        source_node.identifier,
                        target_node.identifier,
                        self.packet_size,
                        math.inf,
                        is_critical=False,
                        return_to_sender=False,
                        identifier=self.simulator.
                        get_unique_packet_identifier())
                    source_node.inject_packet(packet, self.simulator.env.now)
                    self.packet_count += 1

        # If other injection times exist in the time list, register an event
        # for the next injection time
        if self.time:
            next_time = self.time.pop(0)
            self.simulator.env.register_event(next_time, self.rid,
                                              self.insert_next_packages)
