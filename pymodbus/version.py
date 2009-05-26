'''
Handle the version information here; you should only have to
change the version tuple

Since we are using twisted's version class, we can also query
the svn version as well using the local .entries file.
'''
from twisted.python import versions
version = versions.Version('pymodbus', 1, 0, 1)
version.__name__ = "Pymodbus"
