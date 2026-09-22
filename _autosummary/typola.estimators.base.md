# typola.estimators.base

Estimator base class + evaluation utilities.

An estimator is just a callable `counts -> probabilities` with a name
and a params dict. Making it a small dataclass-like object (rather than
a bare function) lets us carry configuration, log runs reproducibly, and
build an evaluation harness that compares strategies.

### Functions

| [`held_out_score`](#typola.estimators.base.held_out_score)(estimator, counts_train, ...)   | Fit an estimator on `counts_train` and score it on `counts_test`.   |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| [`kl_divergence`](#typola.estimators.base.kl_divergence)(p, q, \*[, eps])                 | KL(p || q) between two probability vectors.                         |
| [`log_likelihood`](#typola.estimators.base.log_likelihood)(p, counts, \*[, eps])           | Log-likelihood of multinomial counts under distribution p.          |
| [`normalize`](#typola.estimators.base.normalize)(counts)                              | Divide by the sum so the result sums to 1.                          |

### Classes

| [`Estimator`](#typola.estimators.base.Estimator)([name, params])   | Callable that maps count vectors to probability vectors.   |
|------------------------------------------------------------------------------|------------------------------------------------------------|

### *class* typola.estimators.base.Estimator(name='estimator', params=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Callable that maps count vectors to probability vectors.

Subclasses override `_estimate(counts_array)` to return a numpy
probability vector. The base class handles pandas-Series plumbing,
normalization checks, and the `describe()` / `__repr__` machinery.

### typola.estimators.base.held_out_score(estimator, counts_train, counts_test)

Fit an estimator on `counts_train` and score it on `counts_test`.

Returns a dict of metrics:

- `log_likelihood`  — higher is better
- `perplexity`      — exp(-log_likelihood / N_test); lower is better
- `kl_to_empirical` — KL(empirical_test || predicted); 0 is perfect
- `name`            — estimator’s reported name

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### typola.estimators.base.kl_divergence(p, q, , eps=1e-12)

KL(p || q) between two probability vectors.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### typola.estimators.base.log_likelihood(p, counts, , eps=1e-12)

Log-likelihood of multinomial counts under distribution p.

Returns `sum(counts[i] * log(p[i]))` ignoring the normalizing constant.
Useful for comparing two estimators on the same held-out counts.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### typola.estimators.base.normalize(counts)

Divide by the sum so the result sums to 1. Raises if sum is 0.

* **Return type:**
  `ndarray` | `Series` | [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]
