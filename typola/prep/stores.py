"""dol-backed stores for convenient access to prepped data.

The `Typology` object already holds everything in memory, so these stores
are thin facades that give you a uniform mapping interface over typologies
and their derived artifacts. Useful when you want to compose typola with
other dol-based pipelines.
"""

from __future__ import annotations

from typing import Any, Iterator, Mapping, Optional

import pandas as pd

from typola.prep.canonical import Typology
from typola.prep.loaders import load
from typola.sources.base import list_sources


class TypologyStore(Mapping[str, Typology]):
    """Lazy read-only mapping from source name → Typology.

    Typologies are loaded on first access and cached in memory for the
    lifetime of the store. Unknown names raise `KeyError` — register new
    ones via `typola.sources.register_source(...)`.

    Example
    -------
    >>> ts = TypologyStore()                           # doctest: +SKIP
    >>> sorted(ts)           # ['grambank', 'wals']    # doctest: +SKIP
    >>> ts['wals']           # → Typology (downloads on first call)  # doctest: +SKIP
    >>> 'wals' in ts                                   # doctest: +SKIP
    """

    def __init__(self, *, local_paths: Optional[Mapping[str, str]] = None):
        self._cache: dict[str, Typology] = {}
        self._local_paths = dict(local_paths or {})

    def __iter__(self) -> Iterator[str]:
        return iter(list_sources())

    def __len__(self) -> int:
        return len(list_sources())

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key.lower() in list_sources()

    def __getitem__(self, key: str) -> Typology:
        k = key.lower()
        if k in self._cache:
            return self._cache[k]
        if k not in list_sources():
            raise KeyError(f"Unknown source {key!r}. Known: {list_sources()}")
        local = self._local_paths.get(k)
        tp = load(k, local_path=local) if local else load(k)
        self._cache[k] = tp
        return tp

    def __repr__(self) -> str:
        cached = sorted(self._cache)
        all_ = sorted(list_sources())
        return f"TypologyStore(known={all_}, loaded={cached})"


class CountsStore(Mapping[str, pd.Series]):
    """Read-only mapping: parameter_id → count Series (for one typology).

    Useful when you want to iterate over all parameters, or feed counts into
    a batch estimator comparison.
    """

    def __init__(
        self,
        typology: Typology,
        *,
        condition: Optional[Mapping[str, Any]] = None,
        drop_missing: bool = True,
    ):
        self.typology = typology
        self.condition = dict(condition) if condition else {}
        self.drop_missing = drop_missing

    def __iter__(self) -> Iterator[str]:
        return iter(self.typology.parameters.index)

    def __len__(self) -> int:
        return len(self.typology.parameters)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key in self.typology.parameters.index

    def __getitem__(self, key: str) -> pd.Series:
        if key not in self.typology.parameters.index:
            raise KeyError(key)
        return self.typology.counts(
            key, condition=self.condition, drop_missing=self.drop_missing
        )

    def __repr__(self) -> str:
        cond = f", condition={self.condition}" if self.condition else ""
        return f"CountsStore({self.typology.name}{cond}, n={len(self)})"
