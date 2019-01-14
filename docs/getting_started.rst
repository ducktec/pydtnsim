.. _getting_started:

Getting started with pyDTNsim
=============================

With *pyDTNsim* installed, we can start with running simulations using the library. In this section, a hands-on introduction into the features and the instrumentation procedure of the library module will be provided.

The goal of this introduction is to simulate the simple intermittently connected network topology as depicted below and to generate key characteristics of this simulation run.

Simulation Scenario
-------------------

The following network topology shall be simulated for 1000 seconds:

.. image:: resources/getting_started/topology.svg
   :width: 100%
   
The annotations at the arrows represent available contact between the two (physical) network nodes that an arrow is connecting in `mathematical interval notation <https://en.wikipedia.org/wiki/Interval_(mathematics)#Including_or_excluding_endpoints>`_ in seconds. All contacts are considered to allow for a transmission of data with 100 KBps.
   
.. note:: The propagation delays are considered neglible in this scenario. This is in line with the current configuration of *pyDTNsim* which is not supporting (individual or global) delays at the moment.

The nodes ``A`` and ``C`` are representing *"active"* endpoints which are both continuously inserting packets of 100 KB with a data generation rate of 10 KBps, addressed at node ``A`` and ``C`` respectively. The data generation will continue throughout the entire simulation period.

Node ``B`` is functioning as intermediary node that is solely forwarding packets received from ``A`` and ``B``. It is neither the destination of any packets nor is it injecting any packets.

*Contact Graph Routing (CGR)* will be used as routing mechanism. See :ref:`routing_mechanisms` for more details on provided mechanisms and their implementation.

The characteristics that should be acquired with the simulation run are 

- the overall **average delivery time** of all delivered packets during the simulation run, 
- the **number of packets** enqueued into the **limbo** (i.e., packets that could not be scheduled for transmission with CGR) and
- a **histogram** of the **average delivery time** of all delivered packets throughout the simulation run.

Creating a simulation script
----------------------------
As *pyDTNsim* is a library module, we have to create a simulation script ourselves to leverage the invoke the module's functionality.

Just create a new python script file with your favorite editor or type

.. code-block:: sh

  touch dtn_simulation.py
  vim dtn_simulation.py
  
With the script created, we can now start to import the libraries components. We start with creating a :class:`pydtnsim.simulator.Simulator` object. This object represents the event-oriented simulation environment that keeps track of the simulations components and is later invoked for the actual simulation run. Details about the abstract concept of the simulation environment can be found in :doc:`architecture`.

The :class:`Simulator` can then be used to perform a simulation using it's member function :py:meth:`.Simulator.run_simulation`. For now, it is sufficient to provide this function with the simulation duration in milliseconds. It will then run a simulation from 0 ms to that provided parameter.

The following code snippet shows the most basic simulation script using the :class:`.Simulator` class. Please add this snippet to your script file.



.. code-block:: python

  from pydtnsim import Simulator
  
  def main():
      """Simulate basic scenario."""
      # Create simulation environment
      simulator = Simulator()

      # Run the simulation for 1000 seconds (1000000 ms)
      simulator.run_simulation(1000000)

  if __name__ == "__main__":
      main()
      
As no nodes or contacts were added to the :class:`.Simulator` object, nothing has to be simulated. When running the script, the output is as follows:

.. code-block:: none
  :linenos:

  > python3 dtn_simulation.py 
    Running simulation  for 1000000 ms ...
    Simulation completed!
    Simulation Results:
    - total number of packets generated: 0
    - total number of packets enqueued in limbos: 0
    - total number of packets enqueued in contacts: 0
    
Hooray, that was the first "successful" pyDTNsim simulation run! We didn't actually simulate any network but we can change that by adding simulation elements in the next step.

But first, let's have a look at the output provided by the :class:`.Simulator` object: besides the message that the simulation was completed the output also provides some simple statistics about the performed simulation run in lines *(5-7)*. In our case, no packets were generated and subsequently, no packets remained in limbos or contacts at the end of the simulation run.


Adding simulation elements
--------------------------

In order to not just simulate empty scenarios, we now have to add (active and passive) simulation elements to the simulation environment. In particular, two elements have to be represented in the environment: physical network nodes (e.g., :class:`.SimpleCGRNode`) and contacts in between those nodes (:class:`.Contact`).

.. note::

	Both classes/objects referenced in the paragraph above are exemplary. Depending on the simulated routing mechanisms, the instantiated network node objects have to vary (and might even have to be implemented oneself for novel routing concepts). An opportunistic routing approach might have differing processing requirements both in terms of gathered knowledge at the physical nodes and the forwarding behavior during node contacts.
  
.. warning::

	With the development focus of this simulation environment having been CGR, the generalization in terms of applicable routing mechanisms has not been fully implemented in this area of the application. For now, only CGR implementations are provided and no abstract parent class exists for the easy adoption with other routing approaches. This improvement will likely be implemented in the near future.
  
For the simulation elements including their helper classes, we need to add the following imports:

.. code-block:: python

    from pydtnsim import ContactPlan, ContactGraph, Contact
    from pydtnsim.nodes import SimpleCGRNode
    from pydtnsim.routing import cgr_basic
    
The imported objects will be explained in the following paragraphs.
  
Network Topology
^^^^^^^^^^^^^^^^

As the network node need to be aware about the network topology since we are using :abbr:`CGR (Contact Graph Routing)` as routing mechanism, we have to provide such information during the instantiation.

We provide the topology knowledge as a :class:`.ContactGraph` object. This object represents the topology as a time-invariant graph and can be easily generated from a :class:`.ContactPlan` object. This object holds the same information as the :class:`.ContactGraph`, but is easier to understand and modify for humans. More details on the reasoning behind the :class:`.ContactPlan` and the :class:`.ContactGraph` in the context of :abbr:`CGR (Contact Graph Routing)` is provided in :doc:`routing/cgr`.

As outlined before, we first create the :class:`.ContactPlan` (line 2). The parameters provided during the instantiation are the default data rate in bits per millisecond (10 bits per millisecond, i.e. 10 KBps) and the default propagation delay in milliseconds (50 ms).

.. warning::

  The propagation delay is currently not factored in when simulating networks. The interface for providing such information is already implemented, but the simulation logic is not implemented yet. This is future work, so for now, the propagation delay is always neglected.

.. code-block:: python
    :linenos:

    # Generate empty contact plan
    contact_plan = ContactPlan(10, 50)

    # Add the contacts
    contact_plan.add_contact('node_a', 'node_b', 0, 100000)
    contact_plan.add_contact('node_a', 'node_b', 500000, 750000)
    contact_plan.add_contact('node_b', 'node_c', 0, 200000)
    contact_plan.add_contact('node_b', 'node_c', 350000, 400000)
    contact_plan.add_contact('node_b', 'node_c', 950000, 990000)
    
In lines 5 to 9, the contacts based on our previously outlined scenario are added to the ``contact_plan`` object using :py:meth:`.ContactPlan.add_contact`. The parameters are 

- the source node, 
- the destination node, 
- the start time in milliseconds and 
- the end time in milliseconds.

As no additional optional parameters for the data rate and the delay were provided, the default values of the ``contact_plan`` object are used.

Finally, we can simply convert the filled :class:`.ContactPlan` object into a :class:`.ContactGraph` object:

.. code-block:: python

    # Convert contact plan to contact graph
    contact_graph = ContactGraph(contact_plan)
    
Contacts
^^^^^^^^

The contacts available in between network nodes throughout the simulation are simulated using the :class:`.Contact` object. These objects are an integral part of the simulation environment as they are one of two active **generator** elements that drive the simulation (and generate events, hence the name). Contacts are activated upon their contact start time and then perform handover operations from one node to another during their time active. At the end of a handover of a packet to another node, the routing mechanism on that other node is called to determine the future forwarding.

With the information about the contacts already being available in the ``contact_plan`` object of the previous step, we can iterate over that information to generate our :class:`.Contact` objects:

.. code-block:: python
    :linenos:

    # Generate contact objects and register them
    for planned_contact in contact_plan.get_contacts():
        # Create a Contact simulation object based on the ContactPlan
        # information
        contact = Contact(planned_contact.from_time, planned_contact.to_time,
                          planned_contact.datarate, planned_contact.from_node,
                          planned_contact.to_node, planned_contact.delay)
        # Register the contact as a generator object in the simulation
        # environment
        simulator.register_contact(contact)
        
In addition to the instantiation of the contacts in lines 5 to 7, in line 10, the respective contact also has to be registered with the simulation environment. This is to allow the simulation environment to call the contact upon its start time.


Network Nodes
^^^^^^^^^^^^^

With the topology information available in the correct format, we can add the network nodes. For all three nodes, we will use :class:`.SimpleCGRNode` as representation in the simulation environment. Again, we can use the `contact_plan` object that we instantiated and filled earlier to gather the relevant information for the instantiation: 

.. code-block:: python
    :linenos:     
 
    # Generate network node objects and register them
    for planned_node in contact_plan.get_nodes():
        # Generate contact list of node
        contact_list = contact_plan.get_outbound_contacts_of_node(planned_node)
        # Create a dict that maps the contact identifiers to Contact simulation
        # objects
        contact_dict = simulator.get_contact_dict(contact_list)
        # Create a node simulation object
        SimpleCGRNode(planned_node, contact_dict, cgr_basic.cgr, contact_graph,
                      simulator, [])

In line 2, we get a list of all network nodes in the topology using :py:meth:`.ContactPlan.get_nodes`. We then iterate over this list and create the individual nodes:

1. We first have to get a list of all outbound nodes that the individual 
   network node has. This is done calling 
   :py:meth:`.ContactPlan.get_outbound_contacts_of_node`.
2. This list is then used to get a ``contact_dict`` from the 
   :class:`.Simulator` object. As this object is aware of all contacts and 
   their registered instantiations, it can map the textual list entries of the 
   outbound contacts from the previous step to actual :class:`.Contact` 
   objects. So by calling :py:meth:`.Simulator.get_contact_dict`, we get a 
   ``dict`` mapping a contacts identifier to the instantiation in the 
   simulation context. 
3. With the ``contact_dict`` available, we can instantiate the actual network 
   node object as :class:`.SimpleCGRNode` with the following parameters:

    - the node identifier (e.g. ``node_a``), 
    - the ``contact_dict``, 
    - the routing mechanism's main function ``cgr_basic.cgr``, 
    - the topology information (in this case as :class:`.ContactGraph` object) 
      and 
    - the :class:`.Simulator` object.
    
Packet Generators
^^^^^^^^^^^^^^^^^

Finally, we have to add packet generators that are injecting packets into the simulated network. Without them, regardless of the specified topology, no packets would be forwarded and thus, no non-trivial network behavior would be simulated.

Currently, there two different packet generators provided in the simulation environment, the :class:`.BatchPacketGenerator` and the :class:`.ContinuousPacketGenerator`. Both are children of the parent :class:`.BasePacketGenerator`.

The injection behavior of the two generators is depicted in the following figures:

.. image:: resources/getting_started/injection_methods.svg
   :width: 80%
   :align: center
   
The :class:`.BatchPacketGenerator` injects a specified number of packets at specified points in time whereas the :class:`.ContinuousPacketGenerator` injects packets continuously throughout the simulation period with a defined generation data rate.

Depending on the scenario, one of them might be used for the simulation conducted. Alternatively, an own generator can be implemented based on the :class:`.BasePacketGenerator`.

Monitoring of the Simulation
----------------------------

Running a Simulation
--------------------

Post Processing and Evaluation
------------------------------
