# typola.prep

Data preparation: raw source → canonical `Typology`.

This subpackage is self-contained: you can use it without any of the
probabilistic modeling code. The output of `load(...)` is a plain
`Typology` (four pandas DataFrames) that can be analyzed with any
tool you like.

### Functions

| [`available_sources`](#typola.prep.available_sources)()                                | List sources known to the registry.                                  |
|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`load`](#typola.prep.load)(name_or_spec, \*[, local_path, ...])          | Load a typology by name.                                             |
| [`load_from_cldf_dir`](#typola.prep.load_from_cldf_dir)(path, \*[, name, citation])     | Alias: load a typology from a local CLDF directory with no download. |
| [`read_cldf_structure_dataset`](#typola.prep.read_cldf_structure_dataset)(path, \*[, name, ...]) | Load a CLDF StructureDataset directory into a `Typology`.            |

### Classes

| [`CountsStore`](#typola.prep.CountsStore)(typology, \*[, condition, ...])       | Read-only mapping: parameter_id → count Series (for one typology).   |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`Typology`](#typola.prep.Typology)(name, languages, parameters, codes, ...) | A categorical typology dataset in canonical form.                    |
| [`TypologyStore`](#typola.prep.TypologyStore)(\*[, local_paths])                  | Lazy read-only mapping from source name → Typology.                  |

### *class* typola.prep.CountsStore(typology, , condition=None, drop_missing=True)

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), `Series`]

Read-only mapping: parameter_id → count Series (for one typology).

Useful when you want to iterate over all parameters, or feed counts into
a batch estimator comparison.

### *class* typola.prep.Typology(name, languages, parameters, codes, values, citation='', metadata=<factory>)

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

### *class* typola.prep.TypologyStore(, local_paths=None)

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)]

Lazy read-only mapping from source name → Typology.

Typologies are loaded on first access and cached in memory for the
lifetime of the store. Unknown names raise `KeyError` — register new
ones via `typola.sources.register_source(...)`.

### Example

```pycon
>>> ts = TypologyStore()
>>> sorted(ts)           # ['grambank', 'wals']
>>> ts['wals']           # → Typology (downloads on first call)
>>> 'wals' in ts
```

### typola.prep.available_sources()

List sources known to the registry.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### typola.prep.load(name_or_spec, , local_path=None, download_if_missing=True, verbose=True)

Load a typology by name.

* **Parameters:**
  * **name_or_spec** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`SourceSpec`](typola.sources.base.html.md#typola.sources.base.SourceSpec)) – The registered name (e.g. `"wals"`) or a spec object.
  * **local_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – If given, skip download/cache and load from this directory instead.
    The path can point at the CLDF directory or any ancestor up to the
    dataset root.
  * **download_if_missing** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If False and the source is not cached, raise instead of downloading.
* **Return type:**
  [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)

### typola.prep.load_from_cldf_dir(path, , name=None, citation='')

Alias: load a typology from a local CLDF directory with no download.

* **Return type:**
  [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)

### typola.prep.read_cldf_structure_dataset(path, , name=None, citation='')

Load a CLDF StructureDataset directory into a `Typology`.

* **Parameters:**
  * **path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Directory containing the CLDF `*.csv` files. If the path points to a
    parent directory (e.g. a repo root), we also try `<path>/cldf` and
    any nested `cldf` subdirectory found one level down.
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Short identifier. Defaults to the directory name.
  * **citation** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Bibliographic citation string.
* **Return type:**
  [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)

### Modules

| [`canonical`](typola.prep.canonical.html.md#module-typola.prep.canonical)   | Canonical representation of a typology dataset.                  |
|-------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`cldf`](typola.prep.cldf.html.md#module-typola.prep.cldf)             | Parse a CLDF StructureDataset directory into a `Typology`.       |
| [`loaders`](typola.prep.loaders.html.md#module-typola.prep.loaders)       | High-level `load()` function tying sources ↔ canonical typology. |
| [`stores`](typola.prep.stores.html.md#module-typola.prep.stores)         | dol-backed stores for convenient access to prepped data.         |
