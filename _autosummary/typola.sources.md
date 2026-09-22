# typola.sources

Descriptors and downloaders for typology datasets.

Each source is a small immutable object: name, download URL, expected
top-level directory after unzip, citation, license. Downloaders cache
under `typola.data_dir.cache_dir()`.

Add your own sources with `register_source(SourceSpec(...))`.

### Functions

| `get_source`(name)                                                     |                                                                 |
|------------------------------------------------------------------------|-----------------------------------------------------------------|
| `list_sources`()                                                       |                                                                 |
| [`register_source`](#typola.sources.register_source)(spec) | Register a source so `get_source` and `load(name)` can find it. |

### Classes

| [`SourceSpec`](#typola.sources.SourceSpec)(name, url[, citation, license, ...])   | Describe a typology dataset that can be loaded into a `Typology`.   |
|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|

### *class* typola.sources.SourceSpec(name, url, citation='', license='', archive_type='auto', strip_components=0, loader=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Describe a typology dataset that can be loaded into a `Typology`.

#### name

Short identifier used everywhere else (`"wals"`, `"grambank"`, …).

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### url

Direct download URL for a zip/tarball.

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### citation

Citation string to include with derived outputs.

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### license

License of the dataset (e.g. “CC-BY-NC-4.0”).

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### archive_type

`"zip"` or `"tar.gz"`. Auto-detected from URL if left as `"auto"`.

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### strip_components

Top-level directory entries to strip after extraction (for archives
that wrap everything in a single dir named after the release).

* **Type:**
  [*int*](https://docs.python.org/3/builtins/functions.html#int)

#### download(, force=False, verbose=True)

Download & extract the source archive. Returns the extraction root.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### typola.sources.register_source(spec)

Register a source so `get_source` and `load(name)` can find it.

* **Return type:**
  [`SourceSpec`](typola.sources.base.md#typola.sources.base.SourceSpec)

### Modules

| [`base`](typola.sources.base.md#module-typola.sources.base)       | Source specification & registry.        |
|----------------------------------------------------------------------------------------|-----------------------------------------|
| [`catalog`](typola.sources.catalog.md#module-typola.sources.catalog) | Catalog of known typology data sources. |
