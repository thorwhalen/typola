# typola.data_dir

User-data directory resolution.

Follows XDG on Linux, Application Support on macOS, and %LOCALAPPDATA% on
Windows. The user can override with `TYPOLA_DATA_DIR`.

### Functions

| [`cache_dir`](#typola.data_dir.cache_dir)()   | Subdirectory for downloaded source archives.                   |
|----------------------------------------------------------------|----------------------------------------------------------------|
| [`data_dir`](#typola.data_dir.data_dir)()    | The root data directory for this package (created if missing). |

### typola.data_dir.cache_dir()

Subdirectory for downloaded source archives.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### typola.data_dir.data_dir()

The root data directory for this package (created if missing).

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
