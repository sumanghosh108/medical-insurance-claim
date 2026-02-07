"""CloudWatch Dashboards - Dashboard Building and Management."""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

import boto3

logger = logging.getLogger(__name__)


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    widget_type: str  # metric, log, number, gauge
    title: str
    metrics: Optional[List[List[str]]] = None
    stat: str = "Average"
    period: int = 300
    region: str = "us-east-1"
    yAxis: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to CloudWatch dashboard widget format."""
        widget = {
            'type': self.widget_type,
            'properties': self.properties or {
                'title': self.title,
                'stat': self.stat,
                'period': self.period,
                'region': self.region,
            }
        }
        
        if self.metrics:
            widget['properties']['metrics'] = self.metrics
        
        if self.yAxis:
            widget['properties']['yAxis'] = self.yAxis
        
        if self.annotations:
            widget['properties']['annotations'] = self.annotations
        
        return widget


class MetricDashboard:
    """Dashboard for application metrics."""
    
    def __init__(self, dashboard_name: str, namespace: str = "InsuranceClaims"):
        """
        Initialize metric dashboard.
        
        Args:
            dashboard_name: Name of the dashboard
            namespace: CloudWatch namespace
        """
        self.dashboard_name = dashboard_name
        self.namespace = namespace
        self.widgets: List[DashboardWidget] = []
    
    def add_metric_widget(
        self,
        title: str,
        metric_names: List[str],
        stat: str = "Average",
        period: int = 300,
    ) -> None:
        """
        Add metric widget.
        
        Args:
            title: Widget title
            metric_names: List of metric names
            stat: Statistic (Average, Sum, Maximum, Minimum)
            period: Period in seconds
        """
        metrics = [
            [self.namespace, metric_name]
            for metric_name in metric_names
        ]
        
        widget = DashboardWidget(
            widget_type='metric',
            title=title,
            metrics=metrics,
            stat=stat,
            period=period,
        )
        
        self.widgets.append(widget)
    
    def add_number_widget(
        self,
        title: str,
        metric_name: str,
        stat: str = "Average",
    ) -> None:
        """
        Add number widget.
        
        Args:
            title: Widget title
            metric_name: Metric to display
            stat: Statistic
        """
        widget = DashboardWidget(
            widget_type='number',
            title=title,
            metrics=[[self.namespace, metric_name]],
            stat=stat,
        )
        
        self.widgets.append(widget)
    
    def add_log_widget(
        self,
        title: str,
        log_group: str,
        query: str,
    ) -> None:
        """
        Add log widget.
        
        Args:
            title: Widget title
            log_group: Log group name
            query: CloudWatch Insights query
        """
        widget = DashboardWidget(
            widget_type='log',
            title=title,
            properties={
                'title': title,
                'logGroupNames': [log_group],
                'queryString': query,
            }
        )
        
        self.widgets.append(widget)
    
    def get_dashboard_body(self) -> str:
        """Get dashboard JSON body."""
        body = {
            'widgets': [w.to_dict() for w in self.widgets]
        }
        return json.dumps(body)


class DashboardBuilder:
    """Build and manage CloudWatch dashboards."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize dashboard builder.
        
        Args:
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
    
    def create_dashboard(
        self,
        dashboard_name: str,
        dashboard_body: str,
    ) -> None:
        """
        Create CloudWatch dashboard.
        
        Args:
            dashboard_name: Name of the dashboard
            dashboard_body: Dashboard JSON body
        """
        try:
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=dashboard_body,
            )
            logger.info(f"Created dashboard: {dashboard_name}")
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}", exc_info=True)
    
    def delete_dashboard(self, dashboard_name: str) -> None:
        """
        Delete CloudWatch dashboard.
        
        Args:
            dashboard_name: Name of the dashboard
        """
        try:
            self.cloudwatch.delete_dashboards(
                DashboardNames=[dashboard_name]
            )
            logger.info(f"Deleted dashboard: {dashboard_name}")
        except Exception as e:
            logger.error(f"Failed to delete dashboard: {e}", exc_info=True)
    
    def list_dashboards(self) -> List[str]:
        """
        List all dashboards.
        
        Returns:
            List of dashboard names
        """
        try:
            response = self.cloudwatch.list_dashboards()
            return [d['DashboardName'] for d in response.get('DashboardEntries', [])]
        except Exception as e:
            logger.error(f"Failed to list dashboards: {e}", exc_info=True)
            return []
    
    def create_claims_dashboard(self, namespace: str = "InsuranceClaims") -> None:
        """Create claims processing dashboard."""
        dashboard = MetricDashboard("ClaimsProcessing", namespace)
        
        # Processing metrics
        dashboard.add_metric_widget(
            title="Claim Processing Rate",
            metric_names=["ClaimsReceived", "ClaimsProcessed", "ClaimsRejected"],
        )
        
        # Performance metrics
        dashboard.add_metric_widget(
            title="Processing Duration (ms)",
            metric_names=[
                "DocumentProcessingTime",
                "FraudDetectionTime",
                "ValidationTime",
            ],
        )
        
        # Accuracy
        dashboard.add_number_widget(
            title="Fraud Detection Accuracy",
            metric_name="FraudDetectionAccuracy",
        )
        
        # Errors
        dashboard.add_metric_widget(
            title="Error Count",
            metric_names=["ValidationErrors", "ProcessingErrors", "DatabaseErrors"],
            stat="Sum",
        )
        
        body = dashboard.get_dashboard_body()
        self.create_dashboard("ClaimsProcessing", body)
    
    def create_ml_dashboard(self, namespace: str = "InsuranceClaims") -> None:
        """Create ML monitoring dashboard."""
        dashboard = MetricDashboard("MLMonitoring", namespace)
        
        # Model performance
        dashboard.add_number_widget(
            title="Model Accuracy",
            metric_name="ModelAccuracy",
        )
        
        dashboard.add_number_widget(
            title="Model Precision",
            metric_name="ModelPrecision",
        )
        
        dashboard.add_number_widget(
            title="Model Recall",
            metric_name="ModelRecall",
        )
        
        # Data drift
        dashboard.add_metric_widget(
            title="Data Drift Detection",
            metric_names=["DriftDetectionKS", "DriftDetectionChiSquare"],
        )
        
        # Predictions
        dashboard.add_metric_widget(
            title="Predictions per Minute",
            metric_names=["PredictionLatency", "PredictionThroughput"],
        )
        
        body = dashboard.get_dashboard_body()
        self.create_dashboard("MLMonitoring", body)
    
    def create_infrastructure_dashboard(self, namespace: str = "InsuranceClaims") -> None:
        """Create infrastructure monitoring dashboard."""
        dashboard = MetricDashboard("Infrastructure", namespace)
        
        # Lambda
        dashboard.add_metric_widget(
            title="Lambda Invocations",
            metric_names=["LambdaInvocations", "LambdaDuration", "LambdaErrors"],
        )
        
        # Database
        dashboard.add_metric_widget(
            title="Database Performance",
            metric_names=["DatabaseConnections", "QueryDuration", "DatabaseErrors"],
        )
        
        # S3
        dashboard.add_metric_widget(
            title="S3 Operations",
            metric_names=["S3Uploads", "S3UploadLatency"],
        )
        
        body = dashboard.get_dashboard_body()
        self.create_dashboard("Infrastructure", body)