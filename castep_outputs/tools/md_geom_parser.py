"""Lazy MD/Geom parser object."""

from __future__ import annotations

from collections.abc import Generator, Sequence
from functools import singledispatchmethod
from pathlib import Path
from typing import overload

from castep_outputs.parsers.md_geom_file_parser import (
    MDGeomTimestepInfo,
    parse_md_geom_frame,
)
from castep_outputs.utilities.filewrapper import Block, FileWrapper

from ..utilities.utility import log_factory


class MDGeomParser:
    """Lazy MD/Geom parser.

    Implements iterator and getitem approaches for
    lazily navigating .md/.geom files.

    Parameters
    ----------
    md_geom_file : Path or str
        File to parse.
    """

    def __init__(self, md_geom_file: Path | str) -> None:
        self._next_frame: int | None

        self.file = Path(md_geom_file).expanduser()

        if not self.file.is_file():
            raise FileNotFoundError(f"Cannot open file ({self.file.absolute()}).")

        self._raw_handle = self.file.open()
        self._handle = FileWrapper(self._raw_handle)
        self.logger = log_factory(self._handle)

        for line in self._handle:
            if "END header" in line:
                break
        else:
            raise ValueError(f'"END header" not in file ({self._handle.name}).')

        next(self._handle)
        self._start = self._handle.tell()
        self._start_line = self._handle.lineno

        while next(self._handle).strip():
            pass
        self._frame_lines = self._handle.lineno - self._start_line - 1

        self._frame_bytes = self._handle.tell() - self._start
        stat = self.file.stat()

        len_est = (stat.st_size - self._start) / self._frame_bytes

        if not len_est.is_integer():
            self.logger(
                f"""\
Number of frames estimate is non-integral ({len_est}).
This may have been caused by manually modifying the file.

While iteration should work, extracting particular frames may not.
""",
                level="warning",
            )

        self._len = int(len_est)
        self._go_to_frame(0)

    @property
    def next_frame(self) -> int | None:
        """Get index of next frame to be read, or None if at file end."""
        return self._next_frame

    def _get_index(self, frame: int) -> int:
        """Get index of given frame in bytes.

        Parameters
        ----------
        frame : int
            Frame to compute.

        Returns
        -------
        int
            Current index in bytes.
        """
        return self._start + (self._frame_bytes * frame)

    def _go_to_frame(self, frame: int) -> None:
        """Set file pointer to given index."""
        ind = self._get_index(frame)
        self._handle.file.seek(ind)
        self._handle._lineno = self._start_line + (frame * self._frame_lines)
        self._next_frame = frame if frame < len(self) else None

    def get_frame(self, frame: int) -> MDGeomTimestepInfo:
        """Get particular frame of md/geom.

        Parameters
        ----------
        frame : int
            Frame to retrieve.

        Returns
        -------
        MDGeomTimestepInfo
            Parsed frame.

        Raises
        ------
        IndexError
            Requested frame out of range.
        """
        if -len(self) > frame < len(self):
            raise IndexError(f"Cannot get {frame}th frame. File only has {len(self)} frames.")

        if frame < 0:
            frame = len(self) + frame

        if frame != self.next_frame:
            self._go_to_frame(frame)

        return next(self)

    def __len__(self) -> int:
        """Get number of frames in file.

        Returns
        -------
        int
            Number of frames.
        """
        return self._len

    def __iter__(self) -> Generator[MDGeomTimestepInfo, int, None]:
        """
        Get generator over all frames in system.

        Jumps permitted through ``send``.

        Yields
        ------
        MDGeomTimestepInfo
            Frames in file.
        """
        i = 0
        while i < len(self):
            trial = yield self[i]
            i += 1
            if trial is not None:
                i = trial

    def __next__(self) -> MDGeomTimestepInfo:
        """Get the next frame.

        Returns
        -------
        MDGeomTimestepInfo
            Next frame in series.

        Raises
        ------
        StopIteration
            No next frame.
        """
        if not (block := Block.get_lines(self._handle, self._frame_lines, eof_possible=True)):
            raise StopIteration

        self._next_frame = self._next_frame + 1 if self._next_frame < len(self) - 1 else None
        return parse_md_geom_frame(block)

    @overload
    def __getitem__(self, frame: int) -> MDGeomTimestepInfo: ...

    @overload
    def __getitem__(self, frame: Sequence | slice) -> list[MDGeomTimestepInfo]: ...

    @singledispatchmethod
    def __getitem__(self, frame) -> list[MDGeomTimestepInfo] | MDGeomTimestepInfo:
        """Get particular frame of md/geom.

        Parameters
        ----------
        frame : int or Sequence or slice
            Frame(s) to extract.

        Returns
        -------
        list[MDGeomTimestepInfo] or MDGeomTimestepInfo
            Requested frames.
        """
        raise NotImplementedError(f"Can't get {frame}th frame.")

    @__getitem__.register
    def _(self, frame: int) -> MDGeomTimestepInfo:
        return self.get_frame(frame)

    @__getitem__.register
    def _(self, frames: Sequence) -> list[MDGeomTimestepInfo]:
        return [self.get_frame(frame) for frame in frames]

    @__getitem__.register
    def _(self, frames: slice) -> list[MDGeomTimestepInfo]:
        range_ = frames.indices(len(self))

        return self[range(*range_)]

    def __del__(self) -> None:
        """Close file before deletion."""
        self._handle.close()

    def __str__(self) -> str:
        """Get file info.

        Returns
        -------
        str
            Summary of MD/geom file.
        """
        return f"""\
File: {self.file}
Frames: {self._len}
Next frame: {self._next_frame}"""
