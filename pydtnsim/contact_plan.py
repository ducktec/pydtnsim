"""Implementation of a contact plan object."""

from collections import OrderedDict, namedtuple
import json
import math
import networkx as nx
from jsonschema import validate, ValidationError

# The schema of the TVG JSON output files that is validated
LEGACY_TVG_SCHEMA = {
    "type": "object",
    "properties": {
        "vertices": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "vertices": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "contacts": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 3,
                            "items": {
                                "type": "number"
                            }
                        }
                    }
                }
            }
        }
    }
}

# The schema of the TVG_UTIL JSON output files that is validated
TVG_SCHEMA = {
    "type": "object",
    "properties": {
        "vertices": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "vertices": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "contacts": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type":
                            "array",
                            "minItems":
                            7,
                            "maxItems":
                            7,
                            "items": [{
                                "type": "string"
                            }, {
                                "type": "string"
                            }, {
                                "type": "number"
                            }, {
                                "type": "number"
                            },
                                      {
                                          "type": "array",
                                          "minItems": 1,
                                          "maxItems": 1,
                                          "items": {
                                              "type": "array",
                                              "minItems": 2,
                                              "maxItems": 2,
                                              "items": {
                                                  "type": "number"
                                              }
                                          }
                                      }, {
                                          "type": "number"
                                      }, {
                                          "type": "number"
                                      }]
                        }
                    }
                }
            }
        }
    }
}

# ContactIdentifier object for better readability and access to identifer
# tuple object.
ContactIdentifier = namedtuple(
    'ContactIdentifier',
    ['from_node', 'to_node', 'from_time', 'to_time', 'datarate', 'delay'])


class ContactPlan:
    """Represents a specific contact plan in the CGR context.

    It can be either filled manually or by loading a JSON representation
    (following the dtn-tvg-tools syntax) of the plan. The contact plan object
    can then be used for generating contact graphs and getting relevant
    information about the topology.
    """

    def __init__(self,
                 default_datarate,
                 default_delay,
                 json_source_file=None,
                 json_str=None,
                 simulation_end_time=math.inf):
        """Initialize the contact plan object.

        Is initialized either as empty object or as an object filled with the
        contents of the json_source_file.

        .. note::

            Contacts in the TVG-DTN-Tools JSON representation are always
            considered bidirectional, thus one contact object in JSON is
            considered as a contact for both involved nodes!

        Args:
            default_datarate (int): The contact datarate in bit/ms that is
                used whenever no specific datarate is provided (e.g. when
                loading the contact plan from a JSON file)
            default_delay (int): The default transimission delay in ms.
                Is used whenever no specific delay is provided (e.g. when
                loading the contact plan from a JSON file)
            json_source_file (string): The path to a JSON source file that is
                used to load a predefined contact plan from that file. Defaults
                to None.
            json_str (string): A string already containing the
                predefined contact plan (e.g. previously loaded from a file).
            json_source_file (str): A path to a JSON source file following the
                DTN-TVG-Output syntax.
            simulation_end_time (int): The time in ms when the simulation
                should end. Contacts in the source file that are starting after
                that time are ignored and contacts that end after the time
                are shortened.

        Raises:
            ValueError: If both a json source file and a json string are
                provided for initialization

        """
        # Save delay and datarate values
        self.default_datarate = default_datarate
        self.default_delay = default_delay

        # Initialize the internal representation of the contact plan
        self.plan = OrderedDict()
        self.plan['nodes'] = list()
        self.plan['contacts'] = list()
        self.hotspots = None
        self.coldspots = None

        # Load plan from file if json_source_file is specified
        if json_source_file is not None and json_str is not None:
            raise ValueError("Ambiguous topology configuration provided!")
        elif json_source_file is not None:
            data = self._load_json_from_file(json_source_file)
            self.load_dtn_tvg_plan(data, simulation_end_time, default_datarate,
                                   default_delay)
        elif json_str is not None:
            data = self._load_json_from_string(json_str)
            self.load_dtn_tvg_plan(data, simulation_end_time, default_datarate,
                                   default_delay)

    @staticmethod
    def _load_json_from_file(file):
        """Read the topology json information from a file.

        Args:
            file (str): The path/filename description of the loaded file.

        Returns:
            data: A json object (i.e. dictionary)

        """
        # Open the file and load it using the JSON module
        with open(file) as fds:
            data = json.load(fds)

        return data

    @staticmethod
    def _load_json_from_string(string):
        """Read the topology json information from a string.

        Args:
            string (str): The string containing the unparsed json information.

        Returns:
            data: A json object (i.e. dictionary)

        """
        # Open the file and load it using the JSON module
        data = json.loads(string)

        return data

    def load_dtn_tvg_plan(self,
                          data,
                          simulation_end_time,
                          datarate=None,
                          delay=None):
        """Load contact plan information from a JSON source file.

        Will only succeed if the JSON source file has a syntax that is
        supported and that can be validated.

        Args:
            data (dict): The parsed json data as dictionary.
            datarate (type): Datarate that should be used for contacts where
                no datarate is specified. Defaults to None. If no datarate is
                provided but datarate is required, the default_datarate of the
                object is used.
            delay (type): Delay that should be used for contacts where
                no delay is specified. Defaults to None. If no delay is
                provided but delay is required, the default_delay of the
                object is used.
            simulation_end_time (int): The time in ms when the simulation
                should end. Contacts in the source file that are starting after
                that time are ignored and contacts that end after the time
                are shortened.

        Raises:
            FileNotFoundError: If the file specified in the
                ``json_source_file`` argument could not be found.
            ValidationError: If the file specified in the ``json_source_file``
                argument could not be loaded because it did not adhere to any
                of the supported JSON formats.
            SystemError: If the default delay is set to 0. This can cause
                infinite loops.

        """
        # Try to validate the loaded JSON data using the legacy JSON scheme.
        validation_legacy = True
        try:
            validate(data, LEGACY_TVG_SCHEMA)
        except ValidationError:
            validation_legacy = False

        # Try to validate the loaded JSON data using the newer JSON scheme.
        validation_new = True
        try:
            validate(data, TVG_SCHEMA)
        except ValidationError:
            validation_new = False

        # Use default values if no values have been provided
        if datarate is None:
            datarate = self.default_datarate
        if delay is None:
            delay = self.default_delay

        # Parse the JSON data based on the outcome of the validations
        if not validation_new and not validation_legacy:
            raise ValidationError("The provided JSON file did not adhere to " +
                                  "any of the supported JSON schemes!")
        elif validation_new:
            self.__add_dtn_tvg_data(data, simulation_end_time)
        else:
            self.__add_legacy_dtn_tvg_data(data, simulation_end_time, datarate,
                                           delay)

        self._set_gs_status(data)

    def __add_legacy_dtn_tvg_data(self,
                                  data,
                                  simulation_end_time,
                                  datarate=None,
                                  delay=None):
        """Add information from the json_source_file to the contact plan.

        This function does not override already existing contact plan
        information but rather adds the data found in the file.

        This function validates the syntax of the JSON source file and aborts
        if the file is not adhering to the expected syntax. Please refer
        to the DTN_TVG_TOOLS documentation for syntax details.

        .. note::

            Contacts in the TVG-DTN-Tools JSON representation are always
            considered bidirectional, thus one contact object in JSON is
            considered as a contact for both involved nodes.

        Args:
            data (dict): Data loaded from the legacy JSON source file.
            datarate (int): The contact datarate in bit/sec that is for all
                contacts specified in json_source_file (the JSON representation
                 currently has no such information included).
            delay (int): The default transimission delay in ms for all
                contacts specified in json_source_file (the JSON representation
                currently has no such information included).
            simulation_end_time (int): The time in ms when the simulation
                should end. Contacts in the source file that are starting after
                that time are ignored and contacts that end after the time
                are shortened.

        """
        # Add vertices (nodes) to plan
        for node in data['vertices']:
            self.plan['nodes'].append(node)

        # Add edges (contacts) to plan. Implemented as a list because we also
        # want to allow multiple identical contacts between nodes
        for edge in data['edges']:
            for contact in edge['contacts']:
                # Convert str/float second time values to int milliseconds
                from_time = int(float(contact[0]) * 1000)
                to_time = int(float(contact[1]) * 1000)

                # Check if a simulation end time is set, if that is the case
                # ignore all contacts that start after that end time
                if from_time >= simulation_end_time:
                    continue
                # If a contact starts before the end time but ends after the
                # end time, set the end time to the end of the simulation
                # to prevent packets from being scheduled for the time after
                # the simulation has ended.
                elif to_time > simulation_end_time:
                    to_time = simulation_end_time

                contact1 = ContactIdentifier(
                    from_node=edge['vertices'][0],
                    to_node=edge['vertices'][1],
                    from_time=from_time,
                    to_time=to_time,
                    datarate=datarate,
                    delay=delay)
                contact2 = ContactIdentifier(
                    from_node=edge['vertices'][1],
                    to_node=edge['vertices'][0],
                    from_time=from_time,
                    to_time=to_time,
                    datarate=datarate,
                    delay=delay)

                # Add two contacts (due to bidirectionality)
                self.plan['contacts'].append(contact1)
                self.plan['contacts'].append(contact2)

    def __add_dtn_tvg_data(self, data, simulation_end_time):
        """Add information from the json_source_file to the contact plan.

        This function does not override already existing contact plan
        information but rather adds the data found in the file.

        This function validates the syntax of the JSON source file and aborts
        if the file is not adhering to the expected syntax. Please refer
        to the DTN_TVG_TOOLS documentation for syntax details.

        .. note::

            Contacts in the DTN-TVG-UTIL JSON representation are always
            considered unidirectional!

        Args:
            data (dict): JSON data as dict that was loaded from the source
                file.
            simulation_end_time (int): The time in ms when the simulation
                should end. Contacts in the source file that are starting after
                that time are ignored and contacts that end after the time
                are shortened.

        Raises:
            FileNotFoundError: If the file specified in the `json_source_file`
                argument could not be found.

        """
        # Add vertices (nodes) to plan
        for node in data['vertices'].keys():
            self.plan['nodes'].append(node)

        # Add edges (contacts) to plan. Implemented as a list because we also
        # want to allow multiple identical contacts between nodes
        for edge in data['edges']:
            for contact in edge['contacts']:
                # Convert str/float second time values to int milliseconds
                from_time = int(round(float(contact[2]) * 1000))
                to_time = int(round(float(contact[3]) * 1000))

                # Check if a simulation end time is set, if that is the case
                # ignore all contacts that start after that end time
                if from_time >= simulation_end_time:
                    continue
                # If a contact starts before the end time but ends after the
                # end time, set the end time to the end of the simulation
                # to prevent packets from being scheduled for the time after
                # the simulation has ended.
                elif to_time > simulation_end_time:
                    to_time = simulation_end_time

                # Transform the PCP into a FCP by converting the capacity
                # predictions into a constant datarate (assuming that the
                # link can be fully utilized).
                datarate = int(
                    round(
                        contact[4][0][1] / (1000 * (contact[3] - contact[2]))))

                contact = ContactIdentifier(
                    from_node=contact[0],
                    to_node=contact[1],
                    from_time=from_time,
                    to_time=to_time,
                    datarate=datarate,
                    delay=contact[5])

                # Add two contacts (due to bidirectionality)
                self.plan['contacts'].append(contact)

    def _set_gs_status(self, data):
        """Extract the type of groundstations from the json source file.

        If this information is not available, do not set the variables (they
        remain set to None).

        Args:
            data (dict): Data loaded from the legacy JSON source file.

        """
        if 'hotspots' in data:
            # Extract the hotspots from the source file
            self.hotspots = data['hotspots']
            # All gs that are not in the hotspots list are coldspots
            self.coldspots = [
                node for node in self.get_groundstations()
                if node not in self.hotspots
            ]

    def get_nodes(self):
        """Return all nodes of the topology."""
        return self.plan['nodes']

    def get_groundstations(self, identifier="gs"):
        """Provide a list of all groundstations in the topology.

        Kwargs:
            identifier (str): The prefix that is identifying the ground station
                nodes. This defaults to "gs".
        """
        ground_stations = list()
        for node in self.plan['nodes']:
            if node[:len(identifier)] == identifier:
                ground_stations.append(node)
        return ground_stations

    def get_outbound_contacts_of_node(self, node):
        """Provide a list of all contacts for a certain originating node.

        Args:
           node (str): The node identifier.

        Return:
           list: Returns the list of contact for the specified node.
        """
        contacts = list()
        for contact in self.plan['contacts']:
            # Check if source node of contact equals the argument
            if contact[0] == node:
                contacts.append(contact)
        return contacts

    def get_contacts(self):
        """Provide a list of all contacts.

        Return:
           list: Returns the list of all contacts of the contact plan.
        """
        return self.plan['contacts']

    def add_contact(self,
                    node_1,
                    node_2,
                    start_time,
                    end_time,
                    datarate=None,
                    delay=None,
                    bidirectional=True):
        """Add a single contact to the ContactPlan object.

        .. note::

            This function does not verify if a contact corresponding to the
            provided arguments already exists. This check is not intended as
            one might want to add multiple conacts with simular characteristic
            values.

        Args:
            node_1 (str): The identifier of the first involved node. If
                ``bidirectional`` is set to False, this argument specifies the
                source node of the added contact.
            node_2 (str): The identifier of the second involved node. If
                ``bidirectional`` is set to False, this argument specifies the
                destination node of the added contact.
            start_time (int): The start time of the contact in ms.
            end_time (int): The end time of the contact in ms.
            datarate (int): The datarate of the contact in bits/ms. The
                default value of the ContactPlan object is used when no
                datarate is provided.
            delay (int): The transmission delay for transferring data during
                the added contact in ms. The default value of the
                ContactPlan object is used when no delay is provided.
            bidirectional (bool): Specifies whether the added contact should
                be considered bidirectional, i.e. if a second counterpart
                contact should be added.

        Raises:
            SystemError: If the default delay is set to 0. This can cause
                infinite loops.

        """
        # Check, if datarate was specified, otherwas use the default value
        if datarate is None:
            datarate = self.default_datarate

        # Check, if delay was specified, otherwas use the default value
        if delay is None:
            delay = self.default_delay

        # Create named tuple contact object
        contact = ContactIdentifier(
            from_node=node_1,
            to_node=node_2,
            from_time=start_time,
            to_time=end_time,
            datarate=datarate,
            delay=delay)
        # Add contact to contacts list
        self.plan['contacts'].append(contact)

        # If contact is considered bidirectional, also add the counterpart
        # contact
        if bidirectional:
            contact2 = ContactIdentifier(
                from_node=node_2,
                to_node=node_1,
                from_time=start_time,
                to_time=end_time,
                datarate=datarate,
                delay=delay)
            self.plan['contacts'].append(contact2)

        # Add the nodes to the nodes list (if not already present)
        if node_1 not in self.plan['nodes']:
            self.plan['nodes'].append(node_1)
        if node_2 not in self.plan['nodes']:
            self.plan['nodes'].append(node_2)

    def add_node(self, node):
        """Add a node to the contact plan.

        Based on this function call, this node is not connected to any other
        node. However, if the node was already present in the contact plan
        before, the possible previously added contacts will remain valid after
        this function call.
        """
        if node not in self.plan['nodes']:
            self.plan['nodes'].append(node)

    def clear(self):
        """Delete and reinitialize the internal contact plan representation."""
        # Delete the current information
        del self.plan
        # Reinitialize the internal representation of the contact plan
        self.plan = OrderedDict()
        self.plan['nodes'] = list()
        self.plan['contacts'] = list()

    def get_networx_topology_graph(self):
        """Provide contact graph as :mod:`networkx` :class:`DiGraph`."""
        # Create empty DiGraph object
        graph = nx.DiGraph()

        # Add all nodes in the topology to the graph
        for node in self.plan['nodes']:
            graph.add_node(node)

        # Add edges between the contact nodes
        for contact in self.plan['contacts']:
            graph.add_edge(contact.from_node, contact.to_node)

        # Return graph
        return graph
