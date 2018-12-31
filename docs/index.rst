.. pyDTNsim documentation master file, created by
   sphinx-quickstart on Tue Dec 11 18:24:57 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyDTNsim - a DTN simulation environment
=======================================

*pyDTNsim* provides a simulation environment that allows the simulation of arbitrary Delay Tolerant Networking (DTN) scenarios on a packet level. *pyDTNsim* provides users with the ability to evaluate the performance of various routing approaches and to detect possibly occurring overload situations. Currently, the focus lies on deterministic Contact-Graph-based routing approaches, but there might be other approaches available in the future. The clear modularization allows users to easily implement routing approaches on their own.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   install
   getting_started
   examples
   scenario_setup
   routing/index
   monitoring
   data_processing
   
.. toctree::
  :maxdepth: 2
  :caption: Development Guide

  architecture
  development_guide

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :ref:`glossary`
