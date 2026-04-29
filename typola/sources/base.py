"""Source specification & registry.

A source is a handle for one typology dataset — enough metadata to
download it, cite it, and load it, but no data.
"""

from __future__ import annotations

import hashlib
import io
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from typola import data_dir


@dataclass(frozen=True)
class SourceSpec:
    """Describe a typology dataset that can be loaded into a `Typology`.

    Attributes
    ----------
    name : str
        Short identifier used everywhere else (``"wals"``, ``"grambank"``, ...).
    url : str
        Direct download URL for a zip/tarball.
    citation : str
        Citation string to include with derived outputs.
    license : str
        License of the dataset (e.g. "CC-BY-NC-4.0").
    archive_type : str
        ``"zip"`` or ``"tar.gz"``. Auto-detected from URL if left as ``"auto"``.
    strip_components : int
        Top-level directory entries to strip after extraction (for archives
        that wrap everything in a single dir named after the release).
    """

    name: str
    url: str
    citation: str = ""
    license: str = ""
    archive_type: str = "auto"
    strip_components: int = 0

    # runtime-only; optional override. Not frozen-breaking because dataclass is frozen.
    loader: Optional[Callable] = None

    def cache_root(self) -> Path:
        return data_dir.cache_dir() / self.name

    def is_cached(self) -> bool:
        return self.cache_root().exists() and any(self.cache_root().iterdir())

    def download(self, *, force: bool = False, verbose: bool = True) -> Path:
        """Download & extract the source archive. Returns the extraction root."""
        root = self.cache_root()
        if root.exists() and not force:
            if verbose:
                print(f"[typola] {self.name}: already cached at {root}")
            return root
        if force and root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)

        archive_type = self._detect_archive_type()
        if verbose:
            print(f"[typola] {self.name}: downloading {self.url} ...")
        data = _http_get_bytes(self.url)
        if verbose:
            size_mb = len(data) / (1024 * 1024)
            print(f"[typola] {self.name}: got {size_mb:.1f} MB, extracting...")

        extract_to = root / "_extracted"
        extract_to.mkdir(exist_ok=True)
        _extract(data, archive_type, extract_to)

        # optionally unwrap top-level directory
        entries = [p for p in extract_to.iterdir() if not p.name.startswith(".")]
        if self.strip_components > 0 and len(entries) == 1 and entries[0].is_dir():
            # move children up
            inner = entries[0]
            for child in inner.iterdir():
                shutil.move(str(child), str(extract_to / child.name))
            shutil.rmtree(inner)

        if verbose:
            print(f"[typola] {self.name}: ready at {extract_to}")
        return extract_to

    def _detect_archive_type(self) -> str:
        if self.archive_type != "auto":
            return self.archive_type
        url = self.url.lower()
        if url.endswith(".zip"):
            return "zip"
        if url.endswith(".tar.gz") or url.endswith(".tgz"):
            return "tar.gz"
        raise ValueError(
            f"Could not auto-detect archive type for {self.url}; "
            f"pass archive_type='zip' or 'tar.gz' explicitly."
        )


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, SourceSpec] = {}


def register_source(spec: SourceSpec) -> SourceSpec:
    """Register a source so `get_source` and `load(name)` can find it."""
    _REGISTRY[spec.name.lower()] = spec
    return spec


def get_source(name: str) -> SourceSpec:
    key = name.lower()
    if key not in _REGISTRY:
        raise KeyError(f"Unknown source {name!r}. Known: {sorted(_REGISTRY.keys())}")
    return _REGISTRY[key]


def list_sources() -> list[str]:
    return sorted(_REGISTRY.keys())


# ---------------------------------------------------------------------------
# low-level helpers
# ---------------------------------------------------------------------------


def _http_get_bytes(url: str) -> bytes:
    """Download bytes from a URL. Kept as a thin helper so it's easy to mock."""
    import requests

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        chunks = []
        for chunk in r.iter_content(chunk_size=1 << 20):
            if chunk:
                chunks.append(chunk)
    return b"".join(chunks)


def _extract(data: bytes, archive_type: str, dest: Path) -> None:
    if archive_type == "zip":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(dest)
    elif archive_type == "tar.gz":
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
            t.extractall(dest)
    else:
        raise ValueError(f"Unsupported archive_type: {archive_type}")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
