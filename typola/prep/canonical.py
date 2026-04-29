"""Canonical representation of a typology dataset.

A `Typology` is four pandas DataFrames plus a little metadata.
The four-table structure mirrors the CLDF StructureDataset spec, which is
the common ground between WALS, Grambank, APiCS, SAILS, and many others.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import numpy as np
import pandas as pd


@dataclass
class Typology:
    """A categorical typology dataset in canonical form.

    Attributes
    ----------
    name: str
        Short identifier like ``"wals"`` or ``"grambank"``.
    languages: pd.DataFrame
        One row per language. Indexed by ``Language_ID``. Expected columns include
        ``Name``, ``Macroarea``, ``Latitude``, ``Longitude``, ``Glottocode``, ``Family``.
    parameters: pd.DataFrame
        One row per parameter (grammatical feature). Indexed by ``Parameter_ID``.
        Expected columns: ``Name``, ``Description``.
    codes: pd.DataFrame
        One row per possible value for a parameter. Indexed by ``Code_ID``.
        Expected columns: ``Parameter_ID``, ``Name``, ``Description``, ``Number``.
    values: pd.DataFrame
        Long-format observations: one row per (language, parameter) with the observed
        value. Columns: ``Language_ID``, ``Parameter_ID``, ``Value``, ``Code_ID``, and any
        source/comment columns.
    citation: str, optional
        A bibliographic citation string for the dataset.
    metadata: dict, optional
        Any additional metadata (CLDF metadata JSON, download info, etc.).
    """

    name: str
    languages: pd.DataFrame
    parameters: pd.DataFrame
    codes: pd.DataFrame
    values: pd.DataFrame
    citation: str = ""
    metadata: dict = field(default_factory=dict)

    # ----- basic introspection ------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Typology(name={self.name!r}, "
            f"n_languages={len(self.languages)}, "
            f"n_parameters={len(self.parameters)}, "
            f"n_codes={len(self.codes)}, "
            f"n_values={len(self.values)})"
        )

    @property
    def parameter_names(self) -> pd.Series:
        """Series mapping Parameter_ID → Name."""
        if "Name" in self.parameters.columns:
            return self.parameters["Name"]
        return pd.Series(dtype=object)

    def parameter_id(self, key: str) -> str:
        """Resolve a parameter by ID or by (case-insensitive) name prefix.

        Raises KeyError if nothing matches.
        """
        if key in self.parameters.index:
            return key
        names = self.parameter_names.astype(str)
        lowered = names.str.lower()
        key_l = key.lower()
        exact = names[lowered == key_l]
        if len(exact) == 1:
            return exact.index[0]
        prefix = names[lowered.str.startswith(key_l)]
        if len(prefix) == 1:
            return prefix.index[0]
        if len(prefix) > 1:
            raise KeyError(
                f"Ambiguous parameter {key!r}: {prefix.tolist()[:5]} "
                f"(and {max(0, len(prefix) - 5)} more)"
            )
        raise KeyError(f"No parameter matching {key!r}")

    def values_for(self, parameter: str) -> pd.DataFrame:
        """Return the values DataFrame filtered to a single parameter."""
        pid = self.parameter_id(parameter)
        return self.values[self.values["Parameter_ID"] == pid]

    # ----- conditioning on language metadata ---------------------------------

    def filter_languages(
        self,
        condition: Optional[Mapping[str, Any]] = None,
        *,
        parameter_conditions: Optional[Mapping[str, Any]] = None,
    ) -> pd.Index:
        """Return Language_IDs matching language-metadata AND parameter-value conditions.

        Parameters
        ----------
        condition : mapping, optional
            Filter on ``languages`` columns, ``{column: value_or_iterable_or_callable}``:

            - scalar (str / int / bool) → exact match
            - list/tuple/set → membership
            - callable → predicate applied to the column value

        parameter_conditions : mapping, optional
            Filter to languages whose values for given parameters match.
            Keys are parameter IDs or names; values can be a single code ID,
            a Value, or an iterable of acceptable codes/values. Example::

                parameter_conditions={"83A": "83A-2"}            # OV order
                parameter_conditions={"81A": ["81A-1", "81A-2"]} # SOV or SVO

        An empty/None condition + empty parameter_conditions → all language IDs.
        """
        mask = pd.Series(True, index=self.languages.index)

        if condition:
            for col, want in condition.items():
                if col not in self.languages.columns:
                    raise KeyError(
                        f"Condition column {col!r} not in languages. "
                        f"Available: {list(self.languages.columns)}"
                    )
                col_series = self.languages[col]
                if callable(want):
                    mask &= col_series.map(want).fillna(False).astype(bool)
                elif isinstance(want, (list, tuple, set, pd.Index, np.ndarray)):
                    mask &= col_series.isin(list(want))
                else:
                    mask &= col_series == want

        if parameter_conditions:
            for pkey, want in parameter_conditions.items():
                pid = self.parameter_id(pkey)
                sub = self.values[self.values["Parameter_ID"] == pid]
                # Prefer Code_ID, fall back to Value
                use_code = "Code_ID" in sub.columns and sub["Code_ID"].notna().any()
                col = "Code_ID" if use_code else "Value"
                if isinstance(want, (list, tuple, set, pd.Index, np.ndarray)):
                    matching = sub[sub[col].isin(list(want))]["Language_ID"]
                elif callable(want):
                    matching = sub[sub[col].map(want).fillna(False).astype(bool)][
                        "Language_ID"
                    ]
                else:
                    matching = sub[sub[col] == want]["Language_ID"]
                mask &= self.languages.index.isin(matching.to_numpy())

        return self.languages.index[mask]

    # ----- counts -------------------------------------------------------------

    def counts(
        self,
        parameter: str,
        *,
        condition: Optional[Mapping[str, Any]] = None,
        parameter_conditions: Optional[Mapping[str, Any]] = None,
        drop_missing: bool = True,
    ) -> pd.Series:
        """Count languages by code for a parameter, optionally conditioned.

        Returns a Series indexed by ``Code_ID`` (for parameters that use codes)
        or by raw ``Value`` (when no codes are defined), with integer counts.
        Codes present in the parameter's code table but not observed are
        included with count 0.

        Parameters
        ----------
        parameter : str
            Parameter ID or name (via `parameter_id`).
        condition : mapping, optional
            Filter on ``languages`` columns, see `filter_languages`.
        parameter_conditions : mapping, optional
            Filter to languages whose other-parameter values match, see
            `filter_languages`.
        drop_missing : bool
            If True, ignore rows with NaN / missing / "?" values (common in Grambank).
        """
        pid = self.parameter_id(parameter)
        vals = self.values[self.values["Parameter_ID"] == pid]
        if condition or parameter_conditions:
            keep = self.filter_languages(
                condition, parameter_conditions=parameter_conditions
            )
            vals = vals[vals["Language_ID"].isin(keep)]

        # "use_codes" depends on whether the parameter has codes defined,
        # not on whether the filtered slice happens to contain any.
        known_codes = self.codes.index[self.codes["Parameter_ID"] == pid]
        use_codes = len(known_codes) > 0

        col = "Code_ID" if use_codes else "Value"
        observed = vals[col] if col in vals.columns else vals.iloc[:, 0].iloc[0:0]
        if drop_missing:
            observed = observed.dropna()
            observed = observed[observed.astype(str) != "?"]
        counts = observed.value_counts()

        if use_codes:
            counts = counts.reindex(known_codes, fill_value=0)
        return counts.astype(int).sort_index()

    def joint_counts(
        self,
        param_a: str,
        param_b: str,
        *,
        condition: Optional[Mapping[str, Any]] = None,
        parameter_conditions: Optional[Mapping[str, Any]] = None,
        drop_missing: bool = True,
    ) -> pd.DataFrame:
        """Co-occurrence count table for two parameters.

        Rows = codes of ``param_a``, columns = codes of ``param_b``. Counts are
        over languages that have non-missing values for both parameters.
        """
        pa = self.parameter_id(param_a)
        pb = self.parameter_id(param_b)

        va = self.values[self.values["Parameter_ID"] == pa]
        vb = self.values[self.values["Parameter_ID"] == pb]

        if condition or parameter_conditions:
            keep = self.filter_languages(
                condition, parameter_conditions=parameter_conditions
            )
            va = va[va["Language_ID"].isin(keep)]
            vb = vb[vb["Language_ID"].isin(keep)]

        codes_a = self.codes.index[self.codes["Parameter_ID"] == pa]
        codes_b = self.codes.index[self.codes["Parameter_ID"] == pb]
        col_a = "Code_ID" if len(codes_a) > 0 else "Value"
        col_b = "Code_ID" if len(codes_b) > 0 else "Value"

        la = va[["Language_ID", col_a]].rename(columns={col_a: "A"})
        lb = vb[["Language_ID", col_b]].rename(columns={col_b: "B"})
        merged = la.merge(lb, on="Language_ID", how="inner")
        if drop_missing:
            merged = merged.dropna()
            merged = merged[
                (merged["A"].astype(str) != "?") & (merged["B"].astype(str) != "?")
            ]

        if len(merged) == 0:
            # No overlap: return an all-zero matrix with the right shape.
            idx = codes_a if col_a == "Code_ID" else pd.Index([], name="A")
            cols = codes_b if col_b == "Code_ID" else pd.Index([], name="B")
            return pd.DataFrame(0, index=idx, columns=cols, dtype=int)

        ct = pd.crosstab(merged["A"], merged["B"])
        if col_a == "Code_ID":
            ct = ct.reindex(index=codes_a, fill_value=0)
        if col_b == "Code_ID":
            ct = ct.reindex(columns=codes_b, fill_value=0)
        return ct.astype(int)

    # ----- code helpers -------------------------------------------------------

    def code_labels(self, parameter: str) -> pd.Series:
        """Series mapping Code_ID → human-readable name for a parameter."""
        pid = self.parameter_id(parameter)
        sub = self.codes[self.codes["Parameter_ID"] == pid]
        return sub["Name"] if "Name" in sub.columns else pd.Series(dtype=object)
