"""Data Generator that continuously generates packets with a certain rate.

The Data Generator is invoked by the Simulation Manager with specific data
generation information and is adding itself to the simulation
environment.

Packets are always given an unique identifier.

During a simulation run, it is injecting packets (i.e. handing them to nodes)
according to the provided configuration.
"""

import math
from pydtnsim import Packet
from .base_packet_generator import BasePacketGenerator


class ContinuousPacketGenerator(BasePacketGenerator):
    """Packet Generatior injecting packets with a given data rate.

    Args:
        generation_rate (int): Bits per ms that should be generated.
        packet_size (int): Size of the packets that are created and injected.
        source_node_list (list): List of source nodes where packets should be
            the generator.
        target_node_list (list): List of target nodes that should be adressed
            from all source nodes in `source_node_list`.
        start_time (int): Time when the generator should start generating
            packets (in ms).
        end_time (int): Time when the generator should stop generating
            packets (in ms).

    """

    def __init__(self, generation_rate, packet_size, source_node_list,
                 target_node_list, start_time, end_time):
        # Call parent class init method
        super(ContinuousPacketGenerator, self).__init__()
        self.generation_rate = generation_rate
        self.packet_size = packet_size
        self.source_node_list = source_node_list
        self.target_node_list = target_node_list
        self.simulator = None
        self.start_time = start_time
        self.end_time = end_time
        self.source = None
        self.dest = None
        self.timeout = self.packet_size / self.generation_rate

    def run(self):
        """Start the simulation by registering event."""
        self.simulator.env.register_event(self.start_time + self.timeout,
                                          self.rid, self.insert_next_packages)

        # Retrieve the source node objects from the simulator environment
        self.source = self.simulator.get_node_dict(self.source_node_list)
        self.dest = self.simulator.get_node_dict(self.target_node_list)

    def insert_next_packages(self):
        """Simulate the insertion of package.

        Adds new event if end of generatio period has not been reached yet.

        """
        for source_node in self.source.values():
            for target_node in self.dest.values():
                # Create packet from source to destination node
                # that has an unique identifier
                packet = Packet(
                    source_node.identifier,
                    target_node.identifier,
                    self.packet_size,
                    math.inf,
                    is_critical=False,
                    return_to_sender=False,
                    identifier=self.simulator.get_unique_packet_identifier())
                self.packet_count += 1
                source_node.inject_packet(packet, self.simulator.env.now)

        if self.simulator.env.now + self.timeout < self.end_time:
            self.simulator.env.register_event(
                self.simulator.env.now + self.timeout, self.rid,
                self.insert_next_packages)
