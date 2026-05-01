# typola

Probabilistic models over linguistic typology source data (WALS, Grambank, …).

- **Live demo** (web UI): https://thorwhalen-typola.hf.space/
- **PyPI**: https://pypi.org/project/typola/

**The core idea** is separation of concerns:

- **Data prep** — acquire and canonicalize. Raw CLDF datasets → pandas DataFrames, via one generic loader that works for WALS, Grambank, APiCS, and any other CLDF StructureDataset.
- **Count-to-probability estimators** — first-class, pluggable, comparable. MLE, Laplace, Jeffreys, Dirichlet-Multinomial, empirical-Bayes, mixtures — pick one, configure it, or plug in your own. Same API.
- **Probabilistic models** — `Marginal P(parameter|condition)` and `Conditional P(target|given)` built from counts + an estimator.
- **Query / drill-down** — one entry point (`query`) plus a few small utilities (`compare_estimators`, `cross_validate_estimators`, `rank_associations`, `compare_conditions`) for actually interrogating the model.

You can use any layer on its own. The prep layer is just pandas — no probabilistic-model imports required.

## Install

```bash
pip install -e .
# with optional bayesian extras (ba + spyn):
pip install -e '.[bayesian]'
# with web UI backend:
pip install -e '.[web]'
```


## Web UI

A React probability-console frontend (zodal + shadcn) ships in `webapp/`:

```bash
# 1. Start the API (from repo root):
python -m webapp.api.main
# 2. Start the UI:
cd webapp/ui && npm install && npm run dev
# open http://127.0.0.1:5173
```

See `webapp/README.md` for details.

## 60-second tour

```python
from typola import load, query, estimators
from typola.query import compare_estimators, cross_validate_estimators, rank_associations

# 1. Load a typology. Downloaded & cached on first call.
wals = load("wals")
# Typology(name='wals', n_languages=3573, n_parameters=192, n_codes=1143, n_values=76475)

# 2. P(Order of Subject and Verb) globally — Jeffreys smoothing.
d = query(wals, target="81A", estimator=estimators.jeffreys())
d.top_k(4)
#              name  count  probability
# 81A-1         SOV    564     0.409206
# 81A-2         SVO    488     0.354114
# 81A-7  No dominant    189     0.137369
# 81A-3         VSO     95     0.069228

# 3. Condition on language metadata.
query(wals, target="81A", condition={"Family": "Niger-Congo"}).top_k(3)
#              name  count  probability
# 81A-2         SVO    277     0.911
# 81A-7  No dominant     20     0.066
# 81A-1         SOV      4     0.013

# 4. Full conditional P(target | given) — a CPT.
cpt = query(wals, target="83A", given="81A", estimator=estimators.laplace(0.5))
cpt.as_matrix()          # DataFrame, rows sum to 1
cpt.p_given("81A-2")     # row distribution when subject–verb order is SVO
cpt.mutual_information() # bits

# 5. Compare estimators on the same question.
compare_estimators(
    wals, target="81A",
    condition={"Family": "Austronesian"},
    estimators=[estimators.mle(), estimators.jeffreys(),
                estimators.empirical_bayes(wals.counts("81A").values, strength=20)],
)

# 6. Actually test which estimator is best — cross-validated log-likelihood.
cross_validate_estimators(
    wals, target="81A",
    estimators=[estimators.mle(), estimators.laplace(0.1),
                estimators.laplace(0.5), estimators.laplace(1.0),
                estimators.empirical_bayes(wals.counts("81A").values, strength=20)],
    n_folds=5, random_state=0,
    condition={"Family": "Austronesian"},
)
#                                                             log_likelihood  perplexity
# laplace(alpha=1.0)                                                -44.2886      3.7548
# laplace(alpha=0.5)                                                -44.3577      3.7648
# laplace(alpha=0.1)                                                -44.8365      3.8244
# empirical_bayes(global_counts=..., strength=20.0)                 -45.3420      3.8896
# mle()                                                             -52.9648      5.2109

# 7. Drill down: which parameters are most informative about Subject–Verb order?
rank_associations(wals, target="81A", top_k=5, estimator=estimators.laplace(0.5))
#   parameter_id  parameter_name                                         mutual_information  n_languages
# 0         83A  Order of Object and Verb                                             1.06         1368
# 1         84A  Order of Object, Oblique, and Verb                                   0.99          486
# 2         97A  Rel. between OV and AdjN                                             0.97         1190
# 3         95A  Rel. between OV and AdpN                                             0.96         1039
# 4         96A  Rel. between OV and RelN                                             0.91          807
```

Run `python misc/example_bakeoff.py` for the same flow in full.

## Architecture

```
typola
├── sources/      ← source catalog (WALS, Grambank, ...) + downloader
├── prep/         ← CLDF → Typology → dol stores
├── estimators/   ← count → probability: MLE, Laplace, Jeffreys, Dirichlet, ...
├── models/       ← Distribution, Marginal, Conditional
└── query/        ← query(), compare_estimators(), cross_validate_estimators(), rank_associations(), compare_conditions()
```

Each layer only depends on the ones above it in the list — so you can use the prep layer without any probabilistic code, or you can use estimators on counts from any other source (not just typola).

## Data sources

Currently registered:

| Name        | License      | Source |
|-------------|--------------|--------|
| `wals`      | CC BY-NC 4.0 | <https://wals.info/> — Dryer & Haspelmath 2013 |
| `grambank`  | CC BY 4.0    | <https://grambank.clld.org/> — Skirgård et al. 2023 |

Register more with:

```python
from typola.sources import register_source, SourceSpec
register_source(SourceSpec(
    name="apics",
    url="https://github.com/cldf-datasets/apics/archive/refs/heads/master.zip",
    citation="...",
    license="CC-BY-4.0",
    archive_type="zip",
    strip_components=1,
))
```

The loader handles any CLDF StructureDataset that provides `languages.csv`, `parameters.csv`, `codes.csv`, `values.csv`.

## Custom estimators

Subclass `Estimator` or just provide any callable with a `.name` attribute:

```python
from dataclasses import dataclass, field
from typola.estimators import Estimator
import numpy as np

@dataclass(frozen=True, repr=False)
class _HaldaneMix(Estimator):
    name: str = "haldane_mix"
    params: dict = field(default_factory=lambda: {"alpha": 0.01})

    def _estimate(self, counts):
        a = self.params["alpha"]
        smoothed = counts + a
        return smoothed / smoothed.sum()

estimators_under_test = [_HaldaneMix(), estimators.jeffreys(), ...]
```

## Citing data sources

Every `Typology` carries a `.citation` string. Cite it in any downstream output.

- **WALS** requires attribution (CC BY-NC 4.0), no commercial use.
- **Grambank** is CC BY 4.0.

## License

MIT.
