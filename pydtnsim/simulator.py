"""Implements the Simulator object used for running simulations."""

from collections import OrderedDict
from enum import Enum
from tqdm import tqdm
from pydtnsim.monitors import MonitorNotifier
from pydtnsim.backend import QSim


class Output(Enum):
    """Enum to specify the output of the simulatin run."""

    NO_OUTPUT = 0
    TQDM = 1
    TEXTUAL = 2


class Simulator():
    """Simulator object used for running simulations.

    Attributes:
        env (simulation env): Simulation environment (backend).
        notifier (MonitorNotifier): Notifier object for relaying events to
            monitors.
        node_dict (dict): Dict of registered nodes (identifier is key).
        contact_dict (set): Dict of registered contact objects (characteristic
            values are key)

    """

    def __init__(self):
        """Initialize simulator object.

        Creates environment and MonitorNotifier

        """
        self.env = QSim()
        self.notifier = MonitorNotifier(self.env)
        self.node_dict = OrderedDict()
        self.contact_dict = OrderedDict()
        self.generator_list = list()
        self.packet_counter = -1
        self.overall_capacity = 0
        self.capacity_dict = dict()
        self.final_capacity_dict = dict()

    def run_simulation(self,
                       duration,
                       starttime=0,
                       output=Output.NO_OUTPUT,
                       tqdm_position=0,
                       tqdm_desc=None,
                       name=""):
        """Run the simulation using the simulation backend.

        Args:
            duration (int): Simulation duration in milliseconds.
            starttime (int): Time in seconds from which on the simulation will
                run for the also provided duration. Required if TVG imports use
                a certain epoch.Defaults to 0.

                .. note::

                    It is recommended to fix the TVG import values instead of
                    setting a custom start time! It has to be considered, that
                    this custom start time has to be used for generator
                    configuration as well.

            output (Output): Specify if and how the progress of the simulation
                should be presented to the user. Defaults to no output.
            tqdm_position (int): Determine row position of tqdm progress bar.
                Helpful when multiple scenarios are simulated in parallel.
                Defaults to 0.
            tqdm_desc (string): Descriptor of the tqdm progress bar. Defaults
                to None.
            name (string): Descriptor of the simulation. Is used in print
                output. Defaults to "".

        """
        # Calculate the overall available capacity
        for contact in self.contact_dict:
            capacity = self.contact_dict[contact].capacity
            self.overall_capacity += capacity
            self.capacity_dict[contact] = capacity

        print(f"Running simulation {name} for {duration} ms ...")
        # Signal to monitors that simulation started
        self.notifier.simulation_started()

        starttime_ms = starttime * 1000

        # Determine the simulation steps (we use a 1% of the overall
        # simulation time to speed up the run)
        steps = round(duration / 100)
        steps_pbar = int(round(steps / 1000))

        # Disable tdqm if not desired
        if output == Output.TQDM:

            # Create a custom tqdm progress bar object that displays the
            # progress in seconds rather than milliseconds.
            pbar = tqdm(
                total=int(round(duration / 1000)),
                position=tqdm_position,
                desc=tqdm_desc)

            # Run the simulation
            for i in range(0, duration, steps):
                self.env.run_simulation(until=starttime_ms + i + steps)
                pbar.update(steps_pbar)

            # Close the progress bar (ensures correct output)
            pbar.close()
        elif output == Output.TEXTUAL:
            # Determine the simulation steps (we use a 1% of the overall
            # simulation time to speed up the run)
            steps = round(duration / 100)

            # Run the simulation
            for i in range(0, duration, steps):
                self.env.run_simulation(until=starttime_ms + i + steps)
                print(f"Simulation {name} at {(i/steps)}%")

        else:
            self.env.run_simulation(until=duration)

        # Signal to monitors that simulation ended
        self.notifier.simulation_ended()
        self.__print_stats()

    def register_node(self, node):
        """Register node in simulation environment.

        Args:
            node (Node): The registered node.

        Raises:
            ValueError: When a node with the same identifier already exists
                in the environment.

        """
        # Check if node already added to simulation or node with same
        # identifier already exists
        if node.identifier in self.node_dict:
            raise ValueError("Node with name '{}' already exists in "
                             "environment".format(node.identifier))
        # Append to node set
        self.node_dict[node.identifier] = node

    def register_contact(self, contact):
        """Register contact in simulation environment.

        Adds the contact as generator to the simulation environment.

        Args:
            contact (Contact): The registered contact.

        """
        # Add contact to contact set, multiple contacts with the same
        # characteristics are allowed, one cannot add the same contact
        # object multiple times (enforced by set)
        self.contact_dict[contact.get_identifier()] = contact
        # Register the contact as generator object with the simulation
        # environment
        contact.register_simulator(self)

    def register_generator(self, generator):
        """Add packet generator to the simulation environment.

        Args:
            generator (object): The packet generator that should be added
                to the simulation environment.
        """
        # Add the generator object to the list of generators. We use a list
        # here because one can potentially add the same generator object to
        # an simulation environment multiple times.
        self.generator_list.append(generator)
        generator.register_simulator(self)

    def register_monitor(self, monitor):
        """Add monitor to the simulation environment.

        Args:
            monitor (object): The monitor that should be added to the
                simulation environment.

        """
        self.notifier.add_subscriber(monitor)

    def __print_stats(self):
        """Print very basic informations about the simulation to stdout."""
        print("Simulation Results:")
        # Sum up the total number of generated packets
        total_packet_count = 0
        for generator in self.generator_list:
            total_packet_count += generator.get_packet_count()
        print("- total number of packets generated: {:d}".format(
            total_packet_count))

        packets_in_limbo = 0
        for node in self.node_dict.values():
            if node.limbo:
                packets_in_limbo += len(node.limbo)
        print("- total number of packets enqueued in limbos: {:d}".format(
            packets_in_limbo))

        packets_in_contacts = 0
        for contact in self.contact_dict.values():
            packets_in_contacts += contact.len_packet_queue
        print("- total number of packets enqueued in contacts: {:d}".format(
            packets_in_contacts))

        remaining_capacity = 0
        for contact in self.contact_dict:
            local_rem_cap = self.contact_dict[contact].capacity
            remaining_capacity += local_rem_cap
            self.final_capacity_dict[contact] = local_rem_cap

        capacity_utilization = round(
            (((self.overall_capacity - remaining_capacity) /
              self.overall_capacity) * 100), 2)
        print("- contact capacity utilization: {} %".format(
            capacity_utilization))

    def get_utilization_list(self,
                             ignore_inter_hotspot_contact=False,
                             hotspots=None):
        """Generate a list of the utilizations of all contacts.

        Returns:
            list: A list of the utilizations of every individual contact.

        Raises:
            ValueError: If inter hotspot contacts should be excluded, but no
                hot spot list is provided.

        """
        if ignore_inter_hotspot_contact and hotspots is None:
            raise ValueError("Ignoring Hotspot Contacts, but no hotspot list "
                             + "provided!")

        utilization_list = list()
        for contact in self.contact_dict:
            if (ignore_inter_hotspot_contact and contact[0] in hotspots
                    and contact[1] in hotspots):
                continue

            utilization = round((((self.capacity_dict[contact] -
                                   self.final_capacity_dict[contact]) /
                                  self.capacity_dict[contact]) * 100), 2)
            utilization_list.append(utilization)
        return utilization_list

    def get_stats(self):
        """Return very basic informations about the simulation."""
        # Sum up the total number of generated packets
        total_packet_count = 0
        for generator in self.generator_list:
            total_packet_count += generator.get_packet_count()

        packets_in_limbo = 0
        for node in self.node_dict.values():
            if node.limbo:
                packets_in_limbo += len(node.limbo)

        packets_in_contacts = 0
        for contact in self.contact_dict.values():
            packets_in_contacts += contact.len_packet_queue

        return (total_packet_count, packets_in_limbo, packets_in_contacts)

    def hand_over_packet(self, peer, packet):
        """Hand over transmitted packet to peer node.

        Args:
            peer (string): Description of parameter `peer`.
            packet (pydtnsim.Packet): Transmitted packet.

        Raises:
            ValueError: If the packet was forwarded to a node that does not
             exist!

        """
        # Check if peer node does exist
        if peer not in self.node_dict:
            raise ValueError("Packet was forwarded to node '{}' that does not "
                             "exist".format(peer))
        # Perform routing operation at peer node
        self.node_dict[peer].route_packet(packet, self.env.now)

    def get_contact_dict(self, contact_list):
        """Return dict that maps contact identifiers to contact objects.

        Args:
            contact_list (list): List of contacts (in string format) for which
             a dict mapping the string to the Contact object will be provided.

        Raises:
            ValueError: If one of the contact identifiers in the list does not
             exist as contact object.

        Returns:
            dict: A dict mapping the string identifier of a contact to the
             corresponding Contact object.

        """
        list_contact_dict = OrderedDict()
        # Iterate over all contacts in contact_list
        for contact in contact_list:
            # Check if contact exists in contact_dict, otherwise raise error
            if contact not in self.contact_dict:
                raise ValueError(
                    "Contact '{}' listed in the contact "
                    "list does not exist as a contact object".format(
                        contact.get_identifier()))
            # Add contact object to subdict
            list_contact_dict[contact] = self.contact_dict[contact]

        # Return subdict
        return list_contact_dict

    def get_unique_packet_identifier(self):
        """Return an packet identifier (int) that is unique in the scenario."""
        self.packet_counter += 1
        return self.packet_counter

    def get_node_dict(self, node_list):
        """Return dict that maps node identifiers to node objects.

        Args:
            node_list (list): List of nodes (in string identifer format) for
             which a dict mapping the string to the Contact object will be
             provided.

        Raises:
            ValueError: If one of the node identifiers in the list does not
             exist as contact object.

        Returns:
            dict: A dict mapping the string identifier of a node to the
             corresponding Node object.

        """
        list_node_dict = OrderedDict()
        # Iterate over all contacts in contact_list
        for node in node_list:
            # Check if contact exists in contact_dict, otherwise raise error
            if node not in self.node_dict:
                raise ValueError("Node '{}' listed in the node list does not "
                                 "exist as a contact object".format(node))
            # Add node object to subdict
            list_node_dict[node] = self.node_dict[node]

        # Return subdict
        return list_node_dict
