"""An experimental implementation of the Swift CGR (SCGR) routing algorithm.

This implementation makes use of the :mod:`dijkstra` python module that is
part of pydtnsim. While more performance-optimized dijkstra implementations
might exist, this implementation tries to balance readability and performance
by using the priority-queue approach and still maintaining well-structured and
easy to understand code.

This routing implementation currently has no overbooking handling implemented!

The module has one main routine:

CGR Forward Routine:
    This routine has to be executed on a per-bundle basis. :func:`cgr` is
    called with bundle-specific information and subsequently schedules the
    bundle for a contact in the future based on the routing decision (or
    adds the bundle to the limbo if no feasible route to the destination
    exists)
"""

import math
import copy
from collections import namedtuple
from dataclasses import dataclass
from pydtnsim import ContactIdentifier
from . import dijkstra
from . import cgr_utils

Neighbor = namedtuple('Neighbor', ['contact', 'node_id', 'route'])

Route = namedtuple(
    'Route',
    ['transmission_plan', 'edt', 'capacity', 'to_time', 'next_hop', 'hops'])

RouteListEntry = namedtuple('RouteListEntry',
                            ['list', 'excluded_contacts', 'avg_rdt'])


@dataclass
class AvgRouteDeliveryTime:
    """Holds the information about previously calculated Delivery Times."""

    mean: int = 0
    count: int = 0
    window_hit: int = 0
    window_miss: int = 0


def cgr(bundle,
        source_node,
        contact_graph,
        route_list,
        contact_list,
        current_time,
        limbo,
        hot_spots=None):
    """Core routing function of SCGR implementation.

     Enqueues a bundle (packet) into a contact queue base on CGR.

    Args:
        bundle (Packet): The Packet object that should be routed.
        source_node (string): The originating node (i.e. the node where the
            routing decision is performed)
        contact_graph (dict): The contact graph object that provides the
            topological information.
        route_list (list): Cache list to store already found routes inbetween
            routing decisions (whenever possible).
        contact_list (list): List of :mod:`Contact` objects that will be used
            for enqueuing the packet.
        current_time (int): The time of the routing decision (in ms).
        limbo (list): A node-based list where unroutable packets are enqueued
            (and in the best case considered again at a later point)
        hot_spots (list): The list of hot spots n the network. Required to
            prevent a frequent cause for loops. Defaults to none.

    """
    # Reset the list of the excluded nodes
    excluded_nodes = []

    # Check if the bundle prevents returning it to the sender node, if that is
    # the case, add sender to list of excluded nodes
    if not bundle.return_to_sender and bundle.hops:
        # Add all hot_spots to the excluded nodes list if the current node
        # is a hotspot and the packet came from a hot spot. This helps
        # to prevent loops.
        if (hot_spots is not None and source_node in hot_spots
                and bundle.hops[-1] in hot_spots):
            excluded_nodes.extend(hot_spots)
        else:
            excluded_nodes.append(bundle.hops[-1])

    # If the bundle is critical, replicate and forward it to all feasible
    # proximate neighbor nodes (i.e. flood it)
    # FIXME The critical bundle forwarding is experimental and cannot be
    # assumed to be correct yet. It needs more testing.
    if bundle.is_critical:
        for contact, route in find_critical_bundle_neighbors(
                contact_graph, source_node, bundle.end_node, excluded_nodes,
                current_time):
            # Create a deep copy of the packet object to create real duplicates
            bundle_copy = copy.deepcopy(bundle)

            # Don't set route characteristics for critical bundles

            # Enqueue to queue
            contact_list[contact].enqueue_packet(bundle_copy, route, None)

        del bundle
        # Return as all possible enqueueing operations already took place
        return

    best_route = identify_best_feasible_route(
        source_node,
        bundle,
        contact_graph,
        route_list,
        excluded_nodes,
        current_time,
        contact_list,
        ignore_capacity=True)

    first_alternative_route = identify_best_feasible_route(
        source_node,
        bundle,
        contact_graph,
        route_list,
        excluded_nodes,
        current_time,
        contact_list,
        alternative_route=True)

    # Identify the neighbor with the best feasible route to the destination
    neighbor = identify_best_feasible_route(source_node, bundle, contact_graph,
                                            route_list, excluded_nodes,
                                            current_time, contact_list)

    # Check if feasible next hop has been found, if so enqueue the packet for
    # the contact
    if neighbor:
        # Enqueue
        contact_list[neighbor.contact].enqueue_packet(bundle, neighbor.route,
                                                      best_route.route)
        bundle.add_planned_route(neighbor.route)

        if first_alternative_route:
            bundle.add_alternative_route(first_alternative_route.route)
        else:
            bundle.add_alternative_route(None)

    # If no feasible next hop could be found, enqueue the bundle to the limbo
    # (and maybe try later again)
    else:
        limbo.append(bundle)

    # returns nothing


def identify_best_feasible_route(source_node,
                                 bundle,
                                 contact_graph,
                                 route_list,
                                 excluded_nodes,
                                 current_time,
                                 contact_list,
                                 ignore_capacity=False,
                                 alternative_route=False):
    """Get the best route feasible for the specific tim e and packet.

    Args:
        source_node (string): Node where this routing operation is performed.
        bundle (packet): Routed packet.
        contact_graph (dict): Topology information as contact graph.
        route_list (list): Cache list to store already found routes inbetween
            routing decisions (whenever possible).
        excluded_nodes (list): List of nodes that should not be considered for
            forwarding.
        current_time (int): The time of the routing decision (in ms).
        contact_list (list): List of :mod:`Contact` objects that will be used
            for enqueuing the packet.
        ignore_capacity (boolean): When determining if a route is feasible,
            ignore the current utilization of the next hop contact. Defaults
            to False.
        alternative_route (boolean): Instead of the best route, return the
            next alternative one (if there is one), otherwise return None.
            Defaults to False.

    Returns:
        neighbor: A neighbor object containing the found best feasible route

    """
    # Load already found routes from dictionary or initialize otherwise
    if bundle.end_node in route_list:
        # Extract already computed values
        tmp_route_list = route_list[bundle.end_node].list
    else:
        # Create route list entry
        route_list[bundle.end_node] = RouteListEntry(
            list=[], excluded_contacts=[], avg_rdt=AvgRouteDeliveryTime())

        tmp_route_list = []

    found_best_route = False

    while True:
        for route in tmp_route_list:
            # If route to time (i.e. minimal end time of all individual route
            # contacts) is in the past, ignore the route
            if route.to_time <= current_time:
                continue

            # If route arrival time (the time that the bundle would reach the
            # desination) is larger than the deadline, ignore the route (i.e.
            # we are considering the deadlines to be hard deadlines)
            if route.edt >= bundle.deadline:
                continue

            # If the route's capacity is smaller than the bundle/packet size,
            # ignore the route
            if route.capacity < bundle.size:
                continue

            # If the next (i.e. first) hop of a route is in the excluded_nodes
            # list, ignore the route
            if route.transmission_plan[0].to_node in excluded_nodes:
                continue

            # If the queue for a particular contact is already full (i.e.
            # cannot house the currently routed bundle), ignore the route
            if not ignore_capacity and (
                    not contact_list[route.transmission_plan[0]].
                    is_capacity_sufficient(bundle)):
                continue

            if not alternative_route or found_best_route:
                return Neighbor(
                    contact=route.transmission_plan[0],
                    node_id=route.next_hop,
                    route=route)
            found_best_route = True

        # Reload one more route
        new_route, new_excluded_contact = generate_next_route(
            contact_graph, source_node, bundle.end_node,
            route_list[bundle.end_node].excluded_contacts, current_time,
            route_list[bundle.end_node].avg_rdt)

        # No routes found in graph -> abort
        if new_route is None:
            return None

        # Just make sure that we get sound routes
        assert (new_route.edt >= max(
            [c.from_time for c in new_route.transmission_plan]))

        route_list[bundle.end_node].list.append(new_route)
        route_list[bundle.end_node].excluded_contacts.append(
            new_excluded_contact)
        tmp_route_list = [new_route]


def remove_expired_contacts(contact_graph, time):
    """Remove expired and thus obsolete contacts from the contact graphself.

    Helps reducing complexity and thus boost route finding performance.

    Args:
        contact_graph (ContactGraph): A ContactGraph object for topology
            information.
        time (type): The current time. All contacts that expired before that
            time will be removed.

    """
    # Create copy of node list for iterating while modifying the graph
    graph_nodes = list(contact_graph.graph.keys())

    # Iterate over all nodes in graph
    for node in graph_nodes:
        if node.to_time < time:
            # Contact has expired, remove it from the graph
            contact_graph.remove_contact_node(node)

    # Delete outdated node list
    del graph_nodes


def generate_next_route(contact_graph, source_node, destination_node,
                        excluded_contacts, current_time, avg_rdt):
    """Generate an additional (next best) route to destination.

    Args:
        contact_graph (ContactGraph): A ContactGraph object for topology
            information.
        source_node (string): The node where the routing operation takes place
        destination_node (string): The destinatio node that routes should be
            provided for.
        excluded_contacts (list): A list of contacts that should not be
            considered during the route finding procedure. Used to mimic
            the removal of nodes within the graph in a more memory-efficient
            way.
        current_time (int): The simulated time when the route calculation is
            performed (in ms).
        avg_rdt (recordclass): A recordclass object holding the relevant values
            for determining and updating the dijkstra lookahead window.

    Raises:
        ValueError: If no matching limit contact can be found due to
            mismatching to_times.

    Returns:
        tuple: Provides a list of new routes and a list of excluded
        nodes. The excluded nodes were generated while finding the routes.
        They should not be considered in later searches!

    """
    # Generate root_contact terminal node definition
    root_contact = ContactIdentifier(
        from_node=source_node,
        to_node=source_node,
        from_time=0,
        to_time=math.inf,
        datarate=math.inf,
        delay=0)
    # Generate bundle's destination terminal node definition
    destination_contact = ContactIdentifier(
        from_node=destination_node,
        to_node=destination_node,
        from_time=0,
        to_time=math.inf,
        datarate=math.inf,
        delay=0)

    if avg_rdt.mean >= 0:
        lookahead_time = int(current_time + avg_rdt.mean * 1.2)
    else:
        lookahead_time = 8000

    # Determine the shortest route to the bundle's destination in the
    # contact graph representation of the contact plan with a lookahead
    # window limited to the 120% of the previously observed mean delivery
    # times.
    transmission_plan, distance = dijkstra.get_best_route(
        root_contact,
        destination_contact,
        contact_graph,
        cgr_utils.cgr_neighbor_function,
        current_time,
        hashes=contact_graph.hashes,
        suppressed_contacts=excluded_contacts,
        lookahead_time=lookahead_time)

    # If no route has been found in the lookahead window, fall back to the
    # version without the window.
    if transmission_plan is None:
        # Determine the shortest route to the bundle's destination in the
        # contact graph representation of the contact plan without any
        # lookahead window.
        transmission_plan, distance = dijkstra.get_best_route(
            root_contact,
            destination_contact,
            contact_graph,
            cgr_utils.cgr_neighbor_function,
            current_time,
            hashes=contact_graph.hashes,
            suppressed_contacts=excluded_contacts)

        if transmission_plan is None:
            # End the route finding process if no route is found. This means no
            # more routes are available in the contact graph
            return None, None

        avg_rdt.window_miss += 1
        avg_rdt.count += 1
        avg_rdt.mean += (distance - current_time) / avg_rdt.count
    else:
        avg_rdt.window_hit += 1
        avg_rdt.count += 1
        avg_rdt.mean += (distance - current_time) / avg_rdt.count

    # Remove unnecessary root and terminal nodes from the route
    transmission_plan = transmission_plan[1:-1]

    # Generate route characteristics and add this information to the route
    edt, cap, to_time = cgr_utils.cgr_get_route_characteristics(
        transmission_plan, distance)

    # Assign the found route as option for the bundle's destination to the
    # route list
    route = Route(
        transmission_plan=transmission_plan,
        next_hop=transmission_plan[0].to_node,
        edt=edt,
        capacity=cap,
        to_time=to_time,
        hops=len(transmission_plan))

    # If the end time of the overall route is the end time of the first
    # contact of that route (i.e. the first hop), regard to the first
    # contact (hop) as the limiting contact (the contact that ends first
    # and thus renders the entire route invalid)
    limit_contact = None
    for contact in route.transmission_plan:
        if contact.to_time == route.to_time:
            limit_contact = contact
            new_excluded_contact = limit_contact
            break

    # Raise error if we couldn't find a contact matching to the calculated
    # to_time
    if limit_contact is None:
        raise ValueError("The calculated to_time of the route does not" +
                         " match any contacts to_time!")

    # Supress the limit contact as we have already found the best route for
    # that limiting contact and worse routes with that limiting contact
    # should not be considered (realised by setting the suppressed flag in
    # the working area of the contact)

    # Return the route list with the updated routes for the bundle's
    # destination node
    return route, new_excluded_contact


def find_critical_bundle_neighbors(contact_graph, source_node,
                                   destination_node, excluded_nodes,
                                   current_time):
    """Determine all feasible neighbor nodes for forwarding a critical bundle.

    Args:
        contact_graph (dict): Topology information as contact graph.
        source_node (string): Node where this routing operation is performed.
        destination_node (string): Destination node of the packet.
        excluded_nodes (type): List of nodes that should not be considered for
            forwarding.
        current_time (int): Time in the simulation that the calculation is
            performed (in ms).

    Returns:
        list: A list of all feasible neighbor nodes in the form `(neighbor,
        distance, hop count, route)`

    """
    # Initialize route list
    neighbor_list = list()

    # Generate root_contact terminal node definition
    root_contact = ContactIdentifier(
        from_node=source_node,
        to_node=source_node,
        from_time=0,
        to_time=math.inf,
        datarate=math.inf,
        delay=0)
    # Generate bundle's destination terminal node definition
    destination_contact = ContactIdentifier(
        from_node=destination_node,
        to_node=destination_node,
        from_time=0,
        to_time=math.inf,
        datarate=math.inf,
        delay=0)

    # Initialize the suppressed contacts list
    suppressed_contacts = []

    for neighbor in contact_graph.graph[root_contact][0]:
        # Ignore neighbors that are in the excluded nodes list
        if neighbor in excluded_nodes:
            continue

        # Determine all neigbors that are ignored for this evaluation run
        blocked_neigbors = copy.deepcopy(contact_graph \
                            .graph[root_contact][0])
        blocked_neigbors.remove(neighbor)
        suppressed_contacts = blocked_neigbors

        # Determine the shortest route to the bundle's destination in the
        # contact graph representation of the contact plan
        transmission_plan, distance = dijkstra.get_best_route(
            root_contact,
            destination_contact,
            contact_graph,
            cgr_utils.cgr_neighbor_function,
            current_time,
            hashes=contact_graph.hashes,
            suppressed_contacts=suppressed_contacts)

        # End the route finding process if no route is found. This means no
        # more routes are available in the contact graph
        if transmission_plan is None:
            continue

        # Remove unnecessary root and terminal nodes from the route
        transmission_plan = transmission_plan[1:-1]

        # Generate route characteristics and add this information to the route
        edt, cap, to_time = cgr_utils.cgr_get_route_characteristics(
            transmission_plan, distance)

        # Assign the found route as option for the bundle's destination to the
        # route list
        route = Route(
            transmission_plan=transmission_plan,
            next_hop=transmission_plan[0].to_node,
            edt=edt,
            capacity=cap,
            to_time=to_time,
            hops=len(transmission_plan))

        # Assign the found route as option for the bundle's destination to the
        # route list
        neighbor_list.append((route.transmission_plan[0], route))

        del blocked_neigbors

    return neighbor_list
