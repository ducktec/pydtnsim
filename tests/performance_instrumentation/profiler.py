"""Profiling tool using cProfile."""

import argparse
import cProfile
import json
import sys

from pydtnsim import Simulator, ContactPlan, ContactGraph, Contact
from pydtnsim.nodes import SimpleCGRNode
from pydtnsim.monitors import BaseMonitor
from pydtnsim.packet_generators import ContinuousPacketGenerator

import pydtnsim.routing.scgr as scgr
import pydtnsim.routing.cgr_anchor as cgr_anchor
import pydtnsim.routing.cgr_basic as cgr_basic


class ReceptionMonitor(BaseMonitor):
    """ Monitor implementation to record successfully delivered packets.

    Whenever a packet is reaching it's destination, the monitor creates an
    entry for that packet in a dict containing the route, the dt and the
    initially calculated route characteristics.

    """

    def __init__(self, env):
        """Instantiate a MonitorNotifier object.

        Args:
            env (env): The simulation env where the monitor will be
                used in.

        """
        # Call parent class init method
        super(ReceptionMonitor, self).__init__(env)
        self.packet_dict = dict()

    def packet_destination_reached(self, packet, node):
        """Packet reached it's destination node.

        Args:
            packet (Packet): The `Packet` object that reached it's destination.
            node (Node): The destination `Node` object.

        Raises:
            ValueError: If a packet should be monitored (i.e. added to the
                packet dict) that has no identifier.

        """
        if packet.identifier is None:
            raise ValueError("Monitoring unidentifiable packet! Failed!")
        self.packet_dict[packet.identifier] = (packet.hops, self.env.now,
                                               packet.planned_characteristics)


def run_simulation(algorithm):
    """Performs a simulation with a certain algorithm."""

    # Create simulation environment
    simulator = Simulator()

    # Generate contact plan from provided json file
    contact_plan = ContactPlan(1, 100, "tests/resources/tvg_gs10_hs2_it1.json")

    # Open the file and load it using the JSON module
    with open("tests/resources/tvg_gs10_hs2_it1.json") as file:
        tvg = json.load(file)

    hotspots = tvg["hotspots"]

    # Generate cold spot list
    coldspots = list()
    for node in contact_plan.get_nodes():
        if node not in hotspots and node[:2] == "gs":
            coldspots.append(node)

    print('hotspots: {}'.format(hotspots))
    print('coldspots: {}'.format(coldspots))

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
        SimpleCGRNode(planned_node, contact_dict, algorithm, contact_graph,
                      simulator)

    # Generate packet generator(s) and register them
    generator1 = ContinuousPacketGenerator(
        1,  # Create 1Kbps per node
        100000,  # Packet Size: 100KB
        coldspots,  # group 1
        [hotspots[0]],  # group 2
        0,  # Start Time
        86400000)  # End Time

    # Generate packet generator(s) and register them
    generator2 = ContinuousPacketGenerator(
        1,  # Create 1Kbps per node
        100000,  # Packet Size: 100KB
        [hotspots[0]],  # group 2
        coldspots,  # group 1
        0,  # Start time
        86400000)  # End time
    # Register the generators as a generator object in the simulation
    # environment
    simulator.register_generator(generator1)
    simulator.register_generator(generator2)

    # Run the simulation
    simulator.run_simulation(172800000, disable_tdqm=False)

    if algorithm is scgr.cgr:
        hits = 0
        miss = 0
        for node in simulator.node_dict.values():
            for route in node.route_list.values():
                hits += route.avg_rdt.window_hit
                miss += route.avg_rdt.window_miss

        print("\n Window Approach:")
        if (hits + miss) > 0:
            print("- hit: {}\n- miss: {}\n- percent: {}".format(
                hits, miss, hits / (hits + miss)))
        else:
            print("- hit: {}\n- miss: {}\n- percent: -".format(hits, miss))


class Profiler():
    def __init__(self, algo):
        self.algo = algo

    def run_instrumentation(self):
        run_simulation(self.algo)


# Main function
def main(args):
    approaches = [('scgr', scgr.cgr), ('cgr_basic', cgr_basic.cgr),
                  ('cgr_anchor', cgr_anchor.cgr)]

    if not args.dump:
        print("No saving the cProfile dumps!")

    for approach in approaches:
        print("Started {}".format(approach[0]))
        prof = Profiler(approach[1])
        pr = cProfile.Profile()
        pr.runctx('prof.run_instrumentation()', globals(), locals())
        pr.print_stats()
        if args.dump:
            pr.dump_stats('{}.cprof'.format(approach[0]))
            print("Saving dump at \'{}.cprof\'".format(approach[0]))
        print("Finished {}".format(approach[0]))

    sys.exit(0)


parser = argparse.ArgumentParser(
    description="pydtnsim routing determinism check")
parser.add_argument(
    "-n",
    "--dump",
    action='store_true',
    help="Save the profiling dumps in the execution folder.")
if __name__ == "__main__":
    main(parser.parse_args())
