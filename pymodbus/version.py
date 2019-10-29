"""
Handle the version information here; you should only have to
change the version tuple.

Since we are using twisted's version class, we can also query
the svn version as well using the local .entries file.
"""


class Version(object):

    def __init__(self, package, major, minor, micro, pre=None):
        """

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
        """ Return a string in canonical short version format
        <major>.<minor>.<micro>.<pre>
        """
        if self.pre:
            return '%d.%d.%d.%s' % (self.major, self.minor, self.micro, self.pre)
        else:
            return '%d.%d.%d' % (self.major, self.minor, self.micro)

    def __str__(self):
        """ Returns a string representation of the object

        :returns: A string representation of this object
        """
        return '[%s, version %s]' % (self.package, self.short())


version = Version('pymodbus', 2, 3, 0)


version.__name__ = 'pymodbus'  # fix epydoc error

# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #

__all__ = ["version"]
