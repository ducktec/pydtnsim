"""Collection of packet generators for the pydtnsim simulation.

Currently, only one generator exists that generates packets continuously with
a specific data rate and packet size.

There will be more generators added in the future.
"""

from .base_packet_generator import BasePacketGenerator
from .continuous_packet_generator import ContinuousPacketGenerator
from .batch_packet_generator import BatchPacketGenerator
