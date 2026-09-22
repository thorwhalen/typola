"""Data preparation: raw source → canonical `Typology`.

This subpackage is self-contained: you can use it without any of the
probabilistic modeling code. The output of `load(...)` is a plain
`Typology` (four pandas DataFrames) that can be analyzed with any
tool you like.
"""

from typola.prep.canonical import Typology
from typola.prep.cldf import read_cldf_structure_dataset
from typola.prep.loaders import available_sources, load, load_from_cldf_dir
from typola.prep.stores import CountsStore, TypologyStore

__all__ = [
    "CountsStore",
    "Typology",
    "TypologyStore",
    "available_sources",
    "load",
    "load_from_cldf_dir",
    "read_cldf_structure_dataset",
]
