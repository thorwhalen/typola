# typola.models

Probabilistic models over a `Typology`.

## Components

- `Distribution` — a single categorical distribution with counts, probabilities,
  support labels, entropy, and top-k methods.
- `Marginal`     — builds a `Distribution` for P(parameter value | condition),
  using a user-specified estimator.
- `Conditional`  — builds a CPT: for every value of a “given” parameter,
  a `Distribution` over a “target” parameter.

### Classes

| [`Conditional`](#typola.models.Conditional)(typology, target, given, \*[, ...])   | CPT for P(target | given), over languages of the typology.   |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| [`Distribution`](#typola.models.Distribution)(probabilities, counts[, ...])        | A categorical probability distribution with provenance.      |
| [`Marginal`](#typola.models.Marginal)(typology, parameter, \*[, ...])          | Build a `Distribution` over one parameter's values.          |

### *class* typola.models.Conditional(typology, target, given, , condition=None, parameter_conditions=None, estimator=None, drop_missing=True)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

CPT for P(target | given), over languages of the typology.

Each row is a value of the `given` parameter; the row is a
`Distribution` over values of the `target` parameter, built from
the joint count table by applying the estimator row-wise.

The matrix form is also exposed as a DataFrame via `.as_matrix()`.

### Example

```pycon
>>> from typola import load, estimators
>>> from typola.models import Conditional
>>> wals = load("wals")
>>> cpt = Conditional(wals, target="83A", given="82A",
...                   estimator=estimators.laplace(0.5))
>>> cpt.as_matrix().head()         # rows = 82A codes, cols = 83A codes
>>> cpt.p_given("82A-1").top_k(3)  # distribution over 83A when 82A=82A-1
```

#### as_matrix()

CPT as a DataFrame (rows = given code, cols = target code).

* **Return type:**
  `DataFrame`

#### mutual_information(, base=2.0)

Pointwise MI I(target; given) in bits.

Computed from the estimator-smoothed joint via row-normalized CPT and
the corresponding marginal over `given`. Useful for ranking which
parameter pairs actually co-vary.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### p_given(given_value)

Distribution over target values given `given_value`.

* **Return type:**
  [`Distribution`](typola.models.distribution.html.md#typola.models.distribution.Distribution)

### *class* typola.models.Distribution(probabilities, counts, support_labels=None, estimator_name='', metadata=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A categorical probability distribution with provenance.

#### probabilities

Non-negative, sums to 1. Index labels the support (typically code IDs).

* **Type:**
  pd.Series

#### counts

Raw counts this distribution was built from; same index as probabilities.

* **Type:**
  pd.Series

#### support_labels

Human-readable name for each support element (e.g. “SVO”), same index.

* **Type:**
  pd.Series

#### estimator_name

The estimator used (“mle”, “laplace”, etc.); useful in comparisons.

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### metadata

Freeform: parameter id, condition, source, etc.

* **Type:**
  [*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict)

#### entropy(, base=2.0)

Shannon entropy of the probability vector (default: bits).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### kl_divergence(other, , eps=1e-12)

KL(self || other), requires compatible supports.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### mode()

Return the label of the most probable support element.

#### normalized_entropy(, base=2.0)

Entropy / log(K): 1 = uniform, 0 = point mass.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### sample(n=1, rng=None)

Sample n outcomes from the distribution.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

#### to_frame()

One row per support element with columns: name, count, probability.

* **Return type:**
  `DataFrame`

#### top_k(k=5)

Return the k most probable outcomes as a DataFrame.

* **Return type:**
  `DataFrame`

### *class* typola.models.Marginal(typology, parameter, , condition=None, parameter_conditions=None, estimator=None, drop_missing=True)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Build a `Distribution` over one parameter’s values.

This is the entry point for `P(parameter value | condition)`. The
condition is any filter on language metadata columns (see
`Typology.filter_languages`). The count→probability strategy is
specified by `estimator`.

### Example

```pycon
>>> from typola import load, estimators
>>> from typola.models import Marginal
>>> wals = load("wals")
>>> dist = Marginal(
...     wals, "81A",
...     condition={"Family": "Austronesian"},
...     estimator=estimators.laplace(0.5),
... ).distribution
>>> dist.top_k(3)
```

### Modules

| [`conditional`](typola.models.conditional.html.md#module-typola.models.conditional)   | Conditional distribution: P(target parameter | given parameter).     |
|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`distribution`](typola.models.distribution.html.md#module-typola.models.distribution) | A categorical distribution over a known support, with introspection. |
| [`marginal`](typola.models.marginal.html.md#module-typola.models.marginal)         | Marginal distribution over a parameter's support, under a condition. |
