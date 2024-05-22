# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Edifice'
release = '0.6.2'
# Copyright is broken, renders as '1980, David Ding' for some reason
# project_copyright = '2021, David Ding'
author = 'David Ding, James D. Brock, Viktor Kronvall'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys
sys.path.append(os.path.abspath('../..'))
sys.path.append(os.path.abspath('./image'))

extensions = [
'sphinx.ext.autodoc',
'sphinx.ext.autosummary',
'sphinx.ext.napoleon',
'sphinx_autodoc_typehints',
'sphinx.ext.viewcode'
]

templates_path = ['_templates', 'sphinx_book_theme_override']
exclude_patterns = []

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-toc_object_entries
toc_object_entries=False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_theme_options = {
    "repository_url": "https://github.com/pyedifice/pyedifice",
    "use_repository_button": True,
}

# The globaltoc_maxdepth option doesn't work.
# Override this sbt-sidebar-nav.html file so that we can set maxdepth=2.
# https://github.com/executablebooks/sphinx-book-theme/issues/757
# https://sphinx-book-theme.readthedocs.io/en/latest/sections/sidebar-primary.html#control-the-left-sidebar-items
html_sidebars = {
    "**": ["navbar-logo.html", "sbt-sidebar-nav-override.html"]
}

html_logo = "image/EdificePyramid.svg"
html_favicon = "image/EdificePyramid.ico"
