"""Verify that the routing implementations are deterministic."""

import argparse
from multiprocessing import Pool
from io import StringIO
import sys

from pydtnsim import Simulator, ContactPlan, ContactGraph, Contact
from pydtnsim.nodes import SimpleCGRNode
from pydtnsim.monitors import BaseMonitor
from pydtnsim.packet_generators import BatchPacketGenerator

import pydtnsim.routing.scgr as scgr
import pydtnsim.routing.cgr_anchor as cgr_anchor
import pydtnsim.routing.cgr_basic as cgr_basic


class ReceptionMonitor(BaseMonitor):
    """ Monitor implementation that records successfully delivered packets.

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
    generator = BatchPacketGenerator(1000, 10000, source_list,
                                     destination_list, [10000])
    simulator.register_generator(generator)

    # Run the simulation
    simulator.run_simulation(48000000)

    # Return the monitored results
    return monitor.packet_dict


def check_deterministic_behaviour(algorithm, quick):
    """ Run simulation scenario twice and compare results """
    output = StringIO()
    old_stdout = sys.stdout
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

    # Run the simulation two times and verify that the monitored results are
    # equalscgr.cgr
    print("RUN 1\n-----")
    packet_list_run1 = run_simulation(algorithm, source_list, destination_list)
    print("RUN 2\n-----")
    packet_list_run2 = run_simulation(algorithm, source_list, destination_list)

    # Just make sure that there is no implementation error and the two
    # dicts are the exact same object
    if packet_list_run1 is packet_list_run2:
        print("The two packet lists were the same object. Failure.")
        return (output.getvalue(), False)

    # Assert that both dicts contain the same keys
    if packet_list_run1.keys() != packet_list_run2.keys():
        print("The two packet lists did not contain the same keys. Failure.")
        return (output.getvalue(), False)

    # Due to the previous assertion we can only iterate over one key set
    for key in packet_list_run1:
        if packet_list_run1[key] != packet_list_run2[key]:
            print("For packet '{}' the route information differed. Failure.".
                  format(key))
            return (output.getvalue(), False)

    print("""-----\n-> Simulation outcomes of both simulation with '{}' as
     algorithm are equal!\n-----""".format(algorithm.__module__))

    return (output.getvalue(), True)


# Main function
def main(args):
    # Create pool based on processor core count.
    pool = Pool(None)
    results = list()

    # Generate multiprocessing async tasks in pool
    results.append(
        pool.apply_async(check_deterministic_behaviour,
                         (scgr.cgr, args.quick)))
    results.append(
        pool.apply_async(check_deterministic_behaviour,
                         (cgr_anchor.cgr, args.quick)))
    results.append(
        pool.apply_async(check_deterministic_behaviour,
                         (cgr_basic.cgr, args.quick)))

    # Print multiprocessing outputs in correct order and return with
    # return code based on outcomes of multiprocessing
    return_value = None
    for result in results:
        (output, code) = result.get()
        print(output)
        if not code:
            return_value = 1

    sys.exit(return_value)


parser = argparse.ArgumentParser(
    description="pydtnsim routing determinism check")
parser.add_argument(
    "-q",
    "--quick",
    action='store_true',
    help="Run reduced check complexity. Helpful for quick " + "verifications.")

if __name__ == "__main__":
    main(parser.parse_args())
