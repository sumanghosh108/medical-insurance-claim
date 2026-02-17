"""Model Evaluation - Cross-validation and Performance Testing."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.model_selection import (
    cross_val_score,
    cross_validate,
    StratifiedKFold,
    KFold,
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CrossValidationResults:
    """Cross-validation results container."""
    model_name: str
    cv_folds: int
    cv_strategy: str
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    std_f1: float
    mean_precision: float
    std_precision: float
    mean_recall: float
    std_recall: float
    fold_scores: Dict[str, List[float]]
    timestamp: str = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def summary(self) -> str:
        """Get summary string."""
        return (
            f"Cross-validation Results ({self.cv_folds}-fold)\n"
            f"Accuracy: {self.mean_accuracy:.4f} ± {self.std_accuracy:.4f}\n"
            f"F1 Score: {self.mean_f1:.4f} ± {self.std_f1:.4f}\n"
            f"Precision: {self.mean_precision:.4f} ± {self.std_precision:.4f}\n"
            f"Recall: {self.mean_recall:.4f} ± {self.std_recall:.4f}"
        )


class ModelEvaluator:
    """Evaluate model performance."""
    
    def __init__(self, model_name: str):
        """Initialize evaluator."""
        self.model_name = model_name
        self.evaluation_history: List[CrossValidationResults] = []
    
    def cross_validate_classification(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        cv: int = 5,
        stratified: bool = True,
    ) -> CrossValidationResults:
        """
        Perform cross-validation for classification.
        
        Args:
            model: Model to evaluate
            X: Features
            y: Labels
            cv: Number of folds
            stratified: Whether to use stratified k-fold
            
        Returns:
            CrossValidationResults object
        """
        # Choose CV strategy
        if stratified:
            cv_strategy = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
            cv_name = 'stratified_kfold'
        else:
            cv_strategy = KFold(n_splits=cv, shuffle=True, random_state=42)
            cv_name = 'kfold'
        
        # Scoring metrics
        scoring = {
            'accuracy': 'accuracy',
            'precision': 'precision',
            'recall': 'recall',
            'f1': 'f1',
        }
        
        # Cross-validate
        cv_results = cross_validate(
            model, X, y,
            cv=cv_strategy,
            scoring=scoring,
            return_train_score=False,
        )
        
        # Extract results
        results = CrossValidationResults(
            model_name=self.model_name,
            cv_folds=cv,
            cv_strategy=cv_name,
            mean_accuracy=float(cv_results['test_accuracy'].mean()),
            std_accuracy=float(cv_results['test_accuracy'].std()),
            mean_f1=float(cv_results['test_f1'].mean()),
            std_f1=float(cv_results['test_f1'].std()),
            mean_precision=float(cv_results['test_precision'].mean()),
            std_precision=float(cv_results['test_precision'].std()),
            mean_recall=float(cv_results['test_recall'].mean()),
            std_recall=float(cv_results['test_recall'].std()),
            fold_scores={
                'accuracy': cv_results['test_accuracy'].tolist(),
                'precision': cv_results['test_precision'].tolist(),
                'recall': cv_results['test_recall'].tolist(),
                'f1': cv_results['test_f1'].tolist(),
            },
        )
        
        self.evaluation_history.append(results)
        logger.info(f"Cross-validation completed for {self.model_name}\n{results.summary()}")
        
        return results
    
    def evaluate_test_set(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        y_pred_proba: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """
        Evaluate model on test set.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            y_pred_proba: Predicted probabilities (for AUC)
            
        Returns:
            Dictionary of metrics
        """
        y_pred = model.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
        }
        
        # Add AUC if probabilities available
        if y_pred_proba is not None:
            try:
                metrics['auc_roc'] = roc_auc_score(y_test, y_pred_proba)
            except ValueError:
                metrics['auc_roc'] = 0.0
        
        logger.info(f"Test set evaluation:\n{pd.Series(metrics)}")
        
        return metrics
    
    def compare_models(
        self,
        models: Dict[str, Any],
        X: np.ndarray,
        y: np.ndarray,
        cv: int = 5,
    ) -> pd.DataFrame:
        """
        Compare multiple models using cross-validation.
        
        Args:
            models: Dictionary mapping model names to model objects
            X: Features
            y: Labels
            cv: Number of folds
            
        Returns:
            DataFrame with comparison results
        """
        results = []
        
        for model_name, model in models.items():
            logger.info(f"Evaluating {model_name}...")
            
            cv_scores = cross_val_score(
                model, X, y,
                cv=cv,
                scoring='f1',
            )
            
            results.append({
                'model': model_name,
                'mean_f1': cv_scores.mean(),
                'std_f1': cv_scores.std(),
                'min_f1': cv_scores.min(),
                'max_f1': cv_scores.max(),
            })
        
        comparison_df = pd.DataFrame(results)
        comparison_df = comparison_df.sort_values('mean_f1', ascending=False)
        
        logger.info(f"Model comparison:\n{comparison_df}")
        
        return comparison_df
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get evaluation summary."""
        if not self.evaluation_history:
            return {'total_evaluations': 0}
        
        latest = self.evaluation_history[-1]
        
        return {
            'model': self.model_name,
            'total_evaluations': len(self.evaluation_history),
            'latest_evaluation': latest.to_dict(),
            'best_accuracy': max(
                e.mean_accuracy for e in self.evaluation_history
            ),
            'best_f1': max(e.mean_f1 for e in self.evaluation_history),
        }


def evaluate_model_performance(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
):
    """
    Evaluate model performance (convenience function).
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Dictionary of metrics
    """
    y_pred = model.predict(X_test)
    
    return {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
    }


def cross_validate_model(
    model,
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
) -> Dict[str, np.ndarray]:
    """
    Cross-validate model (convenience function).
    
    Args:
        model: Model to evaluate
        X: Features
        y: Labels
        cv: Number of folds
        
    Returns:
        Dictionary with cross-validation results
    """
    scoring = {
        'accuracy': 'accuracy',
        'precision': 'precision',
        'recall': 'recall',
        'f1': 'f1',
    }
    
    return cross_validate(
        model, X, y,
        cv=cv,
        scoring=scoring,
        return_train_score=False,
    )