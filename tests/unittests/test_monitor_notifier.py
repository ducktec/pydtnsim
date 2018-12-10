"""Unit test for the monitor notifier implementation."""

import pytest
from pydtnsim.monitors import BaseMonitor, MonitorNotifier
from pydtnsim.backend import QSim


class Monitor(BaseMonitor):
    """Monitor object inheriting from BaseMonitor."""

    def __init__(self, env):
        """Initialize."""
        self.was_called = False
        super(Monitor, self).__init__(env)

    # Implement a callback method
    def packet_routed(self, packet, node, route, best_route, time):
        """Test callback functionality."""
        self.was_called = True


def test_add_subscriber():
    """Test subscribing functionality."""
    # Create environment
    env = QSim()
    # Create MonitorNotifier
    notifier = MonitorNotifier(env)
    # Create Monitor
    monitor = Monitor(env)

    notifier.add_subscriber(monitor)
    assert len(notifier.subscribers) == 1

    # We try to add the monitor, which is already subscribed.
    notifier.add_subscriber(monitor)

    # We check that the first proper subscriber is still present once again
    assert len(notifier.subscribers) == 1


def test_remove_subscriber():
    """Test unsubscribing functionality."""
    # Create environment
    env = QSim()
    # Create MonitorNotifier
    notifier = MonitorNotifier(env)
    # Create Monitor
    monitor = Monitor(env)

    # First, we add the proper monitor
    notifier.add_subscriber(monitor)

    # We then try to remove a monitor, which was never added.
    notifier.remove_subscriber(object())

    # We check that the first proper subscriber is still present once again
    assert len(notifier.subscribers) == 1

    # We remove the proper monitor and check that it was removed
    notifier.remove_subscriber(monitor)
    assert len(notifier.subscribers) == 0

    # We try to remove the proper monitor, which was already removed.
    notifier.remove_subscriber(monitor)

    # We check that the subscribers list is still empty.
    assert len(notifier.subscribers) == 0


def test_callback():
    """Test callback functionality."""
    # Create environment
    env = QSim()
    # Create MonitorNotifier
    notifier = MonitorNotifier(env)
    # Create proper and faulty Monitor
    monitor = Monitor(env)

    # First, we add the proper monitor
    notifier.subscribers.append(monitor)

    packet = 0
    notifier.packet_routed(packet, None, None, None, 0)

    # Make sure that callback function of subscribed object was called
    assert monitor.was_called
