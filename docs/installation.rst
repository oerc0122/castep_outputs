Install
-------

To install ``castep_outputs`` simply run:

::

   pip install castep_outputs

To check it is installed run:

::

   python -m castep_outputs -h

Dependencies
------------

``castep_outputs`` is designed to have no external dependencies beyond the
standard library, however, it is possible to use either `PyYAML
<https://pypi.org/project/PyYAML/>`__ or `ruamel.yaml
<https://pypi.org/project/ruamel.yaml/>`__ to dump in the YAML format.

This documentation was created using `jupyter-book<https://jupyterbook.org/>`.
If you want to build the documentation yourself you will need to install
the additional dependencies listed in ``docs/requirements.txt``. You can do this 
by installing ``castep_outputs`` with the ``docs`` extra:

::

   pip install castep_outputs[docs]

If installing from a local copy of the repository you can install the
``docs`` extra by running:

::

   pip install -e .[docs]


Note that in `zsh` you will need to escape the square brackets:

::

   pip install -e .\[docs\]

