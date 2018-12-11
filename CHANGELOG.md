# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
-

## [0.1.0] - 2018-12-11
### Added 
- Added requirements.txt to allow for an easy dependency installation.

### Changed
- First public release version. Renamed project from `simpy-dtn` to `pydtnsim`.
- Adapted changelog and readme
- Switched to Travis CI .yml file (and removed gitlab CI file). The checks 
  performed during the CI runs are the same.
- Updated `setup.py` to load long description from `README.md` with common 
  function call

## Fixed
- Corrected and cleaned up dependencies, deleted requirements.txt, added
  version value ranges for dependencies

## [0.0.10] - 2018-12-07
### Added
- The `ContactPlan` object now allows for the loading of topology information 
  from Strings and not just only files. This allows for a loading of data 
  embedded in other file types than simple json files.
- The `SimpleCGRNode` is now provided with a list of the hotspots in the 
  topology (this change is scenario-specific, i.e. for the ring road scenario, 
  and might be removed in future versions).
- The `Simulator` in combination with the `Contacts` now keeps track of the 
  contact utilization.

### Changed
- Improved monitoring interface: The monitoring interface now allows for a 
  more fine-grained evaluation of occurring events. In particular, more 
  detailed parameters about routing decisions are provided to the registered 
  monitors.
- The internal forwarding handling of the `Packet` object, the implemented 
  routing mechanisms and the unit tests were modified to accommodate the 
  changes to the monitoring interface as well.

### Fixed
- Removed cyclic imports in `monitors` and `packet_generators` submodules.
- Additional style issues were removed that arose due to the update of pylint 
  to version 2.2.2
- The `qsim` backend was updated to assure that insertion of events in the 
  past are caught. Also, the backend now allows for the insertion of two 
  concurrent events scheduled for the same time by the same runner.

## [0.0.9] - 2018-10-22
### Added
- Allowing naming of simulation runs for an better overview if multiple 
  simulations are running at the same time. Also provide 3 types of output: 
  `NONE`, `TQDM` and `TEXTUAL`.

### Changed
- Removed delay calculations from the simulation environment.
- Order successor list in `ContactGraph` object both after to_time and hash 
  value of the to_node.

### Fixed
- Fixed bug in the calculation of route capacities in all Dijkstra flavours.
- Create nominal nodes for otherwise unconnected contacts.

## [0.0.8] - 2018-10-19
### Added
- Allow handover of a list of the hotspots to the routing algorithms. This 
  list is used to prevent loops inbetween the hotspots due to congestion to 
  the satellites. Whenever a packet is received at a hotspot from another 
  hotspot with the `Return-To-Sender`-Flag set to False, the packet can not 
  only be returned to the sender, but to no other hotspot as well. It has to 
  be scheduled on the local node for a later contact.
- If the JSON source file contains the information regarding the hotspots, this
  information is automatically extracted during the generation of the 
  `ContactPlan`. It can be accessed through both the `ContactPlan` and the 
  `ContactGraph` object.
  
### Changed
- Sort successor and predecessor lists by the to_time. Instead of having to 
  remove nodes from the `ContactGraph` over time to gain a performance boost, 
  we can simply exit the loop in the neighbor function if we encounter the 
  first value that is <= the current distance.
- Moved commonly used CGR functionality to a shared module `cgr_utils`.
  
### Fixed
- Fixed bug in routing algorithms where the delay of a contact was not 
  considered when deciding on the feasible neighbors.
- Removed unnecessary search operations by setting the start value of the 
  Dijkstra search to the current time. A search run for values below that 
  value is never needed.

## [0.0.7] - 2018-10-17
### Added
- Consider the delay provided with the ContactPlan information both for the 
  simulation forwarding as well as the routing approaches. A delay has to be 
  provided (as default delay) that is used when no delay is provided or the
  delay is zero. The delay (propagation + processing etc.) must never be zero 
  as (in combination with the restricted simulation resolution) this could 
  cause infinite forwarding loops and would prevent the simulation from 
  terminating.
  
### Changed
- Improved the decision consistency of CGR_Basic, CGR_Anchor and SCGR. By 
  using the forwarding time to the next hop instead of the hash as third 
  characteristic value, the overall performance in the face of network 
  congestion is improved. The hash values are used as tie-break as fourth 
  characteristic.

### Fixed  
- Fixed problem where the successor list was altered (items were removed) 
  while iterating over it. This led to undefined behaviour where randomly 
  subsequent values were not considered.

## [0.0.6] - 2018-10-10
### Added
- Added lookahead window in SCGR: Instead of looking for routes of the entire 
  period that the contact graph holds information, the algorithm makes an 
  educated guess as of in which timespan a route could be expected. This is 
  based on a static value for the first run and the previously observed mean 
  route EDT times 1.2 in subsequent runs. If no route can be found within the 
  window, the Dijkstra run is repeated without the window to ensure that a 
  route is found if there is one. With this approach, in Simulations usually 
  more than 90% of the found routes were within the window, thus reducing the 
  overall route finding time significantly while returning the same results.
- Added option to ignore contacts that lie beyond the simulation window. I.e. 
  if the scenario source file contains more topology information, that 
  information is discarded during the ContactPlan generation and thus not used 
  for the contact ContactGraph generation.
- Implemented new custom backend (called qsim) that handles the event-based
  simulation procedure much faster than simpy. Changed contact and packet
  generators to use the new backend.
- Added rich comparison methods for packet object (based on packet identifier).
- Contact Utilization Analysis. The average value for all contacts is provided
  in the standard post-simulation summary and the function 
  `get_utilization_list` returns a list of the utilizations per individual
  contact.

### Changed
- Switched to python 3.7.0 to make use of the integrated dataclasses ("mutable 
  namedtuple"). Updated docker image in CI.
- Removed redundant code in SCGR.
- Refactoring of the Dijkstra implementation to improve the performance. 
  Previously, many variables for the search were initialized for all nodes. By 
  rewriting Dijkstra, this could be mitigated. Instead, the variables are 
  considered to be in a certain stage if they are not initialized. They are 
  instead create on-demand if needed.
- Switched visited data structure in Dijkstra from list to set, which hashes
  the values and thus yields in better performance.
- Changed removal of past contacts from contact graph to on-demand. Instead of 
  iterating over the entire graph all the time, the approaches are now 
  removing the old contact only if they encounter them again in the neighbor function. Improves performance by getting rid of another iteration over all
  elements of the graph.
- Removed profiling script from CI. It takes way too long on the CI runner
  while having only very limited CI testing significance.
- Changed time steps/unit to milliseconds and removed round() where possible.
  Also switched to int instead of float wherever possible to improve 
  performance. With the new approach, round is only used in places where the 
  performance impact is not that severe, but e.g. in is_capacity_sufficient() 
  which is called very often, an approximation is used that slightly 
  deteriorates the overall routing efficiency (because it underestimates the 
  remaining capacity of contacts due to it's conservative estimation). After a 
  routing decision has been made, the precise time is calculated using round().
- Reduced computational complexity of the ContactGraph generation procedure. 
  Moved edge generation into a separate internal static function.
- Changed CI scripts to new ms time unit.
- Adapted documentation to new ms time unit and int type.

### Fixed
- Fixed static selection of SCGR as profiling algorithm in profiler script.
- Fixed bug where due to missing parentheses the datarate during the contact
  graph generation was computed incorrectly (much higher).
- Fixed division-by-zero bug in profiler script.

## [0.0.5] - 2018-10-05
### Added
- Added profiling script to project and integrated that script into CI. 

### Changed
- Major performance optimizations based on analysis using cProfile, 
  pyprof2calltree and KCacheGrind.
- Removed `deepcopy` operations for `ContactGraph` object (every 
  node/destination combination had a own copied object with custom *nominal* 
  nodes) and switched to shared `ContactGraph` object which has all *nominal* 
  nodes integrated. Route finding logic prevents the usage of nominal nodes 
  other than the designated ones in a specific route search.
- The removal/invalidation of edges within the `ContactGraph` object is now 
  performed by maintaining a list of excluded nodes that is provided to 
  `cgr_neighbor_function()`. The function then does not provide these excluded 
  nodes in the returned neighbor list.
- The generation and edge determination of the *nominal* nodes during the 
  standard graph generation procedure also improves the overall `ContactGraph` 
  generation performance.
- The test cases of the `ContactGraph` object had to be changed to accommodate 
  the changes in the graph generation procedure (the integration of the 
  *nominal* nodes).

### Fixed
-

## [0.0.4] - 2018-10-04
### Added
- Auto-detection of submodules for packet installation purposes.
- Chaining of `position` and `desc` variables for `tqdm` in `Simulator` 
  object.
- Stat function in simulator to allow applications to extract the number of
  remaining packets in limbos and contacts and the total packet count.

### Changed
- Updated python docker container used for CI to `3.5-stretch`.
- Precompute hashes for Dijkstra search in all three routing approaches and   
  provide them to to Dijkstra to improve performance.
- Make extensive use of `namedtuples` in all routing approaches: use provided  
  specific access functionality (namedtuple.<value>) in routing logic instead 
  of standard tuple access (tuple[x]) for `Routes`, `Neighbors`, 
  `RouteListEntry`. This greatly improves readability.
- Updated neighbor functions called by Dijkstra in all routing approaches.
- Updated docstrings/documentation in scgr.

### Fixed
- Terminate Dijkstra search when shortest route is found. (Was improperly 
  running until no more (worse) routes were available).
- Ensure correct order of returned routes from Dijkstra search in terms of 
  second characteristic (hops) and third characteristic (hash of nodes).
- Fixed bug where loops (in terms of nodes, not contacts) were not prevented.
- Separated handling of suppressed nodes and suppressed contacts and fixed
  handling logic.

## [0.0.3] - 2018-09-24
### Added
- Stat function in simulator to allow applications to extract the number of
  remaining packets in limbos and contacts and the total packet count.

### Changed
- The Dijkstra implementation now also adds the hop count to the priority
  queue and thus ensures the correct order of route finding both for the
  first (EDT) and second (hop count) CGR route selection criterion. This was
  not the case before and additional code was required to ensure the order in
  terms of the second criterion. Change is not necessary or relevant for
  current core CGR implementations (also backward compatible), but is helpful 
  for additional newly developed routing approaches.

### Fixed
- Wrong callback call in MonitorNotifier object (routed instead of injected).
- Fixed order of action and monitoring callback for injecting packets in 
  SimpleCGRNode object.

## [0.0.2] - 2018-08-16
### Added
- Added packet generator base class to remove code redundancy. Adapted the two
  existing packet generators to be based on that base class.
- Convenience imports in multiple `__init__.py` files to make imports shorter.

### Changed
- Use namedTuples instead of anonymous tuples in the routing context to improve
  readability.

### Fixed
- Fixed integration and behaviour of continous packet generator.
- Comparison source destination node comparison bug in Dijkstra implementation.
- Removed various statements that were not complying with the EAFP paradigm of
  Python.
- Removed statements that were type-checking things and thus contradicting the
  duct-typing paradigm of Python.
- Fixed various Docstring issues (i.e. moved class attributes from init 
  function to class Docstring)

## [0.0.1] - 2018-08-08
### Added
- Initial release.
- Added simulation environment.
- Added three routing algorithms (CGR basic, CGR with anchorin, SCGR).
- Added continous and batch packet generators.
- Added simple cgr-based node implementation.
- Added example file.
- Added unit tests.
- Added determinism and equivalence check for routing approaches.
