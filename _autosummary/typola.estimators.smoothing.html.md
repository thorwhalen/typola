# typola.estimators.smoothing

Concrete count-to-probability estimators.

These implement the plug-and-play API described in `typola.estimators`.
Each public function is a **factory** that returns an Estimator instance.
Instances are callables `counts -> probabilities`.

## Numerical notes

- All estimators are total-preserving: the output sums to 1 up to floating
  point. The base class re-normalizes defensively, but implementations
  already return clean normalized output.
- For an all-zero count vector (e.g. a parameter with no observations in the
  conditioning group), MLE raises. All Bayesian/smoothing estimators
  fall back to the prior. Use `uniform()` explicitly if you want strict
  uniform fallback.

### Functions

| [`dirichlet`](#typola.estimators.smoothing.dirichlet)([prior])                             | Posterior mean under a Dirichlet prior.                                   |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`empirical_bayes`](#typola.estimators.smoothing.empirical_bayes)(global_counts, \*[, strength]) | Smooth local counts toward a global empirical distribution.               |
| [`jeffreys`](#typola.estimators.smoothing.jeffreys)()                                     | Jeffreys prior: symmetric Dirichlet with alpha_i = 0.5 for all i.         |
| [`laplace`](#typola.estimators.smoothing.laplace)([alpha])                               | Add-alpha smoothing.                                                      |
| [`mix`](#typola.estimators.smoothing.mix)(\*components)                              | Linear combination of estimators: `mix((0.7, laplace(1)), (0.3, mle()))`. |
| [`mle`](#typola.estimators.smoothing.mle)()                                          | Raw relative frequencies.                                                 |
| [`uniform`](#typola.estimators.smoothing.uniform)()                                      | Ignore counts; always return the uniform distribution over the support.   |

### typola.estimators.smoothing.dirichlet(prior='jeffreys')

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
  [`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator)

### typola.estimators.smoothing.empirical_bayes(global_counts, , strength=1.0)

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
  [`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator)

### typola.estimators.smoothing.jeffreys()

Jeffreys prior: symmetric Dirichlet with alpha_i = 0.5 for all i.

* **Return type:**
  [`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator)

### typola.estimators.smoothing.laplace(alpha=1.0)

Add-alpha smoothing.

alpha=1      → classic Laplace / add-one
alpha=0.5    → Jeffreys prior (equivalent to `jeffreys()`)
alpha=0      → MLE (but prefer `mle()` for clarity)

* **Return type:**
  [`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator)

### typola.estimators.smoothing.mix(\*components)

Linear combination of estimators: `mix((0.7, laplace(1)), (0.3, mle()))`.

* **Return type:**
  [`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator)

### typola.estimators.smoothing.mle()

Raw relative frequencies. Zero probability for unobserved events.

* **Return type:**
  [`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator)

### typola.estimators.smoothing.uniform()

Ignore counts; always return the uniform distribution over the support.

* **Return type:**
  [`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator)
