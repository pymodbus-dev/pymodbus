"""Pymodbus Interfaces.

A collection of base classes that are used throughout
the pymodbus library.
"""


class Singleton:  # pylint: disable=too-few-public-methods
    """Singleton base class.

    https://mail.python.org/pipermail/python-list/2007-July/450681.html
    """

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """Create a new instance."""
        if "_inst" not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    "Singleton",
]
