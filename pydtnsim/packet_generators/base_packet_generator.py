"""Contains the BasePacketGenerator base class.

The BasePacketGenerator registers as generator with the simulation environment
and is invoked by the the environment during the simulation runtime.

Child objects can specify a generator behaviour on how, where and when packets
are injected into the simulated network.
"""


class BasePacketGenerator:
    """Packet Generator parent object."""

    def __init__(self):
        """Instantiate the BasePacketGenerator object."""
        self.packet_count = 0
        self.rid = 0
        self.simulator = None

    def run(self):
        """Simulator generator stub function."""

    def get_packet_count(self):
        """Return the number of injected packets (up until the function call).

        Returns:
            int: Number of packets injected by this generator.

        """
        return self.packet_count

    def register_simulator(self, simulator):
        """Register a packet generator in a specific simulation environment.

        Args:
            simulator (pydtnsim.Simulator): The generator to be registered.

        """
        self.simulator = simulator
        self.rid = simulator.env.register_runner(self.run)
