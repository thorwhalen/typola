# typola.prep.stores

dol-backed stores for convenient access to prepped data.

The `Typology` object already holds everything in memory, so these stores
are thin facades that give you a uniform mapping interface over typologies
and their derived artifacts. Useful when you want to compose typola with
other dol-based pipelines.

### Classes

| [`CountsStore`](#typola.prep.stores.CountsStore)(typology, \*[, condition, ...])   | Read-only mapping: parameter_id → count Series (for one typology).   |
|------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`TypologyStore`](#typola.prep.stores.TypologyStore)(\*[, local_paths])              | Lazy read-only mapping from source name → Typology.                  |

### *class* typola.prep.stores.CountsStore(typology, , condition=None, drop_missing=True)

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), `Series`]

Read-only mapping: parameter_id → count Series (for one typology).

Useful when you want to iterate over all parameters, or feed counts into
a batch estimator comparison.

### *class* typola.prep.stores.TypologyStore(, local_paths=None)

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
