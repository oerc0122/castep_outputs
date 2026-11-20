"""Compat for legacy Python."""

from typing import Any

# 3.14+
# from operator import is_not_none


def is_not_none(x: Any) -> bool:
    """Whether value is none.

    Dummy for pre 3.14.

    Parameters
    ----------
    x
        Value to test.

    Returns
    -------
    bool
        Whether value is None.
    """
    return x is not None
