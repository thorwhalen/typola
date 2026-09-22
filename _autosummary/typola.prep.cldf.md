# typola.prep.cldf

Parse a CLDF StructureDataset directory into a `Typology`.

CLDF (Cross-Linguistic Data Formats) is the common schema used by WALS,
Grambank, APiCS, SAILS, and many other typological databases. A
StructureDataset directory has these CSV tables:

- `languages.csv`   — one row per language
- `parameters.csv`  — one row per feature (parameter)
- `codes.csv`       — possible values per parameter
- `values.csv`      — long-format observations

This module is deliberately stdlib-and-pandas only (no `pycldf` dependency),
so it stays light and portable.

### Functions

| [`read_cldf_structure_dataset`](#typola.prep.cldf.read_cldf_structure_dataset)(path, \*[, name, ...])   | Load a CLDF StructureDataset directory into a `Typology`.   |
|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|

### typola.prep.cldf.read_cldf_structure_dataset(path, , name=None, citation='')

Load a CLDF StructureDataset directory into a `Typology`.

* **Parameters:**
  * **path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Directory containing the CLDF `*.csv` files. If the path points to a
    parent directory (e.g. a repo root), we also try `<path>/cldf` and
    any nested `cldf` subdirectory found one level down.
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Short identifier. Defaults to the directory name.
  * **citation** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Bibliographic citation string.
* **Return type:**
  [`Typology`](typola.prep.canonical.md#typola.prep.canonical.Typology)
