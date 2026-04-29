"""High-level ``load()`` function tying sources ↔ canonical typology.

The data-prep layer never imports the probabilistic-model layer, so
you can use this module in isolation as a CLDF-to-pandas toolkit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from typola.prep.canonical import Typology
from typola.prep.cldf import read_cldf_structure_dataset
from typola.sources.base import SourceSpec, get_source


def available_sources() -> list[str]:
    """List sources known to the registry."""
    from typola.sources.base import list_sources

    return list_sources()


def load(
    name_or_spec: str | SourceSpec,
    *,
    local_path: Optional[str | Path] = None,
    download_if_missing: bool = True,
    verbose: bool = True,
) -> Typology:
    """Load a typology by name.

    Parameters
    ----------
    name_or_spec : str or SourceSpec
        The registered name (e.g. ``"wals"``) or a spec object.
    local_path : path-like, optional
        If given, skip download/cache and load from this directory instead.
        The path can point at the CLDF directory or any ancestor up to the
        dataset root.
    download_if_missing : bool
        If False and the source is not cached, raise instead of downloading.
    """
    spec = get_source(name_or_spec) if isinstance(name_or_spec, str) else name_or_spec

    if local_path is not None:
        return read_cldf_structure_dataset(
            local_path, name=spec.name, citation=spec.citation
        )

    if not spec.is_cached():
        if not download_if_missing:
            raise FileNotFoundError(
                f"{spec.name!r} not cached and download_if_missing=False. "
                f"Call `spec.download()` first or pass local_path=..."
            )
        spec.download(verbose=verbose)

    root = spec.cache_root() / "_extracted"
    return read_cldf_structure_dataset(root, name=spec.name, citation=spec.citation)


def load_from_cldf_dir(
    path: str | Path, *, name: Optional[str] = None, citation: str = ""
) -> Typology:
    """Alias: load a typology from a local CLDF directory with no download."""
    return read_cldf_structure_dataset(path, name=name, citation=citation)
