"""Contact Implementation (Generator functionality).

This module contains implementations of DTN contacts. So far, only a basic node
implementation has been provided. There might be more implementations later.
"""


class Contact:
    """Contact object implementation (Generator functionality).

    The contact object is functioning as a generator and is run during
    the simulation. While active, the contact forwards packets to the
    communication peer and triggers the routing process on that peer after a
    complete simulated transaction.

    Args:
        start_time (int): Contact start time in ms.
        end_time (int): Contact end time in ms.
        data_rate (int): Contact data rate in bits/ms.
        source (string): Source node identifier of the contact.
        peer (Node): Destination node identifier of the contact.
        delay (int): Propagation delay in ms. Defaults to 0.
        debug (bool): If set to true, generate a real packet queue. Defaults
            to False.

    """

    def __init__(self,
                 start_time,
                 end_time,
                 data_rate,
                 source,
                 peer,
                 delay=0,
                 debug=False):
        self.start_time = start_time
        self.end_time = end_time
        self.data_rate = data_rate
        self.source = source
        self.next_enqueue_time = start_time
        self.len_packet_queue = 0
        self.simulator = None
        self.peer = peer
        self.delay = delay

        self.rid = 0
        # Initialize the contact's capacity to the maximum available
        # capacity
        self.capacity = (end_time - start_time) * data_rate

        # Only create a real packet queue, if we need it for testing
        # and debugging purposes
        self.debug = debug
        if self.debug:
            self.packet_queue = list()

    def enqueue_packet(self, packet, booked_route, best_route):
        """Enqueue a certain packet for the contact.

        Args:
            packet (Packet): The packet to be enqueued.
            booked_route (Route): The route that the packet was booked on.
            best_route (Route): The route that would have been selected if
                no other packets where affecting the forwarding procedure
                of this packet.

        Raises:
            OverflowError: If packet is enqueued that does not fit into
                the contact anymore.

        """
        # Only signal rerouting/nominal routing if sensible (i.e. route
        # available and sound)
        if booked_route is None:
            self.simulator.notifier.node_no_route_found_for_packet(
                self.source, packet)

        if not self.is_capacity_sufficient(packet):
            # Signal to monitors that no route was found, packet will be
            # dropped
            self.simulator.notifier.node_no_route_found_for_packet(
                packet, self.source)
            return

        packet.add_hop(booked_route.transmission_plan[0].from_node)

        # Add packet to the packet queue (simulated by increasing the
        # len value)
        self.len_packet_queue += 1

        # Keep track of the consumed contact capacity (for utilization
        # metrics)
        self.capacity -= packet.size

        # Only add packet to packet queue if we need it for debugging/
        # testing purposes
        if self.debug:
            self.packet_queue.append(packet)

        # Update the next_enqueue_time for this contact
        if self.simulator.env.now <= self.next_enqueue_time:
            transmission_start_time = self.next_enqueue_time
            self.next_enqueue_time += (packet.size / self.data_rate)
        else:
            transmission_start_time = self.simulator.env.now
            self.next_enqueue_time = self.simulator.env.now + \
                (packet.size / self.data_rate)
        if self.next_enqueue_time > self.end_time:
            raise OverflowError("Packet was enqueued that is exceeding the "
                                "contacts capacity!")

        # Register an event that is triggered when the packet will have been
        # fully transmitted to the next hop
        self.simulator.env.register_event(self.next_enqueue_time, self.rid,
                                          self.hand_over_packet, packet)

        # Notify montiors about routing
        self.simulator.notifier.packet_routed(packet, self.source,
                                              booked_route, best_route,
                                              transmission_start_time)

    def register_simulator(self, simulator):
        """Register the contact with the simulator environment.

        Args:
            simulator (Simulator): The simulator environment that the contact
                should be simulated in

        """
        self.simulator = simulator
        self.rid = self.simulator.env.register_runner(self.run)

    def hand_over_packet(self, packet):
        """Hand over packet to the next hop (i.e. peer).

        Args:
            packet (Packet): The packet that should be handed over to
                the peer.

        """
        # Signal successful transmission to monitors
        self.simulator.notifier.packet_transmitted(packet, self.peer)
        # Hand packet to the next node
        self.simulator.hand_over_packet(self.peer, packet)
        # Reduce the packet queue counter
        self.len_packet_queue -= 1
        # Only remove packet from packet queue if we need it for debugging/
        # testing purposes
        if self.debug:
            self.packet_queue.pop(0)

    def run(self):
        """Execute contact object.

        Registers the start event of the contact

        """
        self.simulator.env.register_event(self.start_time, self.rid,
                                          self.contact_started)

    def contact_started(self):
        """Signal contact start.

        Notifies the monitors and registers contact end event.
        """
        # Signal contact has started to monitors
        self.simulator.notifier.contact_started(self.source, self)
        self.simulator.env.register_event(self.end_time, self.rid,
                                          self.contact_ended)

    def contact_ended(self):
        """Signal contact end.

        Notifies the monitors.
        """
        # Signal contact has ended to monitors
        self.simulator.notifier.contact_ended(self.source, self)

    def is_capacity_sufficient(self, packet):
        """Check if capacity remaining is sufficient to schedule packet.

        Args:
            packet (Packet): The packet for which the feasibility of scheduling
                to that contact should be checked.

        Returns:
            bool: True if capacity sufficient, False otherwise

        """
        # Check if the capacity of the contact is sufficient to house the
        # additional packet
        if self.simulator.env.now <= self.next_enqueue_time:
            # We are using the floor division here and are also adding one
            # ms to the value to have a conservative estimation.
            # This approach reduces the computational effort of this
            # often-called function and at most creates an imprecision of 1
            # ms. However, it also ensures that if a contact is selected, the
            # packet will fit, also when the values are properly rounded.
            temp_next_enqueue_time = self.next_enqueue_time + \
                (packet.size // self.data_rate) + 1
        else:
            # We are using the floor division here and are also adding one
            # ms to the value to have a conservative estimation.
            # This approach reduces the computational effort of this
            # often-called function and at most creates an imprecision of 1
            # ms. However, it also ensures that if a contact is selected, the
            # packet will fit, also when the values are properly rounded.
            temp_next_enqueue_time = self.simulator.env.now + \
                (packet.size // self.data_rate) + 1

        if temp_next_enqueue_time <= self.end_time:
            return True

        return False

    def get_identifier(self):
        """Return identifier of contact.

        Returns:
            tuple: Identifier of the contact in the form of
            ``(<source_id>, <destination_id>, <start_time>, <end_time>,
            <data_rate>)``

        """
        return (self.source, self.peer, self.start_time, self.end_time,
                self.data_rate, self.delay)

    # Rich comparison helper methods
    def __lt__(self, other):
        """Start time is before the start time of the other contact."""
        return self.start_time < other.start_time

    def __le__(self, other):
        """Start time is before or equal start time of the other contact."""
        return self.start_time <= other.start_time

    def __eq__(self, other):
        """Start times are equal."""
        return self.start_time == other.start_time

    def __ne__(self, other):
        """Start times are not equal."""
        return self.start_time != other.start_time

    def __ge__(self, other):
        """Start time is after the start time of the other contact."""
        return self.start_time >= other.start_time

    def __gt__(self, other):
        """Start time is after or equal the start time of the other contact."""
        return self.start_time > other.start_time
