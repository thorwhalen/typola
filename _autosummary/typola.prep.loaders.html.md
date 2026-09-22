# typola.prep.loaders

High-level `load()` function tying sources ↔ canonical typology.

The data-prep layer never imports the probabilistic-model layer, so
you can use this module in isolation as a CLDF-to-pandas toolkit.

### Functions

| [`available_sources`](#typola.prep.loaders.available_sources)()                            | List sources known to the registry.                                  |
|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`load`](#typola.prep.loaders.load)(name_or_spec, \*[, local_path, ...])      | Load a typology by name.                                             |
| [`load_from_cldf_dir`](#typola.prep.loaders.load_from_cldf_dir)(path, \*[, name, citation]) | Alias: load a typology from a local CLDF directory with no download. |

### typola.prep.loaders.available_sources()

List sources known to the registry.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### typola.prep.loaders.load(name_or_spec, , local_path=None, download_if_missing=True, verbose=True)

Load a typology by name.

* **Parameters:**
  * **name_or_spec** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`SourceSpec`](typola.sources.base.html.md#typola.sources.base.SourceSpec)) – The registered name (e.g. `"wals"`) or a spec object.
  * **local_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – If given, skip download/cache and load from this directory instead.
    The path can point at the CLDF directory or any ancestor up to the
    dataset root.
  * **download_if_missing** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If False and the source is not cached, raise instead of downloading.
* **Return type:**
  [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)

### typola.prep.loaders.load_from_cldf_dir(path, , name=None, citation='')

Alias: load a typology from a local CLDF directory with no download.

* **Return type:**
  [`Typology`](typola.prep.canonical.html.md#typola.prep.canonical.Typology)
