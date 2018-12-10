"""Implements MonitorNotifier that notifies Monitors about events."""

from .base_monitor import BaseMonitor


class MonitorNotifier(BaseMonitor):
    """Object to handle notification of subscribed monitoring objects.

    Args:
        env (env): The env where the monitor will be used in.

    """

    def __init__(self, env):
        # Call parent class init method
        super(MonitorNotifier, self).__init__(env)
        self.subscribers = []

    def add_subscriber(self, subscriber):
        """Register monitor with this MonitorNotifier.

        Args:
            subscriber (BaseMonitor): The subscribed monitor object. Must be
                an object supporting the :class:`BaseMonitor` interface.

        """
        # Append the subscriber to the list of subscribers
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

    def remove_subscriber(self, subscriber):
        """Unregister monitor with this MonitorNotifier.

        Args:
            subscriber (BaseMonitor): The subscribed monitor object. Must be
                an object supporting the :class:`BaseMonitor` interface.

        """
        try:
            self.subscribers.remove(subscriber)
        # Silenty ignore of the subscriber was not registered
        except ValueError:
            pass

    def packet_routed(self, packet, node, booked_route, best_route,
                      transmission_start_time):
        """Notify subscribers that packet was routed.

        Args:
            packet (Packet): The packet object that was routed.
            node (string): The node identifier where the packet was routed.
            booked_route (Route): The route that the packet was booked on.
            best_route (Route): The route that would have been selected if
                no other packets where affecting the forwarding procedure
                of this packet.
            transmission_start_time (float): The time when the packet will
                be actually starting transfer to another node. Might be
                different than the contact's start time

        """
        for subscriber in self.subscribers:
            subscriber.packet_routed(packet, node, booked_route, best_route,
                                     transmission_start_time)

    def packet_destination_reached(self, packet, node):
        """Notify subscribers that Packet reached it's destination node.

        Args:
            packet (Packet): The `Packet` object that reached it's destination.
            node (Node): The destination `Node` object.

        """
        for subscriber in self.subscribers:
            subscriber.packet_destination_reached(packet, node)

    def packet_transmitted(self, packet, node):
        """Notify subscribers that Packet was transmitted to next hop.

        Args:
            packet (Packet): The `Packet` object that was transmitted.
            node (Node): The `Node` object that was reached.

        """
        for subscriber in self.subscribers:
            subscriber.packet_transmitted(packet, node)

    def packet_injected(self, packet, node):
        """Notify subscribers that Packet was injected.

        Args:
            packet (Packet): The `Packet` object that was injected.
            node (Node): The `Node` object where the packet was injected.

        """
        for subscriber in self.subscribers:
            subscriber.packet_injected(packet, node)

    def node_contact_plan_changed(self, node, contact_plan):
        """Notify subscribers that the contact plan object of a node changed.

        Args:
            node (Node): The `Node` object that had it's contact plan changed.
            contact_plan (contact_plan): The destination `Node` object.

        """
        for subscriber in self.subscribers:
            subscriber.node_contact_plan_changed(node, contact_plan)

    def node_no_route_found_for_packet(self, node, packet):
        """Notify subscribers that no route could be found.

        Packet will be dropped.

        Args:
            node (Node): The `Node` object where no route could be found.
            packet (Packet): The `Packet` object for which no route could be
                found.

        """
        for subscriber in self.subscribers:
            subscriber.node_no_route_found_for_packet(node, packet)

    def node_local_contact_depleted(self, node, contact, packet):
        """Notify subscribers that contact to a neighbor node was full.

         A contact to a neighbor node was selected for forwarding, but was
         already full. An alternative contact had to be selected. Not relevant
         for CGR implementations .

        Args:
            node (Node): The `Node` object where no route could be found.
            packet (Packet): The `Packet` object for which no route could be
                found.
            contact (Contact): The `Contact` object that had no sufficent
                capacity to house the `Packet` object.

        """
        for subscriber in self.subscribers:
            subscriber.node_local_contact_depleted(node, contact, packet)

    def contact_started(self, node, contact):
        """Notify subscribers that contact became active.

        Args:
            node (Node): The originating `Node` object where a contact became
                active.
            contact (Contact): The `Contact` object that became active.

        """
        for subscriber in self.subscribers:
            subscriber.contact_started(node, contact)

    def contact_ended(self, node, contact):
        """Notify subscribers that contact ended.

        Args:
            node (Node): The originating `Node` object where a contact ended.
            contact (Contact): The `Contact` object that ended.

        """
        for subscriber in self.subscribers:
            subscriber.contact_ended(node, contact)

    def contact_suspended(self, node, contact):
        """Notify subscribers that contact was suspended.

        The queue of scheduled packets for the contact is depleted (i.e. all
        scheduled packets were transmitted) and the contact will suspend until
        the contact ends or a new packet is scheduled.

        Args:
            node (Node): The originating `Node` object where a contact was
                suspended.
            contact (Contact): The `Contact` object that was suspended.

        """
        for subscriber in self.subscribers:
            subscriber.contact_suspended(node, contact)

    def contact_reactivated(self, node, contact):
        """Notify subscribers that contact was continued.

        While the contact being suspended, a new packet was scheduled for the
        contact and the contact was therefore reactivated.

        Args:
            node (Node): The originating `Node` object where a contact was
                reactivated.
            contact (Contact): The `Contact` object that was reactivated.

        """
        for subscriber in self.subscribers:
            subscriber.contact_reactivated(node, contact)

    def simulation_started(self):
        """Notify subscribers that simulation started."""
        for subscriber in self.subscribers:
            subscriber.simulation_started()

    def simulation_ended(self):
        """Notify subscribers that simulation terminated."""
        for subscriber in self.subscribers:
            subscriber.simulation_ended()
