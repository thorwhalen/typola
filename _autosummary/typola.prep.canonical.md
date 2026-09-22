# typola.prep.canonical

Canonical representation of a typology dataset.

A `Typology` is four pandas DataFrames plus a little metadata.
The four-table structure mirrors the CLDF StructureDataset spec, which is
the common ground between WALS, Grambank, APiCS, SAILS, and many others.

### Classes

| [`Typology`](#typola.prep.canonical.Typology)(name, languages, parameters, codes, ...)   | A categorical typology dataset in canonical form.   |
|------------------------------------------------------------------------------------------------------|-----------------------------------------------------|

### *class* typola.prep.canonical.Typology(name, languages, parameters, codes, values, citation='', metadata=<factory>)

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
