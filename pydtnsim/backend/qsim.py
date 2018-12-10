"""Implementation a simulation backend for running event-based simulations."""

import heapq
import math


class QSim():
    """(Q)uick discrete event-based (Sim)ulator."""

    def __init__(self):
        """Initialize a new QSim object, i.e. a new simulation environment."""
        self.runner_count = 0
        self.event_queue = list()
        self.now = 0
        self.event_id = 0

    def register_runner(self, runner):
        """Register a runner with the simulation environment.

        Args:
            runner (func): The runner function that should be called upon
                simulation start.

        Returns:
            int: The (numeric) environment identifier for the runner.

        """
        # Save current id for returning, then increase the counter
        identifier = self.runner_count
        self.runner_count += 1

        # Register start event
        self.register_event(0, identifier, runner)

        # Return the runners identifier
        return identifier

    def register_event(self, time, runner_id, function_call, arg=None):
        """Register an event that is calling a function at the given time.

        Args:
            time (int): The callback time in ms.
            runner_id (int): The id of the runner registering the event. We
                trust the runners to provide the correct id for performance
                reasons. Determining the id with an intenal lookup is
                unnecessary overhead.
            function_call (func): The callback function called when the
                event is due.
            arg (optional): An optional parameter for the callback function.
                Defaults to None.

        Raises:
            SystemError: If a second entrie for the same time and runner id
                is created.

        """
        # Get an unique event identifier
        eid = self.event_id
        self.event_id += 1
        # Put the event into the internal event queue to call it when it
        # is due.
        try:
            heapq.heappush(self.event_queue,
                           (time, runner_id, eid, function_call, arg))
        except TypeError:
            raise SystemError("Time and runner_id were matching! " +
                              "Aborting! Only one entry per time and " +
                              "runner_id allowed.")

    def run_simulation(self, until=math.inf):
        """Run the simulation (until a certain point in time).

        Args:
            until (int): The time until the simulation should be run.

        """
        while self.event_queue:
            # Extract the next event from the event queue
            time, rid, eid, function_call, arg = heapq.heappop(
                self.event_queue)
            # Set the current time to the extracted time, we are simulating
            # that time now.
            self.now = time

            # If the next event lies beyond the until parameter, put it
            # back into the queue and return
            if time > until:
                heapq.heappush(self.event_queue,
                               (time, rid, eid, function_call, arg))
                return

            # Call the function with the optional argument if it exists
            if arg is None:
                function_call()
            else:
                function_call(arg)
