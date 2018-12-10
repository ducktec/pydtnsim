"""Module containing the Packet implementation."""
import math


class Packet:
    """Implementation of an object representing a packet in the DTN scenario.

    The Packet object represents a packet that is injected into the network
    at a source node and then forwarded through the network to the destination
    node. The Packet object holds various characteristics of the packet like
    the overall size, but does not actually carry any payload data.

    Args:
        source_node (string): Source node of the packet.
        end_node (string): Destination node of the packet.
        size (int): Overall Packet Size in bits.
        deadline (int): Deadline of the packet in ms.
        return_to_sender (bool): Whether returning the packet to the
            direct sender during transmission is allowed. Defaults to False.
        is_critical (bool): Whether the packet is critical.
        identifier (string): Identifier of the packet. Defaults to None.
    """

    def __init__(self,
                 source_node,
                 end_node,
                 size,
                 deadline=math.inf,
                 return_to_sender=False,
                 is_critical=False,
                 identifier=None):
        self.source_node = source_node
        self.end_node = end_node
        # in Bits, includes everything (payload, protocol overhead etc.)
        self.size = size
        self.hops = list()
        self.deadline = deadline
        self.return_to_sender = return_to_sender
        self.is_critical = is_critical
        self.planned_routes = list()
        self.alternative_routes = list()
        self.on_initial_route = True
        self.planned_characteristics = None
        self.identifier = identifier

    def add_hop(self, hop):
        """Update packet when routed regularly.

        Args:
            hop (node): The next hop on the path to the destination.

        """
        # Add current hop to list
        self.hops.append(hop)

    def set_completed(self, node):
        """Set final hop of route.

        Args:
            node (string): Final hop of packet route.

        """
        # Add destination node to route
        self.hops.append(node)

    def add_planned_route(self, route):
        """Add route information calculated during routing to list of routes.

        Args:
            route (Route): Calculated route.

        """
        self.planned_routes.append(route)

    def add_alternative_route(self, route):
        """Add route information calculated during routing to list of routes.

        Args:
            route (Route): Calculated alternative route.

        """
        self.alternative_routes.append(route)

    # Rich comparison helper methods
    def __lt__(self, other):
        """Check if id is smaller than the id of the other packet."""
        return self.identifier < other.identifier

    def __le__(self, other):
        """Check if id is <= id of the other packet."""
        return self.identifier <= other.identifier

    def __eq__(self, other):
        """Check if id are equal."""
        return self.identifier == other.identifier

    def __ne__(self, other):
        """Check if id are not equal."""
        return self.identifier != other.identifier

    def __ge__(self, other):
        """Check if id is greater than the id of the other packet."""
        return self.identifier >= other.identifier

    def __gt__(self, other):
        """Check if id is >= the id of the other packet."""
        return self.identifier > other.identifier
