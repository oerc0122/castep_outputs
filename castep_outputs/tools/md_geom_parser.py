"""Lazy MD/Geom parser object."""
from __future__ import annotations

from collections.abc import Generator, Sequence
from functools import singledispatchmethod
from pathlib import Path

from castep_outputs.parsers.md_geom_file_parser import (
    MDGeomTimestepInfo,
    parse_md_geom_frame,
)
from castep_outputs.utilities.filewrapper import Block


class MDGeomParser:
    """Lazy MD/Geom parser."""

    def __init__(self, md_geom_file: Path | str):
        self._next_frame = 0

        self.file = Path(md_geom_file).expanduser()

        if not self.file.exists() or not self.file.is_file():
            raise FileNotFoundError(f"Cannot open file ({self.file.absolute()}).")

        self._handle = self.file.open()
        while "END header" not in self._handle.readline():
            pass
        self._handle.readline()
        self._start = self._handle.tell()

        self._frame_len = 0
        while self._handle.readline().strip():
            self._frame_len += 1
        self._byte_len = self._handle.tell() - self._start
        stat = self.file.stat()

        len_est = (stat.st_size - self._start) / self._byte_len

        if not len_est.is_integer():
            print(f"""\
WARNING: Number of frames estimate is non-integral ({len_est}).
This may have been caused by manually modifying the file.

While iteration should work, extracting particular frames may not.
""")

        self._len = int(len_est)

    @property
    def next_frame(self) -> int:
        """Get index of next frame to be read."""
        return self._next_frame

    def _get_index(self, frame: int) -> int:
        """Get index of given frame in bytes."""
        return self._start + (self._byte_len * frame)

    def _go_to_frame(self, frame: int) -> None:
        """Set file pointer to given index."""
        ind = self._get_index(frame)
        self._handle.seek(ind)
        self._next_frame = frame if frame < len(self) else None

    def get_frame(self, frame: int) -> MDGeomTimestepInfo:
        """Get particular frame of md/geom."""
        if -len(self) > frame > len(self):
            print(f"Cannot get {frame}th frame. File only has {len(self)} frames.")

        if frame < 0:
            frame = len(self) + frame

        self._go_to_frame(frame)

        return next(self)

    def __len__(self) -> int:
        """Get number of frames in file."""
        return self._len

    def __iter__(self) -> Generator[MDGeomTimestepInfo, int, None]:
        """
        Get generator over all frames in system.

        Jumps permitted through ``send``.
        """
        self._handle.seek(self._start)
        self._next_frame = 0
        while self._next_frame is not None:
            jump = yield next(self)
            if jump is not None:
                self._go_to_frame(jump)

    def __next__(self) -> MDGeomTimestepInfo:
        """Get the next frame."""
        if not (block := Block.get_lines(self._handle, self._frame_len, eof_possible=True)):
            raise StopIteration

        self._next_frame = self._next_frame + 1 if self._next_frame < len(self) - 1 else None
        return parse_md_geom_frame(block)

    @singledispatchmethod
    def __getitem__(self, frame) -> list[MDGeomTimestepInfo] | MDGeomTimestepInfo:
        """Get particular frame of md/geom."""
        raise NotImplementedError(f"Can't get {frame}th frame.")

    @__getitem__.register(int)
    def _(self, frame) -> MDGeomTimestepInfo:
        """Get particular frame of md/geom."""
        return self.get_frame(frame)

    @__getitem__.register(Sequence)
    def _(self, frames) -> list[MDGeomTimestepInfo]:
        """Get particular frame of md/geom."""
        return [self.get_frame(frame) for frame in frames]

    @__getitem__.register(slice)
    def _(self, frames) -> list[MDGeomTimestepInfo]:
        """Get particular frame of md/geom."""
        range_ = frames.start or 0, frames.stop or len(self), frames.step or 1

        return self[range(*range_)]

    def __del__(self):
        """Close file before deletion."""
        self._handle.close()

    def __str__(self) -> str:
        """Get file info."""
        return f"""\
File: {self.file}
Frames: {self._len}
Next frame: {self._next_frame}"""
