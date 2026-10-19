"""Scorecard PD emballée pour MLflow : données brutes en entrée, PD et score en sortie."""

import numpy as np
import pandas as pd
from mlflow.pyfunc import PythonModel
from pandas.api.types import is_bool_dtype, is_numeric_dtype

VARIABLES_CALCULEES = ["duree_mois", "ratio_financement"]


class ScorecardPD(PythonModel):
    def __init__(self, decoupage, coefficients, retenues, candidates, facteur, offset):
        self.decoupage = decoupage              # BinningProcess entraîné (classes et WoE)
        self.coefficients = dict(coefficients)  # "const" + un coefficient par variable retenue
        self.retenues = list(retenues)
        self.candidates = list(candidates)
        self.facteur = facteur
        self.offset = offset

    def _preparer(self, donnees):
        X = donnees.copy()
        X["duree_mois"] = X["montant_credit"] / X["annuite"]
        X["ratio_financement"] = X["montant_credit"] / X["prix_bien"]
        X = X[self.candidates]
        texte = [c for c in X.columns if not is_numeric_dtype(X[c]) or is_bool_dtype(X[c])]
        X[texte] = X[texte].astype(str).astype(object)
        return X

    def predict(self, context, model_input, params=None):
        woe = self.decoupage.transform(self._preparer(model_input), metric="woe", metric_missing="empirical")
        z = self.coefficients["const"] + sum(self.coefficients[v] * woe[v].to_numpy() for v in self.retenues)
        pd_ = 1 / (1 + np.exp(-z))
        return pd.DataFrame({"pd": pd_, "score": self.offset - self.facteur * z}, index=model_input.index)