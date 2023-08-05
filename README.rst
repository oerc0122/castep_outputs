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

When run as a commandline tool, it attempts to find all files for the given
seedname, filtered by ``inc`` args (default: all). Explicit files can be passed
using longname arguments. castep_outputs can parse most human-readable castep
outputs including: ``.castep``, ``.param``, ``.cell``, ``.geom``, ``.md``,
``.bands``, ``.hug``, ``.phonon_dos``, ``.efield``, ``.xrd_sf``, ``.elf_fmt``,
``.chdiff_fmt``, ``.pot_fmt, .den_fmt``, ``.elastic``, ``.ts``.

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
using the ``PyYAML`` engine.

As a module
-----------

``import``\ ing ``castep_outputs`` directly puts all of the parsers directly
into your local namespace.

The simplest method to use ``castep_outputs`` in a tool is to use the
``parse_single`` method which attempts to determine the parser from the file
extension.

::

   import castep_outputs

   my_dict = parse_single('my_file.castep')

If you need a specific parser rather than by extension it is possible to pass
them as the second argument, or call them directly.

::

   import castep_outputs

   my_dict = parse_single('my_file', parse_castep_file)

   with open('my_file', 'r', encoding='utf-8') as inp:
       my_dict = parse_castep_file(inp)

It is recommended that you use ``parse_single`` as it uses special file-handling
to give better diagnostics if it fails. It is possible to enable more detailed
logging via the `logging
<https://docs.python.org/3/library/logging.html#logging.basicConfig>`_ module:

::

   import castep_outputs
   import logging

   my_dict = parse_single('my_file', loglevel=logging.INFO)

The available parsing functions are:

-  ``parse_castep_file``
-  ``parse_cell_param_file``
-  ``parse_param_file``
-  ``parse_cell_file``
-  ``parse_md_geom_file``
-  ``parse_md_file``
-  ``parse_geom_file``
-  ``parse_bands_file``
-  ``parse_hug_file``
-  ``parse_phonon_dos_file``
-  ``parse_efield_file``
-  ``parse_xrd_sf_file``
-  ``parse_elf_fmt_file``
-  ``parse_chdiff_fmt_file``
-  ``parse_pot_fmt_file``
-  ``parse_den_fmt_file``
-  ``parse_elastic_file``
-  ``parse_ts_file``

Which return processed ``list``\ s of ``dict``\ s of data ready for use
in other applications.

Full usage
----------

::

   usage: castep_outputs [-h] [-V] [-L {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-o OUTPUT]
                         [-f {json,ruamel,yaml,pprint,print}] [-t] [-A] [-c] [-g] [-m] [-b] [-p] [-e] [-x] [-H] [-E]
                         [-C] [-P] [-D] [-X] [-T] [--inc-param] [--inc-cell] [--castep [CASTEP ...]]
                         [--geom [GEOM ...]] [--cell [CELL ...]] [--param [PARAM ...]] [--md [MD ...]]
                         [--bands [BANDS ...]] [--hug [HUG ...]] [--phonon_dos [PHONON_DOS ...]]
                         [--efield [EFIELD ...]] [--xrd_sf [XRD_SF ...]] [--elf_fmt [ELF_FMT ...]]
                         [--chdiff_fmt [CHDIFF_FMT ...]] [--pot_fmt [POT_FMT ...]] [--den_fmt [DEN_FMT ...]]
                         [--elastic [ELASTIC ...]] [--ts [TS ...]]
                         ...

   Attempts to find all files for seedname, filtered by `inc` args (default: all). Explicit files can be passed
   using longname arguments. Parse most human-readable castep outputs including: .castep, .param, .cell, .geom, .md,
   .bands, .hug, .phonon_dos, .efield, .xrd_sf, .elf_fmt, .chdiff_fmt, .pot_fmt, .den_fmt, .elastic, .ts

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
     -c, --inc-castep      Extract .castep information
     -g, --inc-geom        Extract .geom information
     -m, --inc-md          Extract .md information
     -b, --inc-bands       Extract .bands information
     -p, --inc-phonon_dos  Extract .phonon_dos information
     -e, --inc-efield      Extract .efield information
     -x, --inc-xrd_sf      Extract .xrd_sf information
     -H, --inc-hug         Extract .hug information
     -E, --inc-elf_fmt     Extract .elf_fmt information
     -C, --inc-chdiff_fmt  Extract .chdiff_fmt information
     -P, --inc-pot_fmt     Extract .pot_fmt information
     -D, --inc-den_fmt     Extract .den_fmt information
     -X, --inc-elastic     Extract .elastic information
     -T, --inc-ts          Extract .ts information
     --inc-param           Extract .param information
     --inc-cell            Extract .cell information
     --castep [CASTEP ...]
                           Extract from CASTEP as .castep type
     --geom [GEOM ...]     Extract from GEOM as .geom type
     --cell [CELL ...]     Extract from CELL as .cell type
     --param [PARAM ...]   Extract from PARAM as .param type
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

Current Parsers:

-  ``.castep``
-  ``.param``
-  ``.cell``
-  ``.geom``
-  ``.md``
-  ``.bands``
-  ``.hug``
-  ``.phonon_dos``
-  ``.efield``
-  ``.xrd_sf``
-  ``.elf_fmt``
-  ``.chdiff_fmt``
-  ``.pot_fmt``
-  ``.den_fmt``
-  ``.elastic``
-  ``.ts``

Current dumpers:

-  ``json``
-  ``ruamel.yaml``
-  ``pyyaml``
-  ``print``
-  ``pprint``
