castep_outputs
==============

.. image:: https://img.shields.io/badge/version-{version}-blue
   :alt: Version

Parser for CASTEP output files

``castep_outputs`` parses the output files of `castep
<https://www.castep.org/>`__ into a standard form and is able to subsequently
dump the processed data into a standard format.

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

Command-line
------------

When run as a commandline tool, it attempts to find all files for the
given seedname, filtered by ``inc`` args (default: all). Explicit
files can be passed using longname arguments. castep_outputs can parse
most human-readable castep outputs including:
{file_formats}.

to run in basic mode:

::

   python -m castep_outputs seedname

Which will attempt to detect all found files and dump a ``.json`` to
stdout, ready for piping.

::

   python -m castep_outputs --inc-castep --inc-param seedname

Will parse only the ``seedname.castep`` and ``seedname.param`` files if
found.

::

   python -m castep_outputs seedname.castep

Will parse the single named file and again dump a ``.json`` to stdout.

::

   python -m castep_outputs --castep seedname.param

Will attempt to parse the file ``seedname.param`` as though it were a
``.castep`` file. While not ordinarily useful it can help with manually renamed
files.

::

   python -m castep_outputs -o my_file.yaml -f yaml seedname.castep

Will parse ``seedname.castep``, dump it to ``my_file.yaml`` in ``yaml`` format
using the ``PyYAML`` engine if available and the ``RUAMEL`` engine if not.

As a module
-----------

``import``\ ing ``castep_outputs`` exposes all of the parsers at the
top-level.

The simplest method to use ``castep_outputs`` in a tool is to use the
``parse_single`` method which attempts to determine the parser from the file
extension.

::

   from castep_outputs import parse_single

   my_dict = parse_single('my_file.castep')

If you need a specific parser rather than determining it by extension
it is possible to pass them as the second argument, or call them
directly.

::

   from castep_outputs import parse_single, parse_castep_file

   my_dict = parse_single('my_file', parse_castep_file)

   with open('my_file', 'r', encoding='utf-8') as inp:
       my_dict = parse_castep_file(inp)

It is recommended that you use ``parse_single`` as it uses special file-handling
to give better diagnostics if it fails. It is possible to enable more detailed
logging via the `logging
<https://docs.python.org/3/library/logging.html#logging.basicConfig>`_ module:

::

   import logging
   from castep_outputs import parse_single

   my_dict = parse_single('my_file', loglevel=logging.INFO)

The available parsing functions for parsing the given format are:

{parse_functions}

Which return processed ``list``\ s of ``dict``\ s of data ready for use
in other applications.

See `Documentation <https://oerc0122.github.io/castep_outputs/index.html>`_ for full layout.

Full usage
----------

::

{usage}

Current Parsers:

{parsers}

Current dumpers:

{dumpers}
