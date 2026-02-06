import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

class FraudDetectionEnsemble:
    def __init__(self):
        self.rf_model=None
        self.lr_model=None
        self.isolation_forest=None
        self.scaler=StandardScaler()
    
    def train(self, X_train,y_train):
        X_scaled=self.scaler.fit_transform(X_train)
        
        # Random Forest
        self.rf_model = RandomForestClassifier(n_estimators=100)
        self.rf_model.fit(X_scaled, y_train)
        
        # Logistic Regression
        self.lr_model = LogisticRegression()
        self.lr_model.fit(X_scaled, y_train)
        
        # Isolation Forest
        self.isolation_forest = IsolationForest(contamination=0.02)
        self.isolation_forest.fit(X_scaled)
    
    def predict(self, X):
        """Generate predictions"""
        X_scaled = self.scaler.transform(X)
        
        rf_proba = self.rf_model.predict_proba(X_scaled)[:, 1]
        lr_proba = self.lr_model.predict_proba(X_scaled)[:, 1]
        if_score = self.isolation_forest.score_samples(X_scaled)
        if_normalized = 1 / (1 + np.exp(-if_score))
        
        # Ensemble score
        fraud_score = 0.4 * rf_proba + 0.3 * lr_proba + 0.3 * if_normalized
        
        return fraud_score
    
    def save(self, filepath):
        """Save model"""
        joblib.dump(self, filepath)
    
    @staticmethod
    def load(filepath):
        """Load model"""
        return joblib.load(filepath)
        
        