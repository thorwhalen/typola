"""semix: probabilistic models over linguistic typology source data.

Public API organized in layers that can be used independently:

- `semix.sources`   — describe and acquire raw typology datasets (WALS, Grambank, ...)
- `semix.prep`      — parse raw CLDF data into a canonical `Typology`
- `semix.estimators`— pluggable count-to-probability strategies (MLE, Laplace, Jeffreys, ...)
- `semix.models`    — probabilistic models: marginal, conditional, joint
- `semix.query`     — high-level querying / drill-down API

Typical usage::

    from semix import load, query, estimators

    wals = load("wals")                       # → Typology
    dist = query(wals, target="81A",          # Order of Subject and Verb
                 given={"family": "Austronesian"},
                 estimator=estimators.laplace(alpha=0.5))
    dist.to_frame()                           # DataFrame of (code, name, prob)
"""

from semix.prep.canonical import Typology
from semix.prep.loaders import load, load_from_cldf_dir
from semix import sources

__all__ = [
    "Typology",
    "load",
    "load_from_cldf_dir",
    "sources",
]

# Optional subpackages — imported lazily when available so the prep
# layer is usable in isolation.
try:
    from semix import estimators  # noqa: F401
    __all__.append("estimators")
except ImportError:
    pass

try:
    from semix.query.api import query  # noqa: F401
    from semix.models.marginal import Marginal  # noqa: F401
    from semix.models.conditional import Conditional  # noqa: F401
    __all__ += ["query", "Marginal", "Conditional"]
except ImportError:
    pass
