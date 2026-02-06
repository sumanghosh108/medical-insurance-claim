import numpy as np
from sklearn.datasets import make_classification

from ml_models.fraud_detection import FraudDetectionEnsemble


def test_fraud_detection_ensemble_trains_and_predicts():
    X, y = make_classification(
        n_samples=200,
        n_features=6,
        n_informative=4,
        n_redundant=0,
        n_classes=2,
        weights=[0.9, 0.1],
        random_state=42,
    )

    model = FraudDetectionEnsemble()
    model.train(X, y)

    scores = model.predict(X[:10])

    assert scores.shape == (10,)
    assert np.all((scores >= 0) & (scores <= 1))