"""Module of commonly shared functions of various flavours of CGR."""
import math


def cgr_neighbor_function(contact_graph, node, destination, current_distance,
                          set_visited, suppressed_contacts, lookahead_time):
    """Neighbor function of CGR used by the Dijkstra algorithm.

     Used to determine feasible direct neigbors of a given node.

    Args:
        contact_graph (ContactGraph): The topology information in the form
            of a contact graph
        node (tuple): The evaluated node in the contact graph node form
            ``(from_node, to_node, from_time, to_time, data_rate)``.
        destination (tuple): The nominal destination node in the form
            ``(destination_id, destination_id, 0, math.inf, math.inf)``
        current_distance (int): Contains the weight of the shortest path
            to the currently investigated node (in ms).
        set_visited (set): Set used for storing the visited flag
            of nodes during the Dijkstra runs. Also used for excluding
            suppressed (physical) nodes.
        suppressed_contacts (list): List of contacts that shall not be
            considered for forwarding (and thus neighbor selection)
        lookahead_time (int): Time value that specifies a time window
            (or rather a maximum time) only in which routes are searched.
            This reduces the time necessary to find a shortest route.

    Returns:
        list: A list of all feasible neighbors with items of the form
        ``(<node_id>, weight)`` with ``<node_id>`` representing a certain
        contact in the contact graph.

    """
    neighbors = []

    # Set the node as visited
    set_visited.add(node.from_node)

    # Extract the start time of the given node
    for edge in contact_graph.graph[node].successors:
        # Break the loop if the found edge to_time is smaller than the
        # current distance. As the successor list is sorted, all subsequent
        # edges will be smaller as well.
        if edge.to_time <= current_distance:
            break

        # Only consider when neigbor has not been visited by dijkstra yet
        # and it is not in the suppressed_contacts list
        # and can be reached given the currently consideret point in time
        # and if it is within the lookahead window (only when a lookahead
        # window is used)
        if ((lookahead_time is None or edge.from_time < lookahead_time)
                and edge.to_node not in set_visited
                and edge not in suppressed_contacts
                and (edge.to_time > current_distance)):
            # Only add to neighbors if no artificial end node or artificial end
            # node is bundle's destination
            if edge == destination or edge.from_node != edge.to_node:
                # Calculate the time (which is either positive or 0, relevant
                # for artificial terminal nodes)
                weight = edge.from_time - current_distance
                if weight < 0:
                    weight = 0

                # Append to neighbor list with weight
                neighbors.append((edge, weight))

    return neighbors


def cgr_get_route_characteristics(route, distance):
    """Calculate characteristics of a certain route.

    Args:
        route (list): A list of the nodes of the calculated route that's
            elements comprise of all relevant information for determining the
            characteristics'
        distance (int): The precalculated distance

    Returns:
        tuple: A tuple consisting of the (precalculated) distance, the capacity
        and the end time of the availability of that route

    """
    capacity = math.inf
    distance = 0

    # Iterate over all nodes in route and check if capacity is smaller than
    # already found minimum
    for node in route:
        distance = max(distance, node.from_time)
        # Generate capacity for node's contact
        capacity_new = ((node.to_time - distance) * node.datarate)

        # Update capacity if smaller
        if capacity_new < capacity:
            capacity = capacity_new

    # The to_time of a route is the minimum end time of a contact within this
    # route (minus the assumed signal propagation delay, in the rr considered
    # to be neglegible)
    to_time = min([node.to_time for node in route])

    # Return the characteristics tuple consisting of the route distance (i.e.
    # the arrival time), the route capacity and the route availability end
    # time (i.e. the to-time)
    return (distance, capacity, to_time)
