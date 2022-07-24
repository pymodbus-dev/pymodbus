#!/usr/bin/env python3
# pylint: skip-file
"""Pydoc sub-class for generating documentation for entire packages.

Taken from: http://pyopengl.sourceforge.net/pydoc/OpenGLContext.pydoc.pydoc2.html
Author: Mike Fletcher
"""
import inspect
import logging
import os
import pydoc
import shutil
import string
from string import join, split, strip
import sys

_log = logging.getLogger(__name__)


def classify_class_attrs(cls):
    """Return list of attribute-descriptor tuples.

    For each name in dir(cls), the return list contains a 4-tuple
    with these elements:

        0. The name (a string).

        1. The kind of attribute this is, one of these strings:
               "class method"    created via classmethod()
               "static method"   created via staticmethod()
               "property"        created via property()
               "method"          any other flavor of method
               "data"            not a method

        2. The class which defined this attribute (a class).

        3. The object as obtained directly from the defining class"s
           __dict__, not via getattr.  This is especially important for
           data attributes:  C.data is just a data object, but
           C.__dict__["data"] may be a data descriptor with additional
           info, like a __doc__ string.

    Note: This version is patched to work with Zope Interface-bearing objects
    """
    mro = inspect.getmro(cls)
    names = dir(cls)
    result = []
    for name in names:
        # Get the object associated with the name.
        # Getting an obj from the __dict__ sometimes reveals more than
        # using getattr.  Static and class methods are dramatic examples.
        if name in cls.__dict__:
            obj = cls.__dict__[name]
        else:
            try:
                obj = getattr(cls, name)
            except AttributeError:
                continue

        # Figure out where it was defined.
        homecls = getattr(obj, "__objclass__", None)
        if homecls is None:
            # search the dicts.
            for base in mro:
                if name in base.__dict__:
                    homecls = base
                    break

        # Get the object again, in order to get it from the defining
        # __dict__ instead of via getattr (if possible).
        if homecls is not None and name in homecls.__dict__:
            obj = homecls.__dict__[name]

        # Also get the object via getattr.
        obj_via_getattr = getattr(cls, name)

        # Classify the object.
        if isinstance(obj, staticmethod):
            kind = "static method"
        elif isinstance(obj, classmethod):
            kind = "class method"
        elif isinstance(obj, property):
            kind = "property"
        elif inspect.ismethod(obj_via_getattr) or inspect.ismethoddescriptor(
            obj_via_getattr
        ):
            kind = "method"
        else:
            kind = "data"

        result.append((name, kind, homecls, obj))

    return result


inspect.classify_class_attrs = classify_class_attrs


class DefaultFormatter(pydoc.HTMLDoc):
    """Default formatter."""

    def docmodule(  # noqa: C901
        self, object, name=None, mod=None, packageContext=None, *ignored
    ):  # noqa: C901
        """Produce HTML documentation for a module object."""
        my_name = object.__name__  # ignore the passed-in name
        parts = split(my_name, ".")
        links = []
        for i in range(len(parts) - 1):
            links.append(
                '<a href="%s.html"><font color="#ffffff">%s</font></a>'
                % (join(parts[: i + 1], "."), parts[i])
            )
        linkedname = join(links + parts[-1:], ".")
        head = "<big><big><strong>%s</strong></big></big>" % linkedname
        try:
            path = inspect.getabsfile(object)
            url = path
            if sys.platform == "win32":
                import nturl2path

                url = nturl2path.pathname2url(path)
            filelink = '<a href="file:%s">%s</a>' % (url, path)
        except TypeError:
            filelink = "(built-in)"
        info = []
        if hasattr(object, "__version__"):
            version = str(object.__version__)
            if version[:11] == "$" + "Revision: " and version[-1:] == "$":
                version = strip(version[11:-1])
            info.append("version %s" % self.escape(version))
        if hasattr(object, "__date__"):
            info.append(self.escape(str(object.__date__)))
        if info:
            head = head + " (%s)" % join(info, ", ")
        result = self.heading(
            head, "#ffffff", "#7799ee", '<a href=".">index</a><br>' + filelink
        )

        modules = inspect.getmembers(object, inspect.ismodule)

        classes, cdict = [], {}
        for key, value in inspect.getmembers(object, inspect.isclass):
            if (inspect.getmodule(value) or object) is object:
                classes.append((key, value))
                cdict[key] = cdict[value] = "#" + key
        for key, value in classes:
            for base in value.__bases__:
                key, modname = base.__name__, base.__module__
                module = sys.modules.get(modname)
                if modname != my_name and module and hasattr(module, key):
                    if getattr(module, key) is base:
                        if key not in cdict:
                            cdict[key] = cdict[base] = modname + ".html#" + key
        funcs, fdict = [], {}
        for key, value in inspect.getmembers(object, inspect.isroutine):
            if inspect.isbuiltin(value) or inspect.getmodule(value) is object:
                funcs.append((key, value))
                fdict[key] = "#-" + key
                if inspect.isfunction(value):
                    fdict[value] = fdict[key]
        data = []
        for key, value in inspect.getmembers(object, pydoc.isdata):
            if key not in ["__builtins__", "__doc__"]:
                data.append((key, value))

        doc = self.markup(pydoc.getdoc(object), self.preformat, fdict, cdict)
        doc = doc and "<tt>%s</tt>" % doc
        result = result + "<p>%s</p>\n" % doc

        packageContext.clean(classes, object)
        packageContext.clean(funcs, object)
        packageContext.clean(data, object)

        if hasattr(object, "__path__"):
            modpkgs = []
            modnames = []
            for file in os.listdir(object.__path__[0]):
                path = os.path.join(object.__path__[0], file)
                modname = inspect.getmodulename(file)
                if modname and modname not in modnames:
                    modpkgs.append((modname, my_name, 0, 0))
                    modnames.append(modname)
                elif pydoc.ispackage(path):
                    modpkgs.append((file, my_name, 1, 0))
            modpkgs.sort()
            contents = self.multicolumn(modpkgs, self.modpkglink)
            # #   result = result + self.bigsection(
            # #   "Package Contents", "#ffffff", "#aa55cc", contents)
            result = result + self.moduleSection(object, packageContext)
        elif modules:
            # FIX   contents = self.multicolumn(
            # FIX   modules, lambda (key, value), s=self: s.modulelink(value))
            result = result + self.bigsection("Modules", "#fffff", "#aa55cc", contents)

        if classes:
            # FIX  classlist = map(lambda (key, value): value, classes)
            contents = [
                self.formattree(
                    inspect.getclasstree(classlist, 1), my_name  # noqa: F821
                )
            ]
            for key, value in classes:
                contents.append(self.document(value, key, my_name, fdict, cdict))
            result = result + self.bigsection(
                "Classes", "#ffffff", "#ee77aa", join(contents)
            )
        if funcs:
            contents = []
            for key, value in funcs:
                contents.append(self.document(value, key, my_name, fdict, cdict))
            result = result + self.bigsection(
                "Functions", "#ffffff", "#eeaa77", join(contents)
            )
        if data:
            contents = []
            for key, value in data:
                try:
                    contents.append(self.document(value, key))
                except Exception:  # nosec
                    pass
            result = result + self.bigsection(
                "Data", "#ffffff", "#55aa55", join(contents, "<br>\n")
            )
        if hasattr(object, "__author__"):
            contents = self.markup(str(object.__author__), self.preformat)
            result = result + self.bigsection("Author", "#ffffff", "#7799ee", contents)
        if hasattr(object, "__credits__"):
            contents = self.markup(str(object.__credits__), self.preformat)
            result = result + self.bigsection("Credits", "#ffffff", "#7799ee", contents)

        return result

    def classlink(self, object, modname):
        """Make a link for a class."""
        name, module = object.__name__, sys.modules.get(object.__module__)
        if hasattr(module, name) and getattr(module, name) is object:
            return '<a href="%s.html#%s">%s</a>' % (module.__name__, name, name)
        return pydoc.classname(object, modname)

    def moduleSection(self, object, packageContext):
        """Create a module-links section for the given object (module)"""
        modules = inspect.getmembers(object, inspect.ismodule)
        packageContext.clean(modules, object)
        packageContext.recurseScan(modules)

        if hasattr(object, "__path__"):
            modpkgs = []
            modnames = []
            for file in os.listdir(object.__path__[0]):
                path = os.path.join(object.__path__[0], file)
                modname = inspect.getmodulename(file)
                if modname and modname not in modnames:
                    modpkgs.append((modname, object.__name__, 0, 0))
                    modnames.append(modname)
                elif pydoc.ispackage(path):
                    modpkgs.append((file, object.__name__, 1, 0))
            modpkgs.sort()
            # do more recursion here...
            for (modname, name, ya, yo) in modpkgs:
                packageContext.addInteresting(join((object.__name__, modname), "."))
            items = []
            for (modname, name, ispackage, isshadowed) in modpkgs:
                try:
                    module = pydoc.safeimport("%s.%s" % (name, modname))
                    description, documentation = pydoc.splitdoc(inspect.getdoc(module))
                    if description:
                        txt = f"{self.modpkglink((modname, name, ispackage, isshadowed))} -- {description}"
                        items.append(txt)
                    else:
                        items.append(
                            self.modpkglink((modname, name, ispackage, isshadowed))
                        )
                except:  # noqa: E722
                    items.append(
                        self.modpkglink((modname, name, ispackage, isshadowed))
                    )
            contents = string.join(items, "<br>")
            result = self.bigsection("Package Contents", "#ffffff", "#aa55cc", contents)
        elif modules:
            result = self.bigsection("Modules", "#fffff", "#aa55cc", contents)
        else:
            result = ""
        return result


class AlreadyDone(Exception):
    """Already done."""

    pass


class PackageDocumentationGenerator:
    """A package document generator creates documentation.

    for an entire package using pydoc"s machinery.

    baseModules -- modules which will be included
        and whose included and children modules will be
        considered fair game for documentation
    destinationDirectory -- the directory into which
        the HTML documentation will be written
    recursion -- whether to add modules which are
        referenced by and/or children of base modules
    exclusions -- a list of modules whose contents will
        not be shown in any other module, commonly
        such modules as OpenGL.GL, wxPython.wx etc.
    recursionStops -- a list of modules which will
        explicitly stop recursion (i.e. they will never
        be included), even if they are children of base
        modules.
    formatter -- allows for passing in a custom formatter
        see DefaultFormatter for sample implementation.
    """

    def __init__(
        self,
        baseModules,
        destinationDirectory=".",
        recursion=1,
        exclusions=(),
        recursionStops=(),
        formatter=None,
    ):
        """Initialize."""
        self.destinationDirectory = os.path.abspath(destinationDirectory)
        self.exclusions = {}
        self.warnings = []
        self.baseSpecifiers = {}
        self.completed = {}
        self.recursionStops = {}
        self.recursion = recursion
        for stop in recursionStops:
            self.recursionStops[stop] = 1
        self.pending = []
        for exclusion in exclusions:
            try:
                self.exclusions[exclusion] = pydoc.locate(exclusion)
            except pydoc.ErrorDuringImport:
                self.warn(
                    """Unable to import the module %s which was specified as an exclusion module"""
                    % (repr(exclusion))
                )
        self.formatter = formatter or DefaultFormatter()
        for base in baseModules:
            self.addBase(base)

    def warn(self, message):
        """Get warnings are used for recoverable, but not necessarily ignorable conditions."""
        self.warnings.append(message)

    def info(self, message):
        """Get information/status report."""
        _log.debug(message)

    def addBase(self, specifier):
        """Set the base of the documentation set, only children of these modules will be documented."""
        try:
            self.baseSpecifiers[specifier] = pydoc.locate(specifier)
            self.pending.append(specifier)
        except pydoc.ErrorDuringImport:
            self.warn(
                """Unable to import the module %s which was specified as a base module"""
                % (repr(specifier))
            )

    def addInteresting(self, specifier):
        """Add a module to the list of interesting modules."""
        if self.checkScope(specifier):
            self.pending.append(specifier)
        else:
            self.completed[specifier] = 1

    def checkScope(self, specifier):
        """Check that the specifier is "in scope" for the recursion."""
        if not self.recursion:
            return 0
        items = string.split(specifier, ".")
        stopCheck = items[:]
        while stopCheck:
            name = string.join(items, ".")
            if self.recursionStops.get(name):
                return 0
            elif self.completed.get(name):
                return 0
            del stopCheck[-1]
        while items:
            if self.baseSpecifiers.get(string.join(items, ".")):
                return 1
            del items[-1]
        # was not within any given scope
        return 0

    def process(self):
        """Process.

        Having added all of the base and/or interesting modules,
        proceed to generate the appropriate documentation for each
        module in the appropriate directory, doing the recursion
        as we go.
        """
        try:
            while self.pending:
                try:
                    if self.pending[0] in self.completed:
                        raise AlreadyDone(self.pending[0])
                    self.info("""Start %s""" % (repr(self.pending[0])))
                    object = pydoc.locate(self.pending[0])
                    self.info("""   ... found %s""" % (repr(object.__name__)))
                except AlreadyDone:
                    pass
                except pydoc.ErrorDuringImport as value:
                    self.info("""   ... FAILED %s""" % (repr(value)))
                    self.warn(
                        """Unable to import the module %s""" % (repr(self.pending[0]))
                    )
                except (SystemError, SystemExit) as value:
                    self.info("""   ... FAILED %s""" % (repr(value)))
                    self.warn(
                        """Unable to import the module %s""" % (repr(self.pending[0]))
                    )
                except Exception as value:
                    self.info("""   ... FAILED %s""" % (repr(value)))
                    self.warn(
                        """Unable to import the module %s""" % (repr(self.pending[0]))
                    )
                else:
                    page = self.formatter.page(
                        pydoc.describe(object),
                        self.formatter.docmodule(
                            object,
                            object.__name__,
                            packageContext=self,
                        ),
                    )
                    file = open(
                        os.path.join(
                            self.destinationDirectory,
                            self.pending[0] + ".html",
                        ),
                        "w",
                    )
                    file.write(page)
                    file.close()
                    self.completed[self.pending[0]] = object
                del self.pending[0]
        finally:
            for item in self.warnings:
                _log.info(item)

    def clean(self, objectList, object):
        """Clean.

        Callback from the formatter object asking us to remove
        those items in the key, value pairs where the object is
        imported from one of the excluded modules.
        """
        for key, value in objectList[:]:
            for excludeObject in self.exclusions.values():
                if hasattr(excludeObject, key) and excludeObject is not object:
                    if getattr(excludeObject, key) is value or (
                        hasattr(excludeObject, "__name__")
                        and excludeObject.__name__ == "Numeric"
                    ):
                        objectList[:] = [(k, o) for k, o in objectList if k != key]

    def recurseScan(self, objectList):
        """Process the list of modules.

        trying to add each to the
        list of interesting modules.
        """
        for key, value in objectList:
            self.addInteresting(value.__name__)


# ---------------------------------------------------------------------------#
#  Main Runner
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    if not os.path.exists("./html"):
        os.mkdir("./html")

    print("Building Pydoc API Documentation")
    PackageDocumentationGenerator(
        baseModules=["pymodbus", "__builtin__"],
        destinationDirectory="./html/",
        exclusions=["math", "string"],
        recursionStops=[],
    ).process()

    if os.path.exists("../../../build"):
        shutil.move("html", "../../../build/pydoc")
