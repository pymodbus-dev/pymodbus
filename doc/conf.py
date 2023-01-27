"""Document configuration."""
# -*- coding: utf-8 -*-
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
from recommonmark.parser import CommonMarkParser

from pymodbus import __version__

parent_dir = os.path.abspath(os.pardir)
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, "examples"))
github_doc_root = "https://github.com/pymodbus-dev/pymodbus/tree/master/doc/"

# -- General configuration ------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
    'sphinx.ext.autosectionlabel'
]
source_suffix = ['.rst']
master_doc = 'index'
project = 'PyModbus'
copyright = "See license"
author = "Open Source volunteers"
version = __version__
release = __version__
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = []
html_sidebars = {
    "**": [
        "relations.html",  # needs "show_related": True theme option to display
        "searchbox.html",
    ]
}


def setup(app):
    """Do setup."""
    app.add_config_value(
        "recommonmark_config",
        {
            "url_resolver": lambda url: github_doc_root + url,
            "auto_toc_tree_section": "Contents",
        },
        True,
    )
    app.add_transform(AutoStructify)
