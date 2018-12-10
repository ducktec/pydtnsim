"""Simple(st) CGR routing algorithm implementation.

This module contains an implementation of the CGR routing algorithm as
outlined in the paper *Assessing Contact Graph Routing Performance and
Reliability in Distributed Satellite Constellations* by Fraire et al.

However, this implementation does not implement the anchoring mechanism
outlined in the paper!

This routing implementation currently has no overbooking handling implemented!

The module has two main routines:

CGR Forward Routine:
    This routine has to be executed on a per-bundle
    basis. :func:`cgr` and :func:`identify_proximate_node_list` are part of
    this routine.
CGR Routing Routine:
    This routine has to be performed whenever the contact graph changes.
    :func:`load_route_list` is part of that routine.
"""

import math
import copy
from collections import namedtuple
from pydtnsim import ContactIdentifier
from . import dijkstra
from . import cgr_utils

Neighbor = namedtuple('Neighbor', ['contact', 'node_id', 'route'])

Route = namedtuple(
    'Route',
    ['transmission_plan', 'edt', 'capacity', 'to_time', 'next_hop', 'hops'])


def cgr(bundle,
        source_node,
        contact_graph,
        route_list,
        contact_list,
        current_time,
        limbo,
        hot_spots=None,
        proximate_nodes=None):
    """Core routing function of CGR implementation.

     Enques a bundle (packet) into a contact queue base on CGR.

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
        proximate_nodes (list): A list of feasible neigbor nodes. Only used
                                for unit testing to isolate this function's
                                behaviour. Defaults to None.

    """
    # Reset the list of the excluded nodes
    excluded_nodes = []

    # In this function we expect that the route list is reseted manually
    # whenever the contact graph changes, thus no reset mechanism is
    # implemented

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

    # Identify feasible proximate neighbor n odes (if no list was already
    # provided, helpful for unit tests)
    if proximate_nodes is None:
        proximate_nodes = identify_proximate_node_list(
            source_node, bundle, contact_graph, route_list, excluded_nodes,
            current_time, contact_list)

    # If the bundle is critical, replicate and forward it to all feasible
    # proximate neighbor nodes (i.e. flood it)
    if bundle.is_critical:
        # Enqueue it for all identified neighbors
        for neighbor in proximate_nodes:
            # Create a deep copy of the packet object to create real duplicates
            bundle_copy = copy.deepcopy(bundle)

            # Don't set route characteristics for critical bundles

            # Enqueue to queue
            contact_list[neighbor.contact].enqueue_packet(
                bundle_copy, neighbor.route, None)

        del bundle
        # Return as all possible enqueueing operations already took place
        return

    # Reset next hop optimization variable
    next_hop = None

    # Iterate over all returned proximate nodes (or rather, routes) and select
    # the best (first based on EDT, then on Hops)
    for neighbor in proximate_nodes:

        # If no value was set yet, take the first available one
        if not next_hop:
            next_hop = neighbor

        # If the edt of the iterated node is better than the saved value,
        # update the saved optimization variable
        elif neighbor.route.edt < next_hop.route.edt:
            next_hop = neighbor
        # Otherwise continue
        elif neighbor.route.edt > next_hop.route.edt:
            continue

        # If the hops of the iterated node are less than the saved value,
        # update the saved optimization variable
        elif neighbor.route.hops < next_hop.route.hops:
            next_hop = neighbor
        elif neighbor.route.hops > next_hop.route.hops:
            continue

        # Consistency feature for SCGR. This condition is not existent in
        # vanilla cgr and is added to provide the same routing decisions as
        # SCGR. Basically, before deciding on the basis of the hash value we
        # also make the start time of the next contact (i.e. when the packet
        # is leaving the node) a parameter.
        elif neighbor.contact.from_time < next_hop.contact.from_time:
            next_hop = neighbor
        elif neighbor.contact.from_time > next_hop.contact.from_time:
            continue

        # If all characteristics were identical before, make decision based
        # on the hashes of the node id (names).
        elif hash(neighbor.node_id) < hash(next_hop.node_id):
            next_hop = neighbor

    # Check if feasible next hop has been found, if so enqueue the packet for
    # the contact
    if next_hop:
        # Update characteristics if source node
        if bundle.source_node == source_node:
            bundle.add_planned_route(next_hop.route)

        # Enqueue
        contact_list[next_hop.contact].enqueue_packet(bundle, next_hop.route,
                                                      None)

    # If no feasible next hop could be found, enqueue the bundle to the limbo
    # (and maybe try later again)
    else:
        limbo.append(bundle)

    # returns nothing


def identify_proximate_node_list(source_node, bundle, contact_graph,
                                 route_list, excluded_nodes, current_time,
                                 contact_list):
    """Compile a list of feasible neighbor nodes.

      Neigbor nodes are feasible for fowarding if they have a feasible route
      to forward the bundle to the destination node.

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

    Returns:
        list: A list of feasible neigbor nodes that can forward the packet to
        it's destination.

    """
    proximate_nodes = list()

    # If the route list for a particular destination is empty, (re-)load the
    # route list by invoking load_route_list for that destination
    if bundle.end_node not in route_list.keys() or route_list[bundle.
                                                              end_node] == []:
        route_list[bundle.end_node] = load_route_list(
            contact_graph, source_node, bundle.end_node, current_time)

    for route in route_list[bundle.end_node]:
        # If route to time (i.e. minimal end time of all individual route
        # contacts) is in the past, ignore the route
        if route.to_time <= current_time:
            continue

        # If route arrival time (the time that the bundle would reach the
        # desination) is larger than the deadline, ignore the route (i.e. we
        # are considering the deadlines to be hard deadlines)
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

        # If the queue for a particular contact is already full (i.e. cannot
        # house the currently routed bundle), ignore the route
        if (not contact_list[route.transmission_plan[0]].
                is_capacity_sufficient(bundle)):
            continue

        # Iterate over all already detected proximate nodes to optimize the
        # characteristics of the proximate nodes if they are also used by the
        # investigated route and the routes characteristics are better
        for proximate_node in proximate_nodes:
            # Only consider updating node characteristics if the proximate node
            # is the first hop of the investigated route
            if proximate_node.node_id == route.next_hop:
                # If the arrival time of the investigated route is better than
                # the values saved for the current route of the proximate node,
                # then replace the characteristics with the new route by
                # deleting and reinserting the list item
                if proximate_node.route.edt > route.edt:
                    proximate_nodes.remove(proximate_node)
                    proximate_nodes.append(
                        Neighbor(
                            contact=route.transmission_plan[0],
                            node_id=route.next_hop,
                            route=route))

                # If the arrival time of the investigated route is worse,
                # ignore route and continue
                elif proximate_node.route.edt < route.edt:
                    continue

                # If more hops are required for the currently linked proximate
                # node route, then update the proximate node characteristics to
                # the current route by deleting and reinserting the list item
                elif proximate_node.route.hops > route.hops:
                    proximate_nodes.remove(proximate_node)
                    proximate_nodes.append(
                        Neighbor(
                            contact=route.transmission_plan[0],
                            node_id=route.next_hop,
                            route=route))

                # If less hops are required with the currently linked route,
                # continue
                elif proximate_node.route.hops < route.hops:
                    continue

                # As final optimization option, we use a hash of the node
                # identifier (the smaller the better)
                elif hash(proximate_node.node_id) > hash(route.next_hop):
                    proximate_nodes.remove(proximate_node)
                    proximate_nodes.append(
                        Neighbor(
                            contact=route.transmission_plan[0],
                            node_id=route.next_hop,
                            route=route))

                # Stop iterating the proximate node list because the
                # corresponding proximate node (to the first hop of the route)
                # was found
                break

        # If the next hop of the route is not element of the proximate_nodes
        # list
        if (route.next_hop not in [
                neighbor.node_id for neighbor in proximate_nodes
        ]):

            proximate_node = Neighbor(
                contact=route.transmission_plan[0],
                node_id=route.next_hop,
                route=route)
            proximate_nodes.append(proximate_node)

    return proximate_nodes


def load_route_list(contact_graph, source_node, destination_node,
                    current_time):
    """Generate a list of all feasible routes.

    Routes are calculated from the source node to the destination node.

    Args:
        contact_graph (dict): The topology information in the form of a
                              contact graph.
        source_node (string): The identifier of the source node (where the
                              routing decision is performed)
        destination_node (sting): The identifier of the destination node.
        current_time (int): Time in the simulation when the calculation
            is performed (in ms).

    Raises:
        ValueError: If no matching limit contact can be found due to
            mismatching to_times.

    Returns:
        list: A list of all feasible routes in the form of (route,
              route_characteristics)

    """
    # Initialize route list
    route_list = list()

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

    # Initialize the list of excluded contacts
    suppressed_contacts = []

    # Main loop (which is left when there are no more routes to be considered
    # between the source node and the bundle's destination)
    while True:

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
            break

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

        route_list.append(route)

        limit_contact = None
        for contact in route.transmission_plan:
            if contact.to_time == route.to_time:
                limit_contact = contact
                break

        # Raise error if we couldn't find a contact matching to the calculated
        # to_time
        if limit_contact is None:
            raise ValueError("The calculated to_time of the route does not" +
                             " match any contacts to_time!")

        # Remove the limit contact as we have already found the best route for
        # that limiting contact and worse routes with that limiting contact
        # should not be considered. As the temp graph is not used beyond
        # this iterative search, no side effects occur.
        suppressed_contacts.append(limit_contact)

    # Return the route list with the updated routes for the bundle's
    # destination node
    return route_list
