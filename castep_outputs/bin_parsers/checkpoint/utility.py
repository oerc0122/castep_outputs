"""Utilities for parsing checkpoint files."""

from typing import Any

from castep_outputs.bin_parsers.fortran_bin_parser import FortranBinaryReader
from castep_outputs.utilities.type_conv import TypeTupleMapping


def parse_nested_header_dump(
    reader: FortranBinaryReader,
    dtypes: dict[str, TypeTupleMapping],
    term: str,
) -> dict[str, dict[str, Any]]:
    """Parse headered dumps where each header can contain multiple values.

    Header dumps from the dump:

    .. code-block:: fortran

      write(out_unit) "MY_HEADER"
      write(out_unit) data(:10)
      write(out_unit) data2(:10)
      write(out_unit) data3(:10)


    Parameters
    ----------
    reader
        Data to process.
    dtypes
        Types to map in :code:`{header: value}` format.
    term
        String signifying end of sequence.

    Returns
    -------
    :
        Processed data.

    Raises
    ------
    ValueError
        Unknown header.
    """
    accum = {}

    while (header := reader.get(str).strip()) != term:
        key = header.rsplit("%", maxsplit=1)[-1]
        if header not in dtypes:
            raise ValueError(f"Unable to parse unknown block {header}.")

        new_type = dtypes[header]
        accum[key.lower()] = reader.get_dtype_dict(new_type)

    return accum


def parse_headered_dump(
    reader: FortranBinaryReader,
    dtypes: TypeTupleMapping,
    term: str,
) -> dict[str, Any]:
    """Parse headered dumps.

    Header dumps from the dump:

    .. code-block:: fortran

      write(out_unit) "MY_HEADER"
      write(out_unit) data(:10)

    Parameters
    ----------
    reader
        Data to process.
    dtypes
        Types to map in :code:`{header: value}` format.
    term
        String signifying end of sequence.

    Returns
    -------
    :
        Processed data.

    Raises
    ------
    TypeError
        Cannot cast data to type.
    ValueError
        Unknown header.
    """
    accum = {}

    while (header := reader.get(str).strip()) != term:
        key = header.rsplit("%", maxsplit=1)[-1]
        if header not in dtypes:
            raise ValueError(f"Unable to parse unknown block {header}.")

        new_type = dtypes[header]
        if new_type is bytes:
            accum[key.lower()] = next(reader)
            continue

        try:
            new_val = reader.get(new_type)
        except Exception as err:
            reader.rewind()
            raw_data = next(reader)
            raise TypeError(
                f"Unable to process data ({raw_data}) as {new_type} for {header}.",
            ) from err

        accum[key.lower()] = new_val

    return accum
