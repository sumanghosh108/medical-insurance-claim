import numpy as np
import pandas as pd

from ml_models.feature_engineering import build_feature_engineer


def test_feature_engineer_handles_numeric_and_categorical():
    df = pd.DataFrame(
        {
            "claim_amount": [100.0, 200.0, 150.0],
            "customer_age": [30, 45, 28],
            "claim_type": ["auto", "home", "auto"],
        }
    )

    feature_engineer = build_feature_engineer(df)
    features = feature_engineer.fit_transform(df)

    assert features.shape[0] == df.shape[0]
    assert not np.isnan(features).any()