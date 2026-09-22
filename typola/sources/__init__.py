"""Descriptors and downloaders for typology datasets.

Each source is a small immutable object: name, download URL, expected
top-level directory after unzip, citation, license. Downloaders cache
under `typola.data_dir.cache_dir()`.

Add your own sources with `register_source(SourceSpec(...))`.
"""

from typola.sources.base import SourceSpec, get_source, list_sources, register_source
from typola.sources.catalog import GRAMBANK, WALS  # register canonical sources

__all__ = [
    "GRAMBANK",
    "WALS",
    "SourceSpec",
    "get_source",
    "list_sources",
    "register_source",
]
