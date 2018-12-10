""" Testfile for the contactplan.py implementations """
from collections import OrderedDict
import math
import logging
import pytest
from jsonschema import ValidationError

from pydtnsim import ContactPlan


def test_create_contactplan_object():
    # Create contact plan object
    cp = ContactPlan(1000.1, 42.42)

    # Verify that both the datarate and the delay are properly set
    assert cp.default_datarate == 1000.1
    assert cp.default_delay == 42.42

    # Verify that plan object was initialized properly
    assert type(cp.plan) is OrderedDict
    assert type(cp.plan['nodes']) is list
    assert type(cp.plan['contacts']) is list

    # Create contact plan object
    cp = ContactPlan(100, 2)

    # Verify that both the datarate and the delay are properly set
    assert cp.default_datarate == 100.0
    assert cp.default_delay == 2.0


def test_add_node():
    # Create contact plan object
    cp = ContactPlan(1000.1, 42.42)

    # Add node
    cp.add_node('testnode')

    # Check that new node is in node set
    assert 'testnode' in cp.plan['nodes']
    assert len(cp.plan['nodes']) == 1

    # Add node again
    cp.add_node('testnode')

    # Check that new node is in the set only once
    assert 'testnode' in cp.plan['nodes']
    assert len(cp.plan['nodes']) == 1


def test_add_contact():
    # Create contact plan object
    cp = ContactPlan(1000.1, 42.42)

    # Add contact to cp object
    cp.add_contact('node1', 'node2', 0.0, 12.2)

    # Verify that the two contacts (with the default datarate and default delay) were added properly
    assert ('node1', 'node2', 0.0, 12.2, 1000.1, 42.42) in cp.plan['contacts']
    assert ('node2', 'node1', 0.0, 12.2, 1000.1, 42.42) in cp.plan['contacts']
    assert len(cp.plan['contacts']) == 2

    # Add unidirectional contact
    cp.add_contact('node3', 'node4', 0.1, 13.4, bidirectional=False)

    # Verify that the one contact was added properly
    assert ('node3', 'node4', 0.1, 13.4, 1000.1, 42.42) in cp.plan['contacts']
    assert len(cp.plan['contacts']) == 3

    # Use specific values for datarate and delay
    cp.add_contact('node1', 'node2', 0.0, 12.2, delay=4.2)
    cp.add_contact('node1', 'node2', 0.0, 12.2, datarate=1004.2)
    cp.add_contact('node1', 'node2', 0.0, 12.2, delay=12.4, datarate=1004.2)
    cp.add_contact('node5', 'node6', 0.0, 12.2, delay=4.2, bidirectional=False)

    # Check that the added contacts are part of the cp
    assert ('node1', 'node2', 0.0, 12.2, 1000.1, 42.42) in cp.plan['contacts']
    assert ('node2', 'node1', 0.0, 12.2, 1000.1, 42.42) in cp.plan['contacts']
    assert ('node1', 'node2', 0.0, 12.2, 1004.2, 42.42) in cp.plan['contacts']
    assert ('node2', 'node1', 0.0, 12.2, 1004.2, 42.42) in cp.plan['contacts']
    assert ('node5', 'node6', 0.0, 12.2, 1000.1, 4.2) in cp.plan['contacts']
    assert ('node6', 'node5', 0.0, 12.2, 1000.1,
            4.2) not in cp.plan['contacts']

    # Check if all nodes were properly added to the contactplan node list
    assert ['node1', 'node2', 'node3', 'node4', 'node5',
            'node6'] == cp.plan['nodes']


def test_get_nodes():
    # Create contact plan object
    cp = ContactPlan(1000.1, 42.42)

    # Add nodes and contacts (both resulting in adding nodes to set)
    cp.add_node('testnode1')
    cp.add_contact('testnode2', 'testnode3', 0.0, 1.0)

    # Verify that all nodes were added properly
    assert cp.get_nodes() == ['testnode1', 'testnode2', 'testnode3']


def test_get_outbound_contacts_of_node():
    # Create contact plan object
    cp = ContactPlan(1000.1, 42.42)

    # Add nodes and contacts (both resulting in adding nodes to set)
    cp.add_node('testnode1')
    cp.add_contact('testnode2', 'testnode3', 0.0, 1.0)
    cp.add_contact('testnode2', 'testnode3', 0.0, 1.0)
    cp.add_contact('testnode2', 'testnode3', 10.0, 11.0, bidirectional=False)

    # Verify that all contacts are returned properly
    assert cp.get_outbound_contacts_of_node('testnode1') == []
    assert cp.get_outbound_contacts_of_node('testnode2') == [
        ('testnode2', 'testnode3', 0.0, 1.0, 1000.1, 42.42),
        ('testnode2', 'testnode3', 0.0, 1.0, 1000.1, 42.42),
        ('testnode2', 'testnode3', 10.0, 11.0, 1000.1, 42.42)
    ]
    assert cp.get_outbound_contacts_of_node('testnode3') == [
        ('testnode3', 'testnode2', 0.0, 1.0, 1000.1, 42.42),
        ('testnode3', 'testnode2', 0.0, 1.0, 1000.1, 42.42)
    ]


def test_get_groundstations():
    # Create contact plan object
    cp = ContactPlan(1000.1, 42.42)

    # Add nodes
    cp.plan['nodes'].append('gs12')
    cp.plan['nodes'].append('sat1')
    cp.plan['nodes'].append('groundstation3')

    # Check that only matching nodes are returned
    assert cp.get_groundstations() == ['gs12']
    assert cp.get_groundstations('groundstation') == ['groundstation3']


def test_clear():
    # Create contact plan object
    cp = ContactPlan(1000.1, 42.42)

    # Add nodes and contacts (both resulting in adding nodes to set)
    cp.add_node('testnode1')
    cp.add_contact('testnode2', 'testnode3', 0.0, 1.0)

    cp.clear()

    assert cp.plan['nodes'] == list()
    assert cp.plan['contacts'] == []
    assert cp.default_delay == 42.42
    assert cp.default_datarate == 1000.1


def test_load_route_list():
    # Create contact plan object
    cp = ContactPlan(1, 42)

    # Check if exception is thrown if file does not exist
    with pytest.raises(FileNotFoundError):
        cp = ContactPlan(1, 42, 'tests/resources/not_existing_file.json')

    # Check if exception is thrown if invalid file is loaded
    with pytest.raises(ValidationError):
        cp = ContactPlan(1, 42, 'tests/resources/tvg_invalid_file.json')

    # Load a valid contact plan from the file
    cp = ContactPlan(1, 42, 'tests/resources/tvg_valid_file.json')

    assert ['node1', 'node2', 'node3'] == cp.plan['nodes']
    assert ('node1', 'node2', 0, 10000, 1, 42) in cp.plan['contacts']
    assert ('node2', 'node1', 0, 10000, 1, 42) in cp.plan['contacts']
    assert ('node1', 'node2', 20000, 30000, 1, 42) in cp.plan['contacts']
    assert ('node2', 'node1', 20000, 30000, 1, 42) in cp.plan['contacts']
    assert ('node2', 'node3', 30000, 40000, 1, 42) in cp.plan['contacts']
    assert ('node3', 'node2', 30000, 40000, 1, 42) in cp.plan['contacts']

    # Load a valid contact plan with custom datarate and delay from the file
    cp2 = ContactPlan(1, 100, 'tests/resources/tvg_valid_file.json')

    assert ['node1', 'node2', 'node3'] == cp2.plan['nodes']
    assert ('node1', 'node2', 0, 10000, 1, 100) in cp2.plan['contacts']
    assert ('node2', 'node1', 0, 10000, 1, 100) in cp2.plan['contacts']
    assert ('node1', 'node2', 20000, 30000, 1, 100) in cp2.plan['contacts']
    assert ('node2', 'node1', 20000, 30000, 1, 100) in cp2.plan['contacts']
    assert ('node2', 'node3', 30000, 40000, 1, 100) in cp2.plan['contacts']
    assert ('node3', 'node2', 30000, 40000, 1, 100) in cp2.plan['contacts']

    # Load a valid contact plan with custom datarate and delay from the file
    cp3 = ContactPlan(1, 42, 'tests/resources/03_tvg.json')

    assert 'NANOSATC-BR1' in cp3.plan['nodes']
    assert 'gs0' in cp3.plan['nodes']
    assert 'gs1' in cp3.plan['nodes']
