r"""Implementation of the Dijkstra algorithm for finding shortest paths.

The algorithm is implemented using a priority queue (in particular heapq that
is provided in python). This should provide a complexity of :math:`O(E \\cdot
log(V))`,
while many other implementations have the complexity :math:`O(V \\cdot E)`.

.. note::

    This still has to be verified, as it has not been evaluated how efficient
    the priority queue implementation is.
"""

import heapq
import math
from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class DijkstraMetrics:
    """Holds Dijkstra data of a certain node."""

    dist: int
    first_hop_dist: int
    path: str
    hops: int
    hash: int


def get_best_route(source,
                   destination,
                   graph,
                   direct_neighbor,
                   current_time,
                   suppressed_nodes=None,
                   suppressed_contacts=None,
                   hashes=None,
                   lookahead_time=None):
    """Return the best route from source to destination through the graph.

    Args:
        source (ContactIdentifier): Source node
        destination (ContactIdentifier): Destination node
        graph (ContactGraph): The Graph that should routed
        direct_neighbor (callable): A callable providing the adjecent nodes of
            a given node - i.e. the neighbors - and the corresponding weight
            (distance) of the specific neighbors return. The signature is as
            follows:

            .. function:: def direct_neighbor(graph, node, distance)
        current_time (int): Time in the simulation when the calculation
            is performed (in ms).
        suppressed_nodes (list): A list of nodes that should not be considered
         during the Dijkstra search run. Defaults to [].
        suppressed_contacts (list): A list of contacts that should not be
         considered during the Dijkstra search run. Defaults to [].
        hashes (dict): A dictionary providing precomputed hash values in tuples
         for all nodes of the graph object. Defaults to None. Hashes are
         computed internally then.
        lookahead_time (int): Time value that specifies a time window
            (or rather a maximum time) only in which routes are searched.
            This reduces the time necessary to find a shortest route.
    Returns:
        tuple: A tuple of the form `(<route>, <weight>)` with `<route>` being
         the found shortest route and `<weight>` the cost of that route.

    .. seealso::

        https://www.geeksforgeeks.org/dijkstras-shortest-path-algorithm-using-priority_queue-stl/

        Based on the provided pseudocode

    """
    priority_queue = list()
    metrics = dict()
    visited = set()

    if suppressed_nodes is None:
        suppressed_nodes = []

    if suppressed_contacts is None:
        suppressed_contacts = []

    if hashes is None:
        hashes = OrderedDict()
        for vertex in graph:
            hashes[vertex] = hash(vertex)

    # Set vertices visited that are in the suppressed list.
    for node in suppressed_nodes:
        visited.add(node)

    # Return immediately with an empty route when source is destination
    if source == destination:
        return [], 0

    # Set distance to source to 0 and add to priority queue
    # Also set the (secondary) hop count to 0
    metrics[source] = DijkstraMetrics(
        dist=0, hops=0, first_hop_dist=0, path=None, hash=hashes[source])

    heapq.heappush(priority_queue,
                   (current_time, 0, 0, hashes[source], source))

    # Loop until the priority queue becomes empty
    while priority_queue:
        # Pop the vertex with the shortest distance from the priority queue
        (dist_min_node, min_hop_count, min_first_hop_dist, hash_min,
         min_node) = heapq.heappop(priority_queue)

        # End the looping if we are evaluating the destination node
        # We definitely found the best route
        if min_node == destination:
            break

        # Iterate over all neighbors of the selected vertex
        for neighbor, dist_neigh in direct_neighbor(
                graph, min_node, destination, dist_min_node, visited,
                suppressed_contacts, lookahead_time):
            # Calculate the overall distance of the minimal path from the
            # source through the min node to the neighbor
            new_distance = dist_min_node + dist_neigh

            if neighbor not in metrics:
                if min_node == source:
                    hash_val = hashes[neighbor]
                    first_hop_dist_val = new_distance
                else:
                    hash_val = hash_min
                    first_hop_dist_val = min_first_hop_dist

                metrics[neighbor] = DijkstraMetrics(
                    dist=new_distance,
                    hops=min_hop_count + 1,
                    first_hop_dist=first_hop_dist_val,
                    path=min_node,
                    hash=hash_val)

                # If not done yet, add the neighbor with the updated values to
                # the priority queue (there might be more than one instance of
                # one node in the queue, but the priority mechanism ensures
                # that always the best one is evaluated)
                heapq.heappush(priority_queue,
                               (new_distance, min_hop_count + 1,
                                first_hop_dist_val, hash_val, neighbor))

            # If that distance is smaller than the distance that was previously
            # calculated, then update the values values and append the new
            # found path to the priority list (we can end if we found the
            # destination node, the found path will be the shortest)
            elif ((metrics[neighbor].dist, metrics[neighbor].hops,
                   metrics[neighbor].first_hop_dist, metrics[neighbor].hash) >
                  (new_distance,
                   (min_hop_count + 1), min_first_hop_dist, hash_min)):

                # Update the distance
                metrics[neighbor].dist = new_distance

                # Update the hop count to the new lower value
                metrics[neighbor].hops = min_hop_count + 1

                # Note the neighbor to be later able to reproduce the shortest
                # path
                metrics[neighbor].path = min_node

                # Save the better first hop
                metrics[neighbor].first_hop_dist = min_first_hop_dist

                # Save the better first hash
                metrics[neighbor].hash = hash_min

                # If not done yet, add the neighbor with the updated values to
                # the priority queue (there might be more than one instance of
                # one node in the queue, but the priority mechanism ensures
                # that always the best one is evaluated)
                heapq.heappush(priority_queue,
                               (new_distance, min_hop_count + 1,
                                min_first_hop_dist, hash_min, neighbor))

    # Check if route was found
    if destination in metrics and metrics[destination].dist < math.inf:
        # Best route found, no generate the path to return to the callee
        node = destination
        path_list = list()
        while node != source:
            path_list.append(node)
            node = metrics[node].path

        path_list.append(source)

        # Return generated path (in the correct order source -> dest)
        return list(reversed(path_list)), metrics[destination].dist
    # No route from source to destination was found, return no route (i.e.
    # None)
    return None, math.inf
