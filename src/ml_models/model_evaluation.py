from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from .fraud_detection import FraudDetectionEnsemble

def evaluate_fraud_model(
    model: FraudDetectionEnsemble,
    X_test: np.ndarray,
    y_test: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, float]:
    scores = model.predict(X_test)
    predictions = (scores >= threshold).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
    }

    if len(np.unique(y_test)) > 1:
        metrics["roc_auc"] = roc_auc_score(y_test, scores)
    else:
        metrics["roc_auc"] = 0.0

    return metrics