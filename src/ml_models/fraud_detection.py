"""Fraud Detection Ensemble Model."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from typing import Dict, Optional, Any
import joblib
import logging

logger = logging.getLogger(__name__)


class FraudDetectionEnsemble:
    """Hybrid ensemble for fraud detection (RF + LR + IF)."""
    
    def __init__(self, random_state: int = 42, verbose: bool = False):
        """Initialize ensemble."""
        self.random_state = random_state
        self.verbose = verbose
        self.rf_model: Optional[RandomForestClassifier] = None
        self.lr_model: Optional[LogisticRegression] = None
        self.isolation_forest: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: list = []
        self.is_trained = False
    
    def prepare_features(self, claim_df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw claim data."""
        features = pd.DataFrame()
        
        # Claim amount
        features['claim_amount'] = claim_df['claim_amount']
        features['claim_amount_log'] = np.log1p(claim_df['claim_amount'])
        claim_mean = claim_df['claim_amount'].mean()
        claim_std = claim_df['claim_amount'].std() + 1e-8
        features['claim_amount_zscore'] = (claim_df['claim_amount'] - claim_mean) / claim_std
        
        # Time features
        df = claim_df.copy()
        df['claim_date'] = pd.to_datetime(df['claim_date'])
        features['day_of_week'] = df['claim_date'].dt.dayofweek
        features['day_of_month'] = df['claim_date'].dt.day
        features['month'] = df['claim_date'].dt.month
        
        # Hospital stats
        hosp_stats = df.groupby('hospital_id')['claim_amount'].agg(['mean', 'std', 'count']).reset_index()
        hosp_stats.columns = ['hospital_id', 'hosp_avg', 'hosp_std', 'hosp_count']
        df = df.merge(hosp_stats, on='hospital_id', how='left')
        features['hospital_avg'] = df['hosp_avg']
        hosp_std = df['hosp_std'].replace(0, 1)
        features['hospital_deviation'] = (df['claim_amount'] - df['hosp_avg']) / hosp_std
        
        # Patient stats
        pat_stats = df.groupby('patient_id')['claim_amount'].agg(['count', 'sum', 'mean']).reset_index()
        pat_stats.columns = ['patient_id', 'pat_freq', 'pat_total', 'pat_avg']
        df = df.merge(pat_stats, on='patient_id', how='left')
        features['patient_frequency'] = df['pat_freq']
        features['patient_total'] = np.log1p(df['pat_total'])
        
        # Document features
        features['missing_fields'] = claim_df.get('missing_fields', 0)
        
        self.feature_names = features.columns.tolist()
        return features.fillna(0).replace([np.inf, -np.inf], 0)
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        sample_weight: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Train ensemble models."""
        if sample_weight is None:
            n_fraud = y_train.sum()
            n_legit = len(y_train) - n_fraud
            sample_weight = np.where(
                y_train == 1,
                1.0 / (2 * max(n_fraud, 1)),
                1.0 / (2 * max(n_legit, 1)),
            )
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_train)
        self.feature_names = list(X_train.columns)
        
        self.rf_model = RandomForestClassifier(
            n_estimators=200, max_depth=20,
            class_weight='balanced', n_jobs=-1,
            random_state=self.random_state,
        )
        self.rf_model.fit(X_scaled, y_train, sample_weight=sample_weight)
        
        self.lr_model = LogisticRegression(
            solver='lbfgs', max_iter=1000,
            class_weight='balanced',
            random_state=self.random_state,
        )
        self.lr_model.fit(X_scaled, y_train, sample_weight=sample_weight)
        
        self.isolation_forest = IsolationForest(
            contamination=0.02, n_estimators=200,
            random_state=self.random_state, n_jobs=-1,
        )
        self.isolation_forest.fit(X_scaled)
        
        self.is_trained = True
        
        return {
            "rf_score": self.rf_model.score(X_scaled, y_train),
            "lr_score": self.lr_model.score(X_scaled, y_train),
            "samples": len(X_train),
            "fraud_rate": float(y_train.mean()),
        }
    
    def predict(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Generate fraud predictions."""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        rf_prob = self.rf_model.predict_proba(X_scaled)[:, 1]
        lr_prob = self.lr_model.predict_proba(X_scaled)[:, 1]
        if_score = self.isolation_forest.score_samples(X_scaled)
        if_norm = 1 / (1 + np.exp(-if_score))
        
        fraud_score = 0.4 * rf_prob + 0.3 * lr_prob + 0.3 * if_norm
        
        return {
            'fraud_score': fraud_score,
            'prediction': (fraud_score > 0.5).astype(int),
            'confidence': np.maximum(fraud_score, 1 - fraud_score),
        }
    
    def save(self, filepath: str) -> None:
        """Save model to disk."""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        joblib.dump({
            'rf': self.rf_model,
            'lr': self.lr_model,
            'if': self.isolation_forest,
            'scaler': self.scaler,
            'features': self.feature_names,
        }, filepath)
    
    @staticmethod
    def load(filepath: str) -> 'FraudDetectionEnsemble':
        """Load model from disk."""
        data = joblib.load(filepath)
        model = FraudDetectionEnsemble()
        model.rf_model = data['rf']
        model.lr_model = data['lr']
        model.isolation_forest = data['if']
        model.scaler = data['scaler']
        model.feature_names = data['features']
        model.is_trained = True
        return model












# import numpy as np
# import pandas as pd
# from sklearn.ensemble import RandomForestClassifier, IsolationForest
# from sklearn.linear_model import LogisticRegression
# from sklearn.preprocessing import StandardScaler
# import joblib

# class FraudDetectionEnsemble:
#     def __init__(self):
#         self.rf_model=None
#         self.lr_model=None
#         self.isolation_forest=None
#         self.scaler=StandardScaler()
    
#     def train(self, X_train,y_train):
#         if X_train is None or len(X_train) == 0:
#             raise ValueError("Training data cannot be empty.")
#         X_scaled=self.scaler.fit_transform(X_train)
        
#         # Random Forest
#         self.rf_model = RandomForestClassifier(n_estimators=100)
#         self.rf_model.fit(X_scaled, y_train)
        
#         # Logistic Regression
#         self.lr_model = LogisticRegression()
#         self.lr_model.fit(X_scaled, y_train)
        
#         # Isolation Forest
#         self.isolation_forest = IsolationForest(contamination=0.02)
#         self.isolation_forest.fit(X_scaled)
    
#     def predict(self, X):
#         """Generate predictions"""
#         if self.rf_model is None or self.lr_model is None or self.isolation_forest is None:
#             raise ValueError("Model must be trained before prediction.")
#         X_scaled = self.scaler.transform(X)
        
#         rf_proba = self.rf_model.predict_proba(X_scaled)[:, 1]
#         lr_proba = self.lr_model.predict_proba(X_scaled)[:, 1]
#         if_score = self.isolation_forest.score_samples(X_scaled)
#         if_normalized = 1 / (1 + np.exp(-if_score))
        
#         # Ensemble score
#         fraud_score = 0.4 * rf_proba + 0.3 * lr_proba + 0.3 * if_normalized
        
#         return fraud_score
    
#     def save(self, filepath):
#         """Save model"""
#         joblib.dump(self, filepath)
    
#     @staticmethod
#     def load(filepath):
#         """Load model"""
#         return joblib.load(filepath)
        
        