""" Testfile for the contact_graph.py implementations """
from collections import OrderedDict
import logging
import pytest
import math
from jsonschema import ValidationError

from pydtnsim import ContactGraph, ContactIdentifier, ContactPlan


def test_create_empty_graph():
    graph = ContactGraph()

    assert type(graph) == ContactGraph
    assert type(graph.graph) == OrderedDict

    assert not graph.graph


def test_add_contact_node():
    graph = ContactGraph()

    identifier = ('a', 'b', 0.0, 10.0, 1000.0, 0.0)
    # Check if exception is thrown if invalid identifier is used
    with pytest.raises(ValueError):
        graph.add_contact_node(identifier)

    identifier1 = ContactIdentifier(
        from_node='a',
        to_node='b',
        from_time=0.0,
        to_time=10.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier1)

    assert len(graph.graph) == 1

    identifier2 = ContactIdentifier(
        from_node='b',
        to_node='c',
        from_time=10.0,
        to_time=20.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier2)

    identifier3 = ContactIdentifier(
        from_node='d',
        to_node='c',
        from_time=10.0,
        to_time=20.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier3)

    # Check that the added nodes are properly connected
    # (predecessors and successors)
    assert len(graph.graph) == 3
    assert identifier2 in graph.graph[identifier1][0]
    assert len(graph.graph[identifier1][0]) == 1
    assert len(graph.graph[identifier1][1]) == 0
    assert identifier1 in graph.graph[identifier2][1]
    assert len(graph.graph[identifier2][1]) == 1
    assert len(graph.graph[identifier2][0]) == 0
    assert len(graph.graph[identifier3][0]) == 0
    assert len(graph.graph[identifier3][1]) == 0


def test_remove_contact_node():
    graph = ContactGraph()

    identifier1 = ContactIdentifier(
        from_node='a',
        to_node='b',
        from_time=0.0,
        to_time=10.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier1)
    identifier2 = ContactIdentifier(
        from_node='b',
        to_node='c',
        from_time=10.0,
        to_time=20.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier2)

    assert len(graph.graph) == 2

    identifier_false = ('a', 'b', 0.0, 10.0, 1000.0, 0.0)
    # Check if exception is thrown if invalid identifier is used
    with pytest.raises(ValueError):
        graph.remove_contact_node(identifier_false)

    assert len(graph.graph) == 2

    graph.remove_contact_node(identifier2)

    # Assert that node was removed properly and both the successor and
    # predecessor lists are empty
    assert len(graph.graph) == 1
    assert not graph.graph[identifier1][0]
    assert not graph.graph[identifier1][1]


def test_remove_toplogical_node():
    graph = ContactGraph()

    identifier1 = ContactIdentifier(
        from_node='a',
        to_node='b',
        from_time=0.0,
        to_time=10.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier1)
    identifier2 = ContactIdentifier(
        from_node='b',
        to_node='c',
        from_time=10.0,
        to_time=20.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier2)

    assert len(graph.graph) == 2

    graph.remove_topology_node('b')

    # Assert that all contacts related to 'b' were removed and the graph is
    # empty
    assert len(graph.graph) == 0


def test_reinitialize():
    graph = ContactGraph()

    identifier1 = ContactIdentifier(
        from_node='a',
        to_node='b',
        from_time=0.0,
        to_time=10.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier1)
    identifier2 = ContactIdentifier(
        from_node='b',
        to_node='c',
        from_time=10.0,
        to_time=20.0,
        datarate=1000.0,
        delay=0.0)
    graph.add_contact_node(identifier2)

    assert len(graph.graph) == 2

    graph.reinitialize()

    # Assert that all contacts related to 'b' were removed and the graph is
    # empty
    assert len(graph.graph) == 0


def test_create_from_contact_plan():
    plan = ContactPlan(1000, 0)

    plan.add_contact('a', 'b', 0.0, 10.0, 1000.0, 0.0, bidirectional=False)
    plan.add_contact('b', 'c', 0.0, 30.0, 1000.0, 0.0, bidirectional=False)
    plan.add_contact('a', 'c', 20.0, 30.0, 1000.0, 0.0, bidirectional=False)

    # Check if exception is thrown if invalid identifier is used
    with pytest.raises(ValueError):
        graph = ContactGraph([])

    graph = ContactGraph(plan)

    assert len(graph.graph) == 6

    id1 = ContactIdentifier('a', 'b', 0.0, 10.0, 1000.0, 0.0)
    id2 = ContactIdentifier('b', 'c', 0.0, 30.0, 1000.0, 0.0)
    id3 = ContactIdentifier('a', 'c', 20.0, 30.0, 1000.0, 0.0)

    assert id2 in graph.graph[id1][0]
    assert id1 in graph.graph[id2][1]
    assert len(graph.graph[id1][0]) == 2
    assert len(graph.graph[id1][1]) == 1
    assert len(graph.graph[id2][0]) == 1
    assert len(graph.graph[id2][1]) == 2
    assert len(graph.graph[id3][0]) == 1
    assert len(graph.graph[id3][1]) == 1

    # Verify number of root node vertices
    assert len(graph.graph[('a', 'a', 0, math.inf, math.inf, 0)][0]) == 2
    assert len(graph.graph[('b', 'b', 0, math.inf, math.inf, 0)][0]) == 1
    assert len(graph.graph[('c', 'c', 0, math.inf, math.inf, 0)][0]) == 0

    # Verify that vertice list of contact nodes contains vertices to correct
    # terminal nodes
    assert ('a', 'a', 0, math.inf, math.inf, 0) in graph.graph[id1][1]
    assert ('b', 'b', 0, math.inf, math.inf, 0) in graph.graph[id1][0]

    assert ('b', 'b', 0, math.inf, math.inf, 0) in graph.graph[id2][1]
    assert ('c', 'c', 0, math.inf, math.inf, 0) in graph.graph[id2][0]

    assert ('a', 'a', 0, math.inf, math.inf, 0) in graph.graph[id3][1]
    assert ('c', 'c', 0, math.inf, math.inf, 0) in graph.graph[id3][0]
