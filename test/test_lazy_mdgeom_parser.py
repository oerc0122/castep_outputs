from pathlib import Path

import pytest

from castep_outputs.tools.md_geom_parser import MDGeomParser



FILE = Path(__file__).parent / "data_files" / "si8-md.md"

@pytest.fixture
def parser():
    yield MDGeomParser(FILE)

def test_read(parser):
    """Check the parser is reading properly."""
    # Check frames
    assert len(parser) == 3

    for frame in parser:
        # Check all expected keys present

        assert not ({"ions", "time", "E", "T", "h",
                     "energy", "temperature", "lattice_vectors"} - frame.keys())

        # Check latt vecs
        lattice_vectors = frame["lattice_vectors"]
        assert len(lattice_vectors) == 3 and all(len(vec) == 3 for vec in lattice_vectors)

        # Check ions
        ions = frame["ions"]
        assert len(ions) == 8
        for ion in ions.values():
            assert not ({"R", "V", "F", "position", "velocity", "force"} - ion.keys())

    # Test getitem
    frames = list(parser)
    assert parser[1] == frames[1]

def test_next_frame(parser):
    """Check the next frame counter is working."""
    it = iter(parser)

    # No frames read
    assert parser.next_frame == 0

    next(it)
    assert parser.next_frame == 1
    next(it)
    assert parser.next_frame == 2

    # Exhausted
    next(it)
    assert parser.next_frame is None

    # Check setting with send (iter resets parser to start)
    it = iter(parser)
    next(it)
    next(it)
    it.send(0)
    assert parser.next_frame == 1

    # Check with getitem
    parser[2]
    assert parser.next_frame is None
    parser[0]
    assert parser.next_frame == 1

def test_getitem(parser):
    it = iter(parser)
    test = [next(it), next(it)]

    assert parser[0, 1] == parser[0:2]

    assert parser[0:2] == test
