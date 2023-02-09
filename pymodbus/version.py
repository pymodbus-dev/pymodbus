"""Handle the version information here.

you should only have to change the version tuple.
"""


class Version:
    """Manage version."""

    def __init__(self, package, major, minor, micro, pre=None):
        """Initialize.

        :param package: Name of the package that this is a version of.
        :param major: The major version number.
        :param minor: The minor version number.
        :param micro: The micro version number.
        :param pre: The pre release tag
        """
        self.package = package
        self.major = major
        self.minor = minor
        self.micro = micro
        self.pre = pre

    def short(self):
        """Return a string in canonical short version format: <major>.<minor>.<micro>.<pre>."""
        pre = ""
        if self.pre:
            pre = f".{self.pre}"
        return f"{self.major}.{self.minor}.{self.micro}{pre}"

    def __str__(self):
        """Return a string representation of the object.

        :returns: A string representation of this object
        """
        return f"[{self.package}, version {self.short()}]"


version = Version("pymodbus", 3, 1, 3, "")
version.__name__ = (  # fix epydoc error # pylint: disable=attribute-defined-outside-init
    "pymodbus"
)


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #

__all__ = ["version"]
