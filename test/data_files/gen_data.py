"""Generate testing benchmark files for dumpers."""
import pathlib

from castep_outputs.cli.castep_outputs_main import parse_all


def gen_data():
    """Generate benchmark data."""
    for type_ in ("castep", "bands", "cell", "param", "elastic", "md", "ts", "efield", "cst_esp",
                  "den_fmt", "chdiff_fmt", "pot_fmt", "elf_fmt", "xrd_sf", "phonon", "phonon_dos",
                  "magres", "efield", "tddft", "err", ("pp-md", "castep"), ("si8-md", "castep")):
        for fmt in ("json", "pyyaml", "ruamel"):
            print(type_, fmt)
            if isinstance(type_, tuple):
                name, typ = type_
                in_name = name
            else:
                name = typ = type_
                in_name = "test"

            # Delete existing
            pth = pathlib.Path(f"{name}.{fmt}")
            pth.unlink(missing_ok=True)
            parse_all(output=str(pth), out_format=fmt, **{typ: [f"{in_name}.{typ}"]})


if __name__ == "__main__":
    gen_data()
