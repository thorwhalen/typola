# typola.models.conditional

Conditional distribution: P(target parameter | given parameter).

### Classes

| [`Conditional`](#typola.models.conditional.Conditional)(typology, target, given, \*[, ...])   | CPT for P(target | given), over languages of the typology.   |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------|

### *class* typola.models.conditional.Conditional(typology, target, given, , condition=None, parameter_conditions=None, estimator=None, drop_missing=True)

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
  [`Distribution`](typola.models.distribution.md#typola.models.distribution.Distribution)
