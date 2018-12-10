"""Implements the (empty) monitor baseclass.

Can be inherited by other monitor classes to only implement the monitoring
hooks that are relevant for a particular monitoring scenario.
"""


class BaseMonitor:
    """Monitor baseclass.

    Does not actually monitor anything but is a template for monitoring
    child classes.

    Args:
        env (env): The simulator env where the monitor will be used in.
    """

    def __init__(self, env):
        # Save the reference to the env of this monitor
        self.env = env

    def packet_routed(self, packet, node, booked_route, best_route,
                      transmission_start_time):
        """Packet was routed.

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

    def packet_destination_reached(self, packet, node):
        """Packet reached it's destination node.

        Args:
            packet (Packet): The packet object that reached it's destination.
            node (String): The destination node identifier.

        """

    def packet_transmitted(self, packet, node):
        """Packet was successfully to a next hop (but not yet scheduled).

        Args:
            packet (Packet): The packet object that was transmitted.
            node (Node): The `Node` object that was reached.

        """

    def packet_injected(self, packet, node):
        """Packet was successfully injected (but not yet scheduled).

        Args:
            packet (Packet): The packet object that was injected.
            node (string): The identifier of the node where the packet was
                injected.
        """

    def node_contact_plan_changed(self, node, contact_plan):
        """Contact plan obect of a node has changed.

        Args:
            node (Node): The `Node` object that had it's contact plan changed.
            contact_plan (contact_plan): The destination `Node` object.

        """

    def node_no_route_found_for_packet(self, node, packet):
        """No route to the destination node could be found.

        Packet will be dropped.

        Args:
            node (Node): The `Node` object where no route could be found.
            packet (Packet): The packet object for which no route could be
                found.

        """

    def node_local_contact_depleted(self, node, contact, packet):
        """Contact to a neighbor node was full.

         A contact to a neighbor node was selected for forwarding, but was
         already full. An alternative contact had to be selected. Not relevant
         for CGR implementations .

        Args:
            node (Node): The `Node` object where no route could be found.
            packet (Packet): The packet object for which no route could be
                found.
            contact (Contact): The `Contact` object that had no sufficent
                capacity to house the packet object.

        """

    def contact_started(self, node, contact):
        """Contact became active.

        Args:
            node (Node): The originating `Node` object where a contact became
                active.
            contact (Contact): The `Contact` object that became active.

        """

    def contact_ended(self, node, contact):
        """Contact ended.

        Args:
            node (Node): The originating `Node` object where a contact ended.
            contact (Contact): The `Contact` object that ended.

        """

    def contact_suspended(self, node, contact):
        """Contact suspended.

        The queue of scheduled packets for the contact is depleted (i.e. all
        scheduled packets were transmitted) and the contact will suspend until
        the contact ends or a new packet is scheduled.

        Args:
            node (Node): The originating `Node` object where a contact was
             suspended.
            contact (Contact): The `Contact` object that was suspended.

        """

    def contact_reactivated(self, node, contact):
        """Contact continued.

        While the contact being suspended, a new packet was scheduled for the
        contact and the contact was therefore reactivated.

        Args:
            node (Node): The originating `Node` object where a contact was
                reactivated.
            contact (Contact): The `Contact` object that was reactivated.

        """

    def simulation_started(self):
        """Signal simulation start."""

    def simulation_ended(self):
        """Signal simulation termination."""
