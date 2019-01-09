"""Minimal Simulation Example."""

from pydtnsim import Simulator, ContactPlan, ContactGraph, Contact
from pydtnsim.nodes import SimpleCGRNode
from pydtnsim.packet_generators import BatchPacketGenerator

from pydtnsim.routing import cgr_basic


def main():
    """Simulate basic scenario."""
    # Create simulation environment
    simulator = Simulator()

    # Run the simulation for 1000 seconds (1000000 ms)
    simulator.run_simulation(1000000)


if __name__ == "__main__":
    main()
