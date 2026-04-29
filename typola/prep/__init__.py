"""Data preparation: raw source → canonical `Typology`.

This subpackage is self-contained: you can use it without any of the
probabilistic modeling code. The output of `load(...)` is a plain
`Typology` (four pandas DataFrames) that can be analyzed with any
tool you like.
"""

from typola.prep.canonical import Typology
from typola.prep.loaders import load, load_from_cldf_dir, available_sources
from typola.prep.cldf import read_cldf_structure_dataset
from typola.prep.stores import TypologyStore, CountsStore

__all__ = [
    "Typology",
    "load",
    "load_from_cldf_dir",
    "available_sources",
    "read_cldf_structure_dataset",
    "TypologyStore",
    "CountsStore",
]
