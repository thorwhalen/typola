# typola

typola: probabilistic models over linguistic typology source data.

Public API organized in layers that can be used independently:

- `typola.sources`   — describe and acquire raw typology datasets (WALS, Grambank, …)
- `typola.prep`      — parse raw CLDF data into a canonical `Typology`
- `typola.estimators`— pluggable count-to-probability strategies (MLE, Laplace, Jeffreys, …)
- `typola.models`    — probabilistic models: marginal, conditional, joint
- `typola.query`     — high-level querying / drill-down API

Typical usage:

```default
from typola import load, query, estimators

wals = load("wals")                       # → Typology
dist = query(wals, target="81A",          # Order of Subject and Verb
             given={"family": "Austronesian"},
             estimator=estimators.laplace(alpha=0.5))
dist.to_frame()                           # DataFrame of (code, name, prob)
```

### Functions

| [`load`](#typola.load)(name_or_spec, \*[, local_path, ...])      | Load a typology by name.                                             |
|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`load_from_cldf_dir`](#typola.load_from_cldf_dir)(path, \*[, name, citation]) | Alias: load a typology from a local CLDF directory with no download. |
| [`query`](#typola.query)(typology, target, \*[, given, ...])      | Ask a probabilistic question about the typology.                     |

### Classes

| [`Typology`](#typola.Typology)(name, languages, parameters, codes, ...)   | A categorical typology dataset in canonical form.          |
|------------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| [`Conditional`](#typola.Conditional)(typology, target, given, \*[, ...])     | CPT for P(target | given), over languages of the typology. |
| [`Marginal`](#typola.Marginal)(typology, parameter, \*[, ...])            | Build a `Distribution` over one parameter's values.        |

### *class* typola.Conditional(typology, target, given, , condition=None, parameter_conditions=None, estimator=None, drop_missing=True)

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

### *class* typola.Marginal(typology, parameter, , condition=None, parameter_conditions=None, estimator=None, drop_missing=True)

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

### *class* typola.Typology(name, languages, parameters, codes, values, citation='', metadata=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A categorical typology dataset in canonical form.

#### name

Short identifier like `"wals"` or `"grambank"`.

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### languages

One row per language. Indexed by `Language_ID`. Expected columns include
`Name`, `Macroarea`, `Latitude`, `Longitude`, `Glottocode`, `Family`.

* **Type:**
  pd.DataFrame

#### parameters

One row per parameter (grammatical feature). Indexed by `Parameter_ID`.
Expected columns: `Name`, `Description`.

* **Type:**
  pd.DataFrame

#### codes

One row per possible value for a parameter. Indexed by `Code_ID`.
Expected columns: `Parameter_ID`, `Name`, `Description`, `Number`.

* **Type:**
  pd.DataFrame

#### values

Long-format observations: one row per (language, parameter) with the observed
value. Columns: `Language_ID`, `Parameter_ID`, `Value`, `Code_ID`, and any
source/comment columns.

* **Type:**
  pd.DataFrame

#### citation

A bibliographic citation string for the dataset.

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str), optional

#### metadata

Any additional metadata (CLDF metadata JSON, download info, etc.).

* **Type:**
  [*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict), optional

#### code_labels(parameter)

Series mapping Code_ID → human-readable name for a parameter.

* **Return type:**
  `Series`

#### counts(parameter, , condition=None, parameter_conditions=None, drop_missing=True)

Count languages by code for a parameter, optionally conditioned.

Returns a Series indexed by `Code_ID` (for parameters that use codes)
or by raw `Value` (when no codes are defined), with integer counts.
Codes present in the parameter’s code table but not observed are
included with count 0.

* **Parameters:**
  * **parameter** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Parameter ID or name (via `parameter_id`).
  * **condition** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Filter on `languages` columns, see `filter_languages`.
  * **parameter_conditions** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Filter to languages whose other-parameter values match, see
    `filter_languages`.
  * **drop_missing** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, ignore rows with NaN / missing / “?” values (common in Grambank).
* **Return type:**
  `Series`

#### filter_languages(condition=None, , parameter_conditions=None)

Return Language_IDs matching language-metadata AND parameter-value conditions.

* **Parameters:**
  * **condition** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – 

    Filter on `languages` columns, `{column: value_or_iterable_or_callable}`:
    - scalar (str / int / bool) → exact match
    - list/tuple/set → membership
    - callable → predicate applied to the column value
  * **parameter_conditions** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – 

    Filter to languages whose values for given parameters match.
    Keys are parameter IDs or names; values can be a single code ID,
    a Value, or an iterable of acceptable codes/values. Example:
    ```default
    parameter_conditions={"83A": "83A-2"}            # OV order
    parameter_conditions={"81A": ["81A-1", "81A-2"]} # SOV or SVO
    ```
  * **IDs.** (*An empty/None condition + empty parameter_conditions → all language*)
* **Return type:**
  `Index`

#### joint_counts(param_a, param_b, , condition=None, parameter_conditions=None, drop_missing=True)

Co-occurrence count table for two parameters.

Rows = codes of `param_a`, columns = codes of `param_b`. Counts are
over languages that have non-missing values for both parameters.

* **Return type:**
  `DataFrame`

#### parameter_id(key)

Resolve a parameter by ID or by (case-insensitive) name prefix.

Raises KeyError if nothing matches.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### *property* parameter_names *: Series*

Series mapping Parameter_ID → Name.

#### values_for(parameter)

Return the values DataFrame filtered to a single parameter.

* **Return type:**
  `DataFrame`

### typola.load(name_or_spec, , local_path=None, download_if_missing=True, verbose=True)

Load a typology by name.

* **Parameters:**
  * **name_or_spec** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`SourceSpec`](typola.sources.base.html.md#typola.sources.base.SourceSpec)) – The registered name (e.g. `"wals"`) or a spec object.
  * **local_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – If given, skip download/cache and load from this directory instead.
    The path can point at the CLDF directory or any ancestor up to the
    dataset root.
  * **download_if_missing** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If False and the source is not cached, raise instead of downloading.
* **Return type:**
  [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)

### typola.load_from_cldf_dir(path, , name=None, citation='')

Alias: load a typology from a local CLDF directory with no download.

* **Return type:**
  [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)

### typola.query(typology, target, , given=None, given_value=None, condition=None, parameter_conditions=None, estimator=None, drop_missing=True)

Ask a probabilistic question about the typology.

* **Parameters:**
  * **typology** ([`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology))
  * **target** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Parameter ID or name to ask about.
  * **given** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Parameter ID or name to condition on. If given without `given_value`,
    the full CPT is returned. With `given_value`, the row distribution
    is returned.
  * **given_value** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – A specific code/value of the `given` parameter.
  * **condition** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Filter on language metadata (see `Typology.filter_languages`).
  * **estimator** ([`Estimator`](typola.estimators.base.html.md#typola.estimators.base.Estimator) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Count-to-probability strategy. Defaults to Jeffreys.
* **Return type:**
  [`Distribution`](typola.models.distribution.html.md#typola.models.distribution.Distribution) | [`Conditional`](typola.models.conditional.html.md#typola.models.conditional.Conditional)
* **Returns:**
  * *Distribution* – When `given` is None, or `given` and `given_value` are both set.
  * *Conditional* – When `given` is a parameter and `given_value` is omitted.

### Modules

| [`sources`](typola.sources.html.md#module-typola.sources)       | Descriptors and downloaders for typology datasets.   |
|--------------------------------------------------------------------------------------|------------------------------------------------------|
| [`estimators`](typola.estimators.html.md#module-typola.estimators) | Pluggable count-to-probability estimators.           |
| [`data_dir`](typola.data_dir.html.md#module-typola.data_dir)     | User-data directory resolution.                      |
| [`models`](typola.models.html.md#module-typola.models)         | Probabilistic models over a `Typology`.              |
| [`prep`](typola.prep.html.md#module-typola.prep)             | Data preparation: raw source → canonical `Typology`. |
