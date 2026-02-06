from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .feature_engineering import FeatureEngineer, build_feature_engineer
from .fraud_detection import FraudDetectionEnsemble

@dataclass
class TrainingArtifacts:
    model: FraudDetectionEnsemble
    feature_engineer: FeatureEngineer
    X_test: np.ndarray
    y_test: np.ndarray

def train_fraud_detection_model(
    df: pd.DataFrame,
    target_column: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> TrainingArtifacts:
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataframe.")

    X = df.drop(columns=[target_column])
    y = df[target_column].to_numpy()
    if X.empty:
        raise ValueError("Training data is empty after removing target column.")

    feature_engineer = build_feature_engineer(X)
    X_processed = feature_engineer.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=test_size, random_state=random_state, stratify=y
    )

    model = FraudDetectionEnsemble()
    model.train(X_train, y_train)

    return TrainingArtifacts(
        model=model,
        feature_engineer=feature_engineer,
        X_test=X_test,
        y_test=y_test,
    )