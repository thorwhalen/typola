"""Parse a CLDF StructureDataset directory into a `Typology`.

CLDF (Cross-Linguistic Data Formats) is the common schema used by WALS,
Grambank, APiCS, SAILS, and many other typological databases. A
StructureDataset directory has these CSV tables:

- ``languages.csv``   — one row per language
- ``parameters.csv``  — one row per feature (parameter)
- ``codes.csv``       — possible values per parameter
- ``values.csv``      — long-format observations

This module is deliberately stdlib-and-pandas only (no ``pycldf`` dependency),
so it stays light and portable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from semix.prep.canonical import Typology

CLDF_TABLES = ("languages", "parameters", "codes", "values")


def read_cldf_structure_dataset(
    path: str | Path,
    *,
    name: Optional[str] = None,
    citation: str = "",
) -> Typology:
    """Load a CLDF StructureDataset directory into a `Typology`.

    Parameters
    ----------
    path : path-like
        Directory containing the CLDF ``*.csv`` files. If the path points to a
        parent directory (e.g. a repo root), we also try ``<path>/cldf`` and
        any nested ``cldf`` subdirectory found one level down.
    name : str, optional
        Short identifier. Defaults to the directory name.
    citation : str, optional
        Bibliographic citation string.
    """
    cldf_dir = _resolve_cldf_dir(Path(path))
    tables = {t: pd.read_csv(cldf_dir / f"{t}.csv", low_memory=False) for t in CLDF_TABLES}

    # Index each table by its primary key (when present).
    for t in ("languages", "parameters", "codes"):
        if "ID" in tables[t].columns:
            tables[t] = tables[t].set_index("ID")

    metadata = _read_metadata(cldf_dir)
    return Typology(
        name=name or cldf_dir.parent.name or cldf_dir.name,
        languages=tables["languages"],
        parameters=tables["parameters"],
        codes=tables["codes"],
        values=tables["values"],
        citation=citation,
        metadata=metadata,
    )


def _resolve_cldf_dir(path: Path) -> Path:
    """Find the directory that actually contains the CLDF CSVs."""
    candidates = [path, path / "cldf"]
    for sub in path.iterdir() if path.is_dir() else []:
        if sub.is_dir() and (sub / "values.csv").exists():
            candidates.append(sub)
        if sub.is_dir() and (sub / "cldf" / "values.csv").exists():
            candidates.append(sub / "cldf")

    for c in candidates:
        if all((c / f"{t}.csv").exists() for t in CLDF_TABLES):
            return c
    raise FileNotFoundError(
        f"No CLDF StructureDataset CSVs found under {path}. "
        f"Looked for: {', '.join(f'{t}.csv' for t in CLDF_TABLES)}"
    )


def _read_metadata(cldf_dir: Path) -> dict:
    """Read CLDF metadata JSON if present."""
    for fname in ("StructureDataset-metadata.json", "metadata.json"):
        f = cldf_dir / fname
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}
