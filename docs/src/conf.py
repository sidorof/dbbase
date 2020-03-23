# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
#import os
#import sys
## sys.path.insert(0, os.path.abspath('.'))
import sphinx_material
import dbbase

# -- Project information -----------------------------------------------------

project = 'dbbase'
copyright = '2020, Don Smiley'
author = 'Don Smiley'

# The full version, including alpha/beta/rc tags
release = dbbase.__version__
pygments_style = "default"
highlight_language = "python3"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    #'sphinx.ext.doctest',
    #'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx_automodapi.automodapi",
    "m2r",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_show_sourcelink = True
html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

extensions.append("sphinx_material")
html_theme_path = sphinx_material.html_theme_path()
html_context = sphinx_material.get_html_context()
html_theme = "sphinx_material"

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = "illustrations/dbbase0_blue_tight_favicon.ico"

# Material theme options (see theme.conf for more information)
html_theme_options = {
    # Set the name of the project to appear in the navigation.
    "nav_title": "dbbase {}".format(release),
    # Set you GA account ID to enable tracking
    # "google_analytics_account": 'here',
    # Specify a base_url used to generate sitemap.xml. If not
    # specified, then no sitemap will be built.
    "base_url": "https://dbbase.github.io",
    # Set the color and the accent color
    "color_primary": "blue",
    # Set the repo location to get a badge with stats
    "repo_url": "https://github.com/sidorof/dbbase/",
    "repo_name": "dbbase",
    # Visible levels of the global TOC; -1 means unlimited
    "globaltoc_depth": 1,
    # If False, expand all TOC entries
    "globaltoc_collapse": True,
    # If True, show hidden TOC entries
    "globaltoc_includehidden": True,
}

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = "%b %d, %Y"

html_use_index = True
html_domain_indices = True


# -- Options for autodoc -----------------------------------------------------

autoclass_content = "class"
autodoc_typehints = "none"
autodoc_default_options = {
    "member-order": "bysource",
    "show-inheritance": True,
}

# -- Options for autosummary -----------------------------------------------------

autosummary_generate = True
autosummary_generate_overwrite = False


# -- Options for napoleon--- -----------------------------------------------------

napoleon_use_rtype = False
