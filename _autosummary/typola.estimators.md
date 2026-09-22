# typola.estimators

Pluggable count-to-probability estimators.

An *estimator* is a callable that converts a vector of non-negative counts
into a probability distribution (non-negative, sums to 1). The key idea
is that the count→probability step is swappable — so you can easily try
several strategies and test which works best for your task.

## Canonical estimators

- `mle`               — raw proportions (zero probability for unobserved events)
- `laplace(alpha)`    — add-alpha smoothing with a uniform pseudocount
- `jeffreys()`        — Laplace with alpha=0.5 (the Jeffreys-prior Dirichlet)
- `dirichlet(prior)`  — posterior mean under a configurable Dirichlet prior
- `empirical_bayes(global_counts, strength)` — prior built from global counts
- `mix(*(weight, est))` — linear combination of any number of estimators

All are pure callables that accept `np.ndarray` **or** `pd.Series` and
preserve the index of a Series. They all have a `.name` attribute and a
`.params` dict so runs are self-describing.

### Functions

| [`dirichlet`](#typola.estimators.dirichlet)([prior])                             | Posterior mean under a Dirichlet prior.                                   |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`empirical_bayes`](#typola.estimators.empirical_bayes)(global_counts, \*[, strength]) | Smooth local counts toward a global empirical distribution.               |
| [`held_out_score`](#typola.estimators.held_out_score)(estimator, counts_train, ...)   | Fit an estimator on `counts_train` and score it on `counts_test`.         |
| [`jeffreys`](#typola.estimators.jeffreys)()                                     | Jeffreys prior: symmetric Dirichlet with alpha_i = 0.5 for all i.         |
| [`kl_divergence`](#typola.estimators.kl_divergence)(p, q, \*[, eps])                 | KL(p || q) between two probability vectors.                               |
| [`laplace`](#typola.estimators.laplace)([alpha])                               | Add-alpha smoothing.                                                      |
| [`log_likelihood`](#typola.estimators.log_likelihood)(p, counts, \*[, eps])           | Log-likelihood of multinomial counts under distribution p.                |
| [`mix`](#typola.estimators.mix)(\*components)                              | Linear combination of estimators: `mix((0.7, laplace(1)), (0.3, mle()))`. |
| [`mle`](#typola.estimators.mle)()                                          | Raw relative frequencies.                                                 |
| [`normalize`](#typola.estimators.normalize)(counts)                              | Divide by the sum so the result sums to 1.                                |
| [`uniform`](#typola.estimators.uniform)()                                      | Ignore counts; always return the uniform distribution over the support.   |

### Classes

| [`Estimator`](#typola.estimators.Estimator)([name, params])   | Callable that maps count vectors to probability vectors.   |
|------------------------------------------------------------------------------|------------------------------------------------------------|

### *class* typola.estimators.Estimator(name='estimator', params=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Callable that maps count vectors to probability vectors.

Subclasses override `_estimate(counts_array)` to return a numpy
probability vector. The base class handles pandas-Series plumbing,
normalization checks, and the `describe()` / `__repr__` machinery.

### typola.estimators.dirichlet(prior='jeffreys')

Posterior mean under a Dirichlet prior.

The prior vector is the expected pseudocount for each category.
Posterior mean is `(alpha_i + n_i) / sum(alpha + n)`.

* **Parameters:**
  **prior** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`float`](https://docs.python.org/3/builtins/functions.html#float)] | [`float`](https://docs.python.org/3/builtins/functions.html#float)) – 
  - `"jeffreys"` (default) — all 0.5
  - `"uniform"` — all 1.0 (Laplace)
  - `"bayes_laplace"` — alias for `"uniform"`
  - a scalar — symmetric prior with that value
  - a sequence — per-category pseudocounts (length must match counts at call time)
* **Return type:**
  [`Estimator`](typola.estimators.base.md#typola.estimators.base.Estimator)

### typola.estimators.empirical_bayes(global_counts, , strength=1.0)

Smooth local counts toward a global empirical distribution.

The prior is `(global_counts / sum) * strength`. Think of `strength`
as the total pseudocount mass pulled from the global view.

Typical use: smooth family-level counts toward the overall WALS
distribution for that parameter.

* **Parameters:**
  * **global_counts** (`ndarray` | `Series` | [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]) – Count vector to use as the prior shape. Must have the same length as
    the local counts when the estimator is called.
  * **strength** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Total pseudocount mass for the prior. Higher → more shrinkage toward
    the global. 0 recovers MLE (but will fail on zero-count cells — use
    `laplace(1e-6)` or similar as fallback).
* **Return type:**
  [`Estimator`](typola.estimators.base.md#typola.estimators.base.Estimator)

### typola.estimators.held_out_score(estimator, counts_train, counts_test)

Fit an estimator on `counts_train` and score it on `counts_test`.

Returns a dict of metrics:

- `log_likelihood`  — higher is better
- `perplexity`      — exp(-log_likelihood / N_test); lower is better
- `kl_to_empirical` — KL(empirical_test || predicted); 0 is perfect
- `name`            — estimator’s reported name

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### typola.estimators.jeffreys()

Jeffreys prior: symmetric Dirichlet with alpha_i = 0.5 for all i.

* **Return type:**
  [`Estimator`](typola.estimators.base.md#typola.estimators.base.Estimator)

### typola.estimators.kl_divergence(p, q, , eps=1e-12)

KL(p || q) between two probability vectors.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### typola.estimators.laplace(alpha=1.0)

Add-alpha smoothing.

alpha=1      → classic Laplace / add-one
alpha=0.5    → Jeffreys prior (equivalent to `jeffreys()`)
alpha=0      → MLE (but prefer `mle()` for clarity)

* **Return type:**
  [`Estimator`](typola.estimators.base.md#typola.estimators.base.Estimator)

### typola.estimators.log_likelihood(p, counts, , eps=1e-12)

Log-likelihood of multinomial counts under distribution p.

Returns `sum(counts[i] * log(p[i]))` ignoring the normalizing constant.
Useful for comparing two estimators on the same held-out counts.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### typola.estimators.mix(\*components)

Linear combination of estimators: `mix((0.7, laplace(1)), (0.3, mle()))`.

* **Return type:**
  [`Estimator`](typola.estimators.base.md#typola.estimators.base.Estimator)

### typola.estimators.mle()

Raw relative frequencies. Zero probability for unobserved events.

* **Return type:**
  [`Estimator`](typola.estimators.base.md#typola.estimators.base.Estimator)

### typola.estimators.normalize(counts)

Divide by the sum so the result sums to 1. Raises if sum is 0.

* **Return type:**
  `ndarray` | `Series` | [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

### typola.estimators.uniform()

Ignore counts; always return the uniform distribution over the support.

* **Return type:**
  [`Estimator`](typola.estimators.base.md#typola.estimators.base.Estimator)

### Modules

| [`base`](typola.estimators.base.md#module-typola.estimators.base)           | Estimator base class + evaluation utilities.   |
|-----------------------------------------------------------------------------------------------|------------------------------------------------|
| [`smoothing`](typola.estimators.smoothing.md#module-typola.estimators.smoothing) | Concrete count-to-probability estimators.      |
