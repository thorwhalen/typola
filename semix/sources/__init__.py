"""Descriptors and downloaders for typology datasets.

Each source is a small immutable object: name, download URL, expected
top-level directory after unzip, citation, license. Downloaders cache
under `semix.data_dir.cache_dir()`.

Add your own sources with `register_source(SourceSpec(...))`.
"""
from semix.sources.base import SourceSpec, list_sources, register_source, get_source
from semix.sources.catalog import WALS, GRAMBANK  # register canonical sources

__all__ = [
    "SourceSpec",
    "list_sources",
    "register_source",
    "get_source",
    "WALS",
    "GRAMBANK",
]
