Installation
============
Depending on the intended use case, the installation procedure for the library differs. If the library modules should only be invoked by custom scripts, installing ``pyDTNsim`` via the Python package index PyPi_ is sufficient. If the simulation modules have to be altered, downloading the source code and installing ``pyDTNsim`` as editable python module is required.

.. _PyPi: https://pypi.org/

Module Dependencies
-------------------
The following modules are used in various contexts of ``pyDTNsim``. However, some are only necessary for the development of the module and not for running simulations.

.. _dependency_table:

+-------------------+-----------+-----------------------------+-----------+ 
| Python Module     | License   | Purpose                     | Dev? [1]_ |
+===================+===========+=============================+===========+
| networkx          | BSD       | Library allows the export   |           | 
|                   |           | of networkx ``DiGraph``     |           |
|                   |           | objects for additional      |           |
|                   |           | graph analyses.             |           |
+-------------------+-----------+-----------------------------+-----------+ 
| tqdm              | MIT       | Used for displaying the     |           |
|                   |           | simulation progress (i.e.   |           |
|                   |           | elapsed simulated seconds). |           |
+-------------------+-----------+-----------------------------+-----------+ 
| jsonschema        | MIT       | Validation of JSON schemes  |           | 
|                   |           | in the loaded topology      |           |
|                   |           | files.                      |           |
+-------------------+-----------+-----------------------------+-----------+ 
| pytest            | MIT       | Used for running the        | x         |
|                   |           | modules unit tests. Only    |           |
|                   |           | executed in CI,             |           |
|                   |           | not integrated otherwise.   |           |
+-------------------+-----------+-----------------------------+-----------+ 
| sphinx            | BSD       | Generation of this          | x         | 
|                   |           | documentation. Not          |           |
|                   |           | invoked by the module.      |           |
+-------------------+-----------+-----------------------------+-----------+ 
| sphinx_rtd_theme  | MIT       | Theme for ``sphinx``.       | x         | 
+-------------------+-----------+-----------------------------+-----------+ 
| pylint            | GPL       | Tool for detecting source   | x         | 
|                   |           | code issues. Only           |           |
|                   |           | executed in CI,             |           |
|                   |           | not integrated otherwise.   |           |
+-------------------+-----------+-----------------------------+-----------+ 
| pydocstyle        | MIT       | Tool for validating         | x         | 
|                   |           | docstrings in source code.  |           |
+-------------------+-----------+-----------------------------+-----------+ 
| termcolor         | MIT       | Provides colorful shell     | x         | 
|                   |           | output when testing         |           |
|                   |           | the examples of the module. |           |
+-------------------+-----------+-----------------------------+-----------+ 

.. [1] Modules with 'Dev?' checked are only relevant in the development context of this module.

pyDTNsim uses new Python features, in particular

- `Data Classes <https://docs.python.org/3/whatsnew/3.7.html#whatsnew37-pep557>`_ (3.7),
- `Formatted String Literals <https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep498>`_ (3.6) and
- `Insertion-Order Preservation <https://mail.python.org/pipermail/python-dev/2017-December/151283.html>`_ of items added to a ``dict`` object. (3.7).

Therefore, **Python 3.7+** is currently required for using this library. 

.. note::

	 It is planned to establish compatibility with older versions (especially 2.7) in the future.


PyPi Installation
-----------------
The latest version of *pyDTNsim* can be installed with ``pip3``:

.. code-block:: sh
  
  $ pip3 install pydtnsim
  
Thats it, ``pip3`` will download the module from PyPi_ and install it locally. Check if the module was installed correctly by invoking a Python shell and importing the module:

.. code-block:: python

  > import pydtnsim
  
If no error occurs, the installation was successful. Continue with the with the section :ref:`getting_started`.
 
Source Code Installation
------------------------
Alternatively, the module can be made available in the local Python instance by downloading it from `Github <https://github.com>`_ and then installing it as editable package. 

This more advanced installation is necessary when the library module (or parts of it) have to be altered. For example, this is the case if contributing to the module is intended.

Archive Download and Extraction
"""""""""""""""""""""""""""""""
The source can be downloaded as `.zip <https://github.com/ducktec/pydtnsim/archive/master.zip>`_ or `.tar.gz <https://github.com/ducktec/pydtnsim/archive/master.tar.gz>`_ archive.

In Linux, the download and extraction of the files can usually also be achieved using the utilities ``wget`` and ``tar``:

.. code-block:: sh

  $ wget https://github.com/ducktec/pydtnsim/archive/master.tar.gz
  $ tar -xzf master.tar.gz 
  $ cd pydtnsim-master/
  
Git Clone
"""""""""
If the version-control system ``git`` is installed, the project can also be cloned:

.. code-block:: sh

  $ git clone https://github.com/ducktec/pydtnsim.git
  $ cd pydtnsim/
  
Module Installation
"""""""""""""""""""
.. warning:: Please store the ``pydtnsim/`` source code folder in an appropriate (long-term) directory on your local device. As we are installing the module as editable, the Python environment will continuously reference the files directly instead of copying them to hidden internal folders. Moving the directory around after the installation will likely result in broken references and errors!
  
As next step, the module can be made available in the Python environment:

.. code-block:: sh

  $ pip install -e "."
  
``pip3`` installs the module as editable (achieved with the parameter ``-e``) and tries to satisfy all core dependencies (see above :ref:`dependency table <dependency_table>`).

If all development dependencies [1]_ shall be installed, the ``[dev]`` specifier has to be added to the installation command:

.. code-block:: sh

  $ pip install -e ".[dev]"
  
Check if the module was installed correctly by invoking a Python shell and importing the module:

.. code-block:: python

  > import pydtnsim
  
If no error occurs, the installation was successful. Continue ith the section :ref:`getting_started`.
