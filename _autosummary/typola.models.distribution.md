# typola.models.distribution

A categorical distribution over a known support, with introspection.

### Classes

| [`Distribution`](#typola.models.distribution.Distribution)(probabilities, counts[, ...])   | A categorical probability distribution with provenance.   |
|-----------------------------------------------------------------------------------------------|-----------------------------------------------------------|

### *class* typola.models.distribution.Distribution(probabilities, counts, support_labels=None, estimator_name='', metadata=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A categorical probability distribution with provenance.

#### probabilities

Non-negative, sums to 1. Index labels the support (typically code IDs).

* **Type:**
  pd.Series

#### counts

Raw counts this distribution was built from; same index as probabilities.

* **Type:**
  pd.Series

#### support_labels

Human-readable name for each support element (e.g. “SVO”), same index.

* **Type:**
  pd.Series

#### estimator_name

The estimator used (“mle”, “laplace”, etc.); useful in comparisons.

* **Type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

#### metadata

Freeform: parameter id, condition, source, etc.

* **Type:**
  [*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict)

#### entropy(, base=2.0)

Shannon entropy of the probability vector (default: bits).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### kl_divergence(other, , eps=1e-12)

KL(self || other), requires compatible supports.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### mode()

Return the label of the most probable support element.

#### normalized_entropy(, base=2.0)

Entropy / log(K): 1 = uniform, 0 = point mass.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### sample(n=1, rng=None)

Sample n outcomes from the distribution.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

#### to_frame()

One row per support element with columns: name, count, probability.

* **Return type:**
  `DataFrame`

#### top_k(k=5)

Return the k most probable outcomes as a DataFrame.

* **Return type:**
  `DataFrame`
