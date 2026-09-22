# typola.models.marginal

Marginal distribution over a parameter’s support, under a condition.

### Classes

| [`Marginal`](#typola.models.marginal.Marginal)(typology, parameter, \*[, ...])   | Build a `Distribution` over one parameter's values.   |
|---------------------------------------------------------------------------------------------|-------------------------------------------------------|

### *class* typola.models.marginal.Marginal(typology, parameter, , condition=None, parameter_conditions=None, estimator=None, drop_missing=True)

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
