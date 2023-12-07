"""Document configuration."""
#
# PyModbus documentation build configuration file,
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# pylint: skip-file
import os
import sys

from recommonmark.transform import AutoStructify

from pymodbus import __version__ as pymodbus_version


# -- General configuration ------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx_rtd_theme",
    "sphinx.ext.autosectionlabel"
]
source_suffix = [".rst"]
root_doc = "index"
project = "PyModbus"
copyright = "See license"
author = "Open Source volunteers"
if "dev" in pymodbus_version:
    version = "dev"
else:
    version = "v" + pymodbus_version
release = pymodbus_version
language = "en"
exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = []
html_sidebars = {
    "**": [
        "relations.html",  # needs "show_related": True theme option to display
        "searchbox.html",
    ]
}

# -- Specials ----------------------------------------------
parent_dir = os.path.abspath(os.pardir)
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, "examples"))
github = f"https://github.com/pymodbus-dev/pymodbus/blob/{version}/"
extlinks = {'github': (github + '%s', '%s')}

def setup(app):
    """Do setup."""
    app.add_config_value(
        "recommonmark_config",
        {
            "url_resolver": lambda url: github + "doc/" + url,
            "auto_toc_tree_section": "Contents",
        },
        True,
    )
    app.add_transform(AutoStructify)
