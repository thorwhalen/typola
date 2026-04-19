"""Catalog of known typology data sources.

Only includes sources with stable public download URLs and permissive-enough
licensing for research use. Users can register more sources with
`register_source(SourceSpec(...))`.

Additional CLDF datasets worth considering (not auto-registered here, but the
same loader should work once you pass a download URL):

- APiCS (Atlas of Pidgin and Creole Language Structures)
- SAILS (South American Indigenous Language Structures)
- PHOIBLE (phonological inventories)
- Lexibank cross-linguistic lexical databases
"""
from semix.sources.base import SourceSpec, register_source

# ---------------------------------------------------------------------------
# WALS
# ---------------------------------------------------------------------------
# The CLDF release is distributed as a GitHub archive. 2020.3 is the most
# recent release used by downstream projects (e.g. dig4el).
#
# Citation: Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013.
#     The World Atlas of Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology.
#     Dataset: https://doi.org/10.5281/zenodo.7385533
# License: CC-BY-NC 4.0 — requires attribution, no commercial use.

WALS = register_source(
    SourceSpec(
        name="wals",
        url="https://github.com/cldf-datasets/wals/archive/refs/heads/master.zip",
        citation=(
            "Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013. "
            "The World Atlas of Language Structures Online. "
            "Leipzig: Max Planck Institute for Evolutionary Anthropology. "
            "https://wals.info/"
        ),
        license="CC-BY-NC-4.0",
        archive_type="zip",
        strip_components=1,
    )
)

# ---------------------------------------------------------------------------
# Grambank 1.0
# ---------------------------------------------------------------------------
# Citation: Skirgård, Hedvig et al. 2023. Grambank v1.0. Zenodo.
#     https://doi.org/10.5281/zenodo.7740140
# License: CC-BY 4.0

GRAMBANK = register_source(
    SourceSpec(
        name="grambank",
        url="https://zenodo.org/record/7740140/files/grambank/grambank-v1.0.3.zip",
        citation=(
            "Skirgård, Hedvig et al. 2023. Grambank v1.0 [Data set]. Zenodo. "
            "https://doi.org/10.5281/zenodo.7740140"
        ),
        license="CC-BY-4.0",
        archive_type="zip",
        strip_components=1,
    )
)
