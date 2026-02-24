# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'bnbpy'
copyright = '2026, Bruno Scalia C. F. Leite'
author = 'Bruno Scalia C. F. Leite'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode'
]

# Autodoc settings
autodoc_typehints = 'description'
autodoc_member_order = 'bysource'

napoleon_google_docstring = False
napoleon_numpy_docstring = True

templates_path = ['_templates']
exclude_patterns = [".pyx", ".pxd"]
include_patterns = ["*.rst", "*.py", "*.pyi", "*.ipynb"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_context = {
    "display_github": True,
    "github_user": "bruscalia",
    "github_repo": "bnbpy",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
