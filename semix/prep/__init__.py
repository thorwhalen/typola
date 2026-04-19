"""Data preparation: raw source → canonical `Typology`.

This subpackage is self-contained: you can use it without any of the
probabilistic modeling code. The output of `load(...)` is a plain
`Typology` (four pandas DataFrames) that can be analyzed with any
tool you like.
"""
from semix.prep.canonical import Typology
from semix.prep.loaders import load, load_from_cldf_dir, available_sources
from semix.prep.cldf import read_cldf_structure_dataset
from semix.prep.stores import TypologyStore, CountsStore

__all__ = [
    "Typology",
    "load",
    "load_from_cldf_dir",
    "available_sources",
    "read_cldf_structure_dataset",
    "TypologyStore",
    "CountsStore",
]
