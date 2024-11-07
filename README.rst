castep_outputs
==============

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
most human-readable castep outputs including: ``.castep``, ``.cell``,
``.param``, ``.geom``, ``.md``, ``.bands``, ``.hug``, ``.phonon``,
``.phonon_dos``, ``.efield``, ``.xrd_sf``, ``.elf_fmt``,
``.chdiff_fmt``, ``.pot_fmt``, ``.den_fmt``, ``.elastic``, ``.ts``,
``.magres``, ``.tddft``, ``.err``.

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

   import castep_outputs as co

   my_dict = co.parse_single('my_file', co.parse_castep_file)

   with open('my_file', 'r', encoding='utf-8') as inp:
       my_dict = co.parse_castep_file(inp)

It is recommended that you use ``parse_single`` as it uses special file-handling
to give better diagnostics if it fails. It is possible to enable more detailed
logging via the `logging
<https://docs.python.org/3/library/logging.html#logging.basicConfig>`_ module:

::

   import logging
   from castep_outputs import parse_single

   my_dict = parse_single('my_file', loglevel=logging.INFO)

The available parsing functions are:

-  ``parse_bands_file``
-  ``parse_castep_file``
-  ``parse_cell_file``
-  ``parse_cell_param_file``
-  ``parse_chdiff_fmt_file``
-  ``parse_den_fmt_file``
-  ``parse_efield_file``
-  ``parse_elastic_file``
-  ``parse_elf_fmt_file``
-  ``parse_err_file``
-  ``parse_geom_file``
-  ``parse_hug_file``
-  ``parse_magres_file``
-  ``parse_md_file``
-  ``parse_md_geom_file``
-  ``parse_param_file``
-  ``parse_phonon_file``
-  ``parse_phonon_dos_file``
-  ``parse_pot_fmt_file``
-  ``parse_tddft_file``
-  ``parse_tddft_file``
-  ``parse_ts_file``
-  ``parse_xrd_sf_file``

Which return processed ``list``\ s of ``dict``\ s of data ready for use
in other applications.

See `Documentation <https://oerc0122.github.io/castep_outputs/intro.html>`_ for full layout.

Full usage
----------

::

   usage: castep_outputs [-h] [-V] [-L {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-o OUTPUT]
                         [-f {json,ruamel,yaml,pprint,print}] [-t] [-A] [--inc-castep]
                         [--inc-cell] [--inc-param] [--inc-geom] [--inc-md]
                         [--inc-bands] [--inc-hug] [--inc-phonon_dos] [--inc-efield]
                         [--inc-xrd_sf] [--inc-elf_fmt] [--inc-chdiff_fmt]
                         [--inc-pot_fmt] [--inc-den_fmt] [--inc-elastic] [--inc-ts]
                         [--inc-magres] [--inc-tddft] [--inc-err] [--inc-phonon]
                         [--castep [CASTEP ...]] [--cell [CELL ...]]
                         [--param [PARAM ...]] [--geom [GEOM ...]] [--md [MD ...]]
                         [--bands [BANDS ...]] [--hug [HUG ...]]
                         [--phonon_dos [PHONON_DOS ...]] [--efield [EFIELD ...]]
                         [--xrd_sf [XRD_SF ...]] [--elf_fmt [ELF_FMT ...]]
                         [--chdiff_fmt [CHDIFF_FMT ...]] [--pot_fmt [POT_FMT ...]]
                         [--den_fmt [DEN_FMT ...]] [--elastic [ELASTIC ...]]
                         [--ts [TS ...]] [--magres [MAGRES ...]] [--tddft [TDDFT ...]]
                         [--err [ERR ...]] [--phonon [PHONON ...]]
                         ...

   Attempts to find all files for seedname, filtered by `inc` args (default: all).
   Explicit files can be passed using longname arguments. castep_outputs can parse most
   human-readable castep outputs including: .castep, .cell, .param, .geom, .md, .bands,
   .hug, .phonon_dos, .efield, .xrd_sf, .elf_fmt, .chdiff_fmt, .pot_fmt, .den_fmt,
   .elastic, .ts, .magres, .tddft, .err, .phonon

   positional arguments:
     seedname              Seed name for data

   options:
     -h, --help            show this help message and exit
     -V, --version         show program's version number and exit
     -L {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                           Verbose output
     -o OUTPUT, --output OUTPUT
                           File to write output, default: screen
     -f {json,ruamel,yaml,pprint,print}, --out-format {json,ruamel,yaml,pprint,print}
                           Output format
     -t, --testing         Set testing mode to produce flat outputs
     -A, --inc-all         Extract all available information
     --inc-castep          Extract .castep information
     --inc-cell            Extract .cell information
     --inc-param           Extract .param information
     --inc-geom            Extract .geom information
     --inc-md              Extract .md information
     --inc-bands           Extract .bands information
     --inc-hug             Extract .hug information
     --inc-phonon_dos      Extract .phonon_dos information
     --inc-efield          Extract .efield information
     --inc-xrd_sf          Extract .xrd_sf information
     --inc-elf_fmt         Extract .elf_fmt information
     --inc-chdiff_fmt      Extract .chdiff_fmt information
     --inc-pot_fmt         Extract .pot_fmt information
     --inc-den_fmt         Extract .den_fmt information
     --inc-elastic         Extract .elastic information
     --inc-ts              Extract .ts information
     --inc-magres          Extract .magres information
     --inc-tddft           Extract .tddft information
     --inc-err             Extract .err information
     --inc-phonon          Extract .phonon information
     --castep [CASTEP ...]
                           Extract from CASTEP as .castep type
     --cell [CELL ...]     Extract from CELL as .cell type
     --param [PARAM ...]   Extract from PARAM as .param type
     --geom [GEOM ...]     Extract from GEOM as .geom type
     --md [MD ...]         Extract from MD as .md type
     --bands [BANDS ...]   Extract from BANDS as .bands type
     --hug [HUG ...]       Extract from HUG as .hug type
     --phonon_dos [PHONON_DOS ...]
                           Extract from PHONON_DOS as .phonon_dos type
     --efield [EFIELD ...]
                           Extract from EFIELD as .efield type
     --xrd_sf [XRD_SF ...]
                           Extract from XRD_SF as .xrd_sf type
     --elf_fmt [ELF_FMT ...]
                           Extract from ELF_FMT as .elf_fmt type
     --chdiff_fmt [CHDIFF_FMT ...]
                           Extract from CHDIFF_FMT as .chdiff_fmt type
     --pot_fmt [POT_FMT ...]
                           Extract from POT_FMT as .pot_fmt type
     --den_fmt [DEN_FMT ...]
                           Extract from DEN_FMT as .den_fmt type
     --elastic [ELASTIC ...]
                           Extract from ELASTIC as .elastic type
     --ts [TS ...]         Extract from TS as .ts type
     --magres [MAGRES ...]
                           Extract from MAGRES as .magres type
     --tddft [TDDFT ...]   Extract from TDDFT as .tddft type
     --err [ERR ...]       Extract from ERR as .err type
     --phonon [PHONON ...]
                           Extract from PHONON as .phonon type

Current Parsers:

-  ``.bands``
-  ``.castep``
-  ``.cell``
-  ``.chdiff_fmt``
-  ``.den_fmt``
-  ``.efield``
-  ``.elastic``
-  ``.elf_fmt``
-  ``.err``
-  ``.geom``
-  ``.hug``
-  ``.magres``
-  ``.md``
-  ``.param``
-  ``.phonon``
-  ``.phonon_dos``
-  ``.pot_fmt``
-  ``.tddft``
-  ``.ts``
-  ``.xrd_sf``

Current dumpers:

-  ``json``
-  ``ruamel.yaml``
-  ``pyyaml``
-  ``print``
-  ``pprint``
