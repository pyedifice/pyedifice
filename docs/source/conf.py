# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.append(os.path.abspath("../.."))
sys.path.append(os.path.abspath("./image"))

project = "Edifice"
release = "2.6.0"
# Copyright is broken, renders as '1980, David Ding' for some reason
# project_copyright = '2021, David Ding'
author = "David Ding, James D. Brock, Viktor Kronvall"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
"sphinx.ext.autodoc",
"sphinx.ext.autosummary",
"sphinx.ext.napoleon",
"sphinx_autodoc_typehints",
"sphinx.ext.viewcode",
"sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = []

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-toc_object_entries
toc_object_entries=False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    # https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/navigation.html#control-the-number-of-navigation-levels
    "navigation_depth": 1,

    # https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/header-links.html#icon-links
    "icon_links": [
        {
            # Label for this link
            "name": "GitHub",
            # URL where the link will redirect
            "url": "https://github.com/pyedifice/pyedifice",
            # Icon class (if "type": "fontawesome"), or path to local image (if "type": "local")
            "icon": "fa-brands fa-github",
            # The type of image to be used (see below for details)
            "type": "fontawesome",
        },
   ],

}

html_logo = "image/EdificePyramid.svg"
html_favicon = "image/EdificePyramid.ico"

# https://github.com/pydata/pydata-sphinx-theme/issues/1238#issuecomment-1463465620
# https://docs.readthedocs.io/en/stable/guides/adding-custom-css.html
html_static_path = ["_static"]
html_css_files = [ "css/custom.css" ]

# https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/layout.html#remove-the-primary-sidebar-from-pages
html_sidebars = {
    # "tutorial": [],
    # "examples": [],
    # "styling": [],
    # "developer_tools": [],
    # "versions": [],
    "**": [],
}

# https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/source-buttons.html#view-source-link
html_show_sourcelink = False
