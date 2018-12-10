"""Verify that the CGR implementations yield the same routing decisions."""

import argparse
from multiprocessing import Pool
from io import StringIO
from collections import OrderedDict
import sys

from pydtnsim import Simulator, ContactPlan, ContactGraph, Contact
from pydtnsim.nodes import SimpleCGRNode
from pydtnsim.monitors import BaseMonitor
from pydtnsim.packet_generators import BatchPacketGenerator

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
        self.packet_dict = OrderedDict()

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


def run_simulation(algorithm, source_list, destination_list):
    """Performs a simulation with a certain algorithm."""

    # Create simulation environment
    simulator = Simulator()

    # Generate contact plan from provided json file
    contact_plan = ContactPlan(1, 100, "tests/resources/tvg_g10_s10.json")

    # Convert contact plan to contact graph
    contact_graph = ContactGraph(contact_plan)

    # Create monitoring instance
    monitor = ReceptionMonitor(simulator.env)
    simulator.register_monitor(monitor)

    # Generate contact objects and register them
    for planned_contact in contact_plan.get_contacts():
        contact = Contact(planned_contact.from_time, planned_contact.to_time,
                          planned_contact.datarate, planned_contact.from_node,
                          planned_contact.to_node, planned_contact.delay)
        simulator.register_contact(contact)

    # Generate node objects and register them
    for planned_node in contact_plan.get_nodes():
        contact_list = contact_plan.get_outbound_contacts_of_node(planned_node)
        contact_dict = simulator.get_contact_dict(contact_list)
        SimpleCGRNode(planned_node, contact_dict, algorithm, contact_graph,
                      simulator, [])

    # Generate packet generator(s) and register them
    generator = BatchPacketGenerator(200, 10000, source_list, destination_list,
                                     [10.0])
    simulator.register_generator(generator)

    # Run the simulation
    simulator.run_simulation(48000000)

    # Return the monitored results
    return monitor.packet_dict


def generate_packet_routing_list(algorithm, quick):
    """Run simulation scenario and return generated packet information."""
    output = StringIO()
    sys.stdout = output

    # Assign source and destination nodes
    if quick:
        source_list = ['gs175']
        destination_list = ['gs109']
    else:
        source_list = ['gs175', 'gs18']
        destination_list = ['gs109', 'gs188']

    print("----------------\nTest Run for {}\n---------------".format(
        algorithm.__module__))

    # Run the simulation
    packet_dict = run_simulation(algorithm, source_list, destination_list)

    return (output.getvalue(), packet_dict)


# Main function
def main(args):
    # Create pool based on processor core count.
    pool = Pool(None)
    results = list()

    # Generate multiprocessing async tasks in pool
    results.append(
        pool.apply_async(generate_packet_routing_list, (scgr.cgr, args.quick)))
    results.append(
        pool.apply_async(generate_packet_routing_list,
                         (cgr_basic.cgr, args.quick)))
    results.append(
        pool.apply_async(generate_packet_routing_list,
                         (cgr_anchor.cgr, args.quick)))

    # Print multiprocessing outputs in correct order and return with
    # return code based on outcomes of multiprocessing
    return_value = None
    packet_dict_list = list()
    for result in results:
        (output, packet_dict) = result.get()
        print(output)
        packet_dict_list.append(packet_dict)

    if len(packet_dict_list[0]) != len(packet_dict_list[1]) or \
       len(packet_dict_list[0]) != len(packet_dict_list[2]):
        print("Number of packets in dicts are differing! Abort")
        sys.exit(1)

    # Take the first dict as a reference and check if the routes/details in
    # CGR_BASIC dict differs
    for packet in packet_dict_list[0].keys():
        if packet_dict_list[0][packet] != packet_dict_list[1][packet]:
            print("Route characteristics differing for {}".format(packet))
            print("- SCGR:   {}".format(packet_dict_list[0][packet]))
            print("- CGR_BS: {}".format(packet_dict_list[1][packet]))
            print("- CGR_AN: {}".format(packet_dict_list[2][packet]))

    # Calculate average real edt for all three approaches
    approaches = ['SCGR', 'CGR_basic', 'CGR_anchor']
    avg_edt_list = list()
    approach_counter = 0
    for packet_dict in packet_dict_list:
        avg_edt = 0
        # Add up the edt of all packets
        for packet in packet_dict:
            avg_edt += packet_dict[packet][1]
        # Get mean by dividing through number of packets
        avg_edt = avg_edt / len(packet_dict)
        avg_edt_list.append(avg_edt)
        print("Mean EDT for {}: {}".format(approaches[approach_counter],
                                           avg_edt))
        approach_counter += 1

    if avg_edt_list[0] == avg_edt_list[1]:
        print("\nThe avg edt for SCGR and CGR_BASIC match!" +
              " Equivalence for these two approaches can be assumed!\n")
        sys.exit(0)
    else:
        print("\nThe avg edt for SCGR and CGR_BASIC do not match!" +
              " Equivalence for these two approaches CANNOT be assumed!\n")
        sys.exit(1)


parser = argparse.ArgumentParser(
    description="pydtnsim routing determinism check")
parser.add_argument(
    "-q",
    "--quick",
    action='store_true',
    help="Run reduced check complexity. Helpful for quick " + "verifications.")

if __name__ == "__main__":
    main(parser.parse_args())
