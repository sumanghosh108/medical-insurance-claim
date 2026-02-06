from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

@dataclass
class FeatureEngineer:
    numeric_features: List[str]
    categorical_features: List[str]
    preprocessor: ColumnTransformer

    def fit(self, df: pd.DataFrame) -> "FeatureEngineer":
        self.preprocessor.fit(df)
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.preprocessor.transform(df)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.preprocessor.fit_transform(df)

def _infer_feature_columns(
    df: pd.DataFrame,
    numeric_features: Optional[Iterable[str]] = None,
    categorical_features: Optional[Iterable[str]] = None,
) -> Tuple[List[str], List[str]]:
    if numeric_features is None:
        numeric_features = df.select_dtypes(include=["number", "bool"]).columns.tolist()
    if categorical_features is None:
        categorical_features = [
            col for col in df.columns if col not in set(numeric_features)
        ]
    return list(numeric_features), list(categorical_features)

def build_feature_engineer(
    df: pd.DataFrame,
    numeric_features: Optional[Iterable[str]] = None,
    categorical_features: Optional[Iterable[str]] = None,
) -> FeatureEngineer:
    numeric_features, categorical_features = _infer_feature_columns(
        df, numeric_features=numeric_features, categorical_features=categorical_features
    )

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )
    return FeatureEngineer(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        preprocessor=preprocessor,
    )