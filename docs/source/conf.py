# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import datetime
import castep_outputs

project = "castep-outputs"
copyright = f"{datetime.datetime.today().year}, {castep_outputs.__author__}"
author = castep_outputs.__author__
release = castep_outputs.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinxarg.ext",
    "sphinxcontrib.bibtex",
    "myst_nb",
]

autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "inherited-members": False,
    "private-members": False,
    "show-inheritance": True,
}
autodoc_type_aliases = {
    "AtomIndex": "castep_outputs.utilities.datatypes.AtomIndex",
    "ThreeVector": "castep_outputs.utilities.datatypes.ThreeVector",
    "SixVector": "castep_outputs.utilities.datatypes.SixVector",
    "ThreeByThreeMatrix": "castep_outputs.utilities.datatypes.ThreeByThreeMatrix",
    "AtomPropBlock": "castep_outputs.utilities.datatypes.AtomPropBlock",
}
autodoc_member_order = "groupwise"

autosummary_generate = True
autoclass_content = "both"

templates_path = ["_templates"]
exclude_patterns = ["example_data/*"]

bibtex_bibfiles = ["references.bib"]

add_module_names = True
napoleon_include_special_with_doc = True
napoleon_use_param = True
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
