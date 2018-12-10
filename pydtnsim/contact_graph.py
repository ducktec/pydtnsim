"""Implementation of a contact graph object."""

from collections import OrderedDict, namedtuple
import math
import networkx as nx
from .contact_plan import ContactIdentifier, ContactPlan

# ContactIdentifier object for better readability and access to identifer
# tuple object.
NeighborLists = namedtuple('NeighborLists', ['successors', 'predecessors'])


class ContactGraph:
    """Represents a specific contact graph in the CGR context.

    The :class:`ContactGraph` object represents the same information than a
    :class:`ContactPlan` object, but in a different form.

    It can be generated based on any :class:`ContactPlan` and is subsequently
    used for CGR routing purposes.

    Args:
        contact_plan (pydtnsim.ContactPlan): The ContactPlan object
            posing the information base for the new object. Defaults to
            None.
    """

    @staticmethod
    def _create_graph_edges(graph):
        """Create the edges within all nodes of the contact graph.

        Args:
            graph (dict): The graph object that already contains the nodes
                and that's successor/predecessor lists should be generated.

        """
        node_list = list(graph.keys())

        # Now that we have all nodes, start generating the edges which is quite
        # expensive but we only have to do it once for all nodes and all times
        # (as long as the contact plan is not changing)
        for node1 in graph:
            # Remove the currently investigated node
            node_list.remove(node1)
            for node2 in node_list:
                # Check if the end node of the first contact is the start node
                # of the second contact and the next contact is not returning
                # to the initial node
                if (node1.to_node == node2.from_node
                        and node1.from_node != node2.to_node):
                    # If that is the case, evaluate if the timing adds up
                    if node2.to_time > node1.from_time:
                        # Add edge from node1 to node2 (directed, by adding
                        # link to node2 to successor list of node1), also add
                        # node1 to list of predecessors of node2
                        graph[node1].successors.append(node2)
                        graph[node2].predecessors.append(node1)
                # Also check if the end node of the second contact is the
                # start node of the first contact and the next contact is not
                # returning to the initial node
                elif (node2.to_node == node1.from_node
                      and node2.from_node != node1.to_node):
                    # If that is the case, evaluate if the timing adds up
                    if node1.to_time > node2.from_time:
                        # Add edge from node1 to node2 (directed, by adding
                        # link to node2 to successor list of node1), also add
                        # node1 to list of predecessors of node2
                        graph[node2].successors.append(node1)
                        graph[node1].predecessors.append(node2)

        # Sort the predecessor/successor lists by the hash value of the
        # nodes.
        for node in graph:
            graph[node].successors.sort(
                key=(lambda c: (c.to_time, hash(c.to_node))), reverse=True)
            graph[node].predecessors.sort(
                key=(lambda c: (c.to_time, hash(c.from_node))), reverse=True)

    @staticmethod
    def _generate_contact_graph(contact_plan):
        """Generate a contact graph based on a given contact plan.

        Args:
            contact_plan (ContactPlan): The contact plan representation used
                for the contact graph generation.

        Returns:
            OrderedDict: The contact graph as ordered dictionary

        Raises:
            ValueError: If the function is called with an object other than
                ContactPlan.

        """
        if not isinstance(contact_plan, ContactPlan):
            raise ValueError("The loaded contact plan is not a ContactPlan "
                             "object")

        # TODO: Normal dictionaries are ordered in Python +3.7
        graph = OrderedDict()

        for contact in contact_plan.plan['contacts']:
            # Add item to graph:
            # - Key: from_node, to_node, start_time, end_time, datarate, delay
            # - Value: NeighborLists(namedtuple)
            graph[contact] = NeighborLists(
                successors=list(), predecessors=list())

            # Create identifier for terminal node
            terminal_node = ContactIdentifier(
                from_node=contact.to_node,
                to_node=contact.to_node,
                from_time=0,
                to_time=math.inf,
                datarate=math.inf,
                delay=0)
            # Create identifier for root node
            root_node = ContactIdentifier(
                from_node=contact.from_node,
                to_node=contact.from_node,
                from_time=0,
                to_time=math.inf,
                datarate=math.inf,
                delay=0)

            # Create terminal node (if not existing yet)
            if terminal_node not in graph:
                graph[terminal_node] = NeighborLists(
                    successors=list(), predecessors=list())
            # Create root node (if not existing yet)
            if root_node not in graph:
                graph[root_node] = NeighborLists(
                    successors=list(), predecessors=list())

        for node in contact_plan.plan['nodes']:
            # Create identifier for terminal node
            nominal_node = ContactIdentifier(
                from_node=node,
                to_node=node,
                from_time=0,
                to_time=math.inf,
                datarate=math.inf,
                delay=0)
            # Create root node (if not existing yet)
            if nominal_node not in graph:
                graph[nominal_node] = NeighborLists(
                    successors=list(), predecessors=list())

        # Return the generated graph object
        return graph

    def __init__(self, contact_plan=None):
        if contact_plan is not None:
            self.graph = ContactGraph._generate_contact_graph(contact_plan)
            self._create_graph_edges(self.graph)
            self.hashes = self._generate_hashes()

            # Copy the coldspot/hotspot information from the ContactPlan
            self.hotspots = contact_plan.hotspots
            self.coldspots = contact_plan.coldspots
            self.capacity_storage = None
        else:
            self.graph = OrderedDict()
            self.hashes = OrderedDict()

    def remove_contact_node(self, contact):
        """Remove single contact from graph.

        Args:
            contact (ContactIdentifier): Contact identifier referencing the
                contact to be removed.

        Raises:
            ValueError: If the contact identifier is not a ContactIdentifier
                named tuple or if the contact identifier is not in the current
                graph.

        """
        # Check if contact is the right type
        if not isinstance(contact, ContactIdentifier):
            raise ValueError("ContactIdentifier named tuple should be used \
                             for accessing ContactGraph object")
        elif contact not in self.graph:
            raise ValueError("Contact specified by identifier not part of \
                             graph")

        # Remove the reference to the contact (i.e. the edge) from all
        # predecessors of this contact
        for pred in self.graph[contact].predecessors:
            self.graph[pred].successors.remove(contact)

        # Remove the reference to the contact (i.e. the edge) from all
        # successors of this contact
        for succ in self.graph[contact].successors:
            self.graph[succ].predecessors.remove(contact)

        # Remove node from graph dict
        del self.graph[contact]
        del self.hashes[contact]

    def add_contact_node(self, contact):
        """Add contact node to graph object.

        Args:
            contact (ContactIdentifier): Contact that should be added to the
             contact graph.

        Raises:
            ValueError: When no ContactIdentifier named tuple is used for
             this operation.

        """
        # Check if contact is the right type
        if not isinstance(contact, ContactIdentifier):
            raise ValueError("ContactIdentifier named tuple should be used \
                             for accessing ContactGraph object")

        # Add node to graph dictionary
        self.graph[contact] = NeighborLists(
            successors=list(), predecessors=list())

        self.hashes[contact] = (hash(contact.to_node), hash(contact.from_node))

        # Add contact successors and predecessors
        for cont in self.graph:
            if cont == contact:
                # Ignore self reference
                continue
            # Check if contact can be successor or predecessor
            if cont.to_time > contact.from_time and \
               cont.from_node == contact.to_node:
                self.graph[contact].successors.append(cont)
                self.graph[cont].predecessors.append(contact)
            if contact.to_time > cont.from_time and \
               contact.from_node == cont.to_node:
                self.graph[contact].predecessors.append(cont)
                self.graph[cont].successors.append(contact)

    def remove_topology_node(self, node_identifier):
        """Remove a topological node from the ContactGraph object.

        Can be used to e.g. purge an entire ground station from the graph.

        Args:
            node_identifier (string): Identifier of the topological node.

        """
        # Iterate over all contacts of graph and check if topological node
        # is involved (either as source or destination node of a contact)
        for contact in list(self.graph.keys()):
            if node_identifier in (contact.from_node, contact.to_node):
                # Call function to remove applicable contact nodes from graph
                self.remove_contact_node(contact)

    def _generate_hashes(self):
        """Generate hashes for all nodes in graph.

        Returns:
            OrderedDict: A dictionary with the hashes of all nodes of the
                graph.

        """
        hashes = OrderedDict()
        for contact in self.graph:
            hashes[contact] = (hash(contact.to_node), hash(contact.from_node))

        return hashes

    def reinitialize(self, contact_plan=None):
        """Delete and regenerate the internal contact graph representation.

        Args:
            contact_plan (pydtnsim.ContactPlan): The ContactPlan object
                used for the new graph generation. Defaults to None.
        """
        # Delete the current information
        del self.graph

        if contact_plan is not None:
            # Reinitialize the internal representation of the contact graph
            self.graph = self._generate_contact_graph(contact_plan)
            self.hashes = self._generate_hashes()
        else:
            self.graph = OrderedDict()
            self.hashes = OrderedDict()

    def get_networx_contact_graph(self, ignore_notional_nodes=False):
        """Provide contact graph as :mod:`networkx` :class:`DiGraph`.

        Args:
            ignore_notional_nodes (type): Return a networkx contact graph
                representation that does not include the notional nodes.
                Defaults to False.

        Returns:
            DiGraph: A networkx graph representation of the contact graph.

        """
        # Create empty DiGraph object
        graph = nx.DiGraph()

        # Add all nodes in the topology to the graph
        for node in self.graph.keys():
            if (ignore_notional_nodes and node.from_node == node.to_node):
                continue
            graph.add_node(str(node))

        # Add edges between the contact nodes
        for node in self.graph.keys():
            for successor in self.graph[node].successors:
                graph.add_edge(str(node), str(successor))

        # Return graph
        return graph
