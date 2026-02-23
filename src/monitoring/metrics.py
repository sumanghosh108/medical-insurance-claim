"""CloudWatch Metrics - Application and System Metrics."""

import boto3
import time
import statistics
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Metric data point."""
    metric_name: str
    value: float
    unit: str = "Count"
    timestamp: Optional[datetime] = None
    dimensions: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CloudWatchMetrics:
    """CloudWatch metrics integration."""
    
    def __init__(self, namespace: str, region: str = "ap-south-1"):
        """
        Initialize CloudWatch metrics.
        
        Args:
            namespace: CloudWatch namespace
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.namespace = namespace
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.buffer_size = 20
    
    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Put metric data.
        
        Args:
            metric_name: Metric name
            value: Metric value
            unit: Unit of measurement (Count, Seconds, Milliseconds, Bytes, Percent)
            dimensions: Optional dimensions dictionary
            timestamp: Optional timestamp
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': timestamp,
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        self.metrics_buffer.append(metric_data)
        
        if len(self.metrics_buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self) -> None:
        """Flush buffered metrics to CloudWatch."""
        if not self.metrics_buffer:
            return
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=self.metrics_buffer,
            )
            logger.info(f"Flushed {len(self.metrics_buffer)} metrics to CloudWatch")
            self.metrics_buffer = []
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}", exc_info=True)
    
    def put_metric_data_batch(self, metrics: List[MetricData]) -> None:
        """
        Put multiple metric data points.
        
        Args:
            metrics: List of MetricData objects
        """
        for metric in metrics:
            self.put_metric(
                metric.metric_name,
                metric.value,
                metric.unit,
                metric.dimensions,
                metric.timestamp,
            )
    
    def get_metric_statistics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics_list: Optional[List[str]] = None,
        dimensions: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get metric statistics.
        
        Args:
            metric_name: Metric name
            start_time: Start time
            end_time: End time
            period: Period in seconds
            statistics_list: List of statistics (Average, Sum, Minimum, Maximum)
            dimensions: Optional dimensions filter
            
        Returns:
            List of metric data points
        """
        if statistics_list is None:
            statistics_list = ['Average', 'Sum', 'Minimum', 'Maximum']
        
        kwargs = {
            'Namespace': self.namespace,
            'MetricName': metric_name,
            'StartTime': start_time,
            'EndTime': end_time,
            'Period': period,
            'Statistics': statistics_list,
        }
        
        if dimensions:
            kwargs['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        try:
            response = self.cloudwatch.get_metric_statistics(**kwargs)
            return response.get('Datapoints', [])
        except Exception as e:
            logger.error(f"Failed to get metric statistics: {e}", exc_info=True)
            return []
    
    def create_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        threshold: float,
        comparison_operator: str = "GreaterThanThreshold",
        evaluation_periods: int = 1,
        period: int = 300,
        statistic: str = "Average",
        alarm_actions: Optional[List[str]] = None,
    ) -> None:
        """
        Create CloudWatch alarm.
        
        Args:
            alarm_name: Alarm name
            metric_name: Metric name
            threshold: Threshold value
            comparison_operator: Comparison operator
            evaluation_periods: Number of evaluation periods
            period: Period in seconds
            statistic: Statistic type
            alarm_actions: List of SNS topic ARNs
        """
        try:
            kwargs = {
                'AlarmName': alarm_name,
                'MetricName': metric_name,
                'Namespace': self.namespace,
                'Statistic': statistic,
                'Period': period,
                'EvaluationPeriods': evaluation_periods,
                'Threshold': threshold,
                'ComparisonOperator': comparison_operator,
            }
            
            if alarm_actions:
                kwargs['AlarmActions'] = alarm_actions
            
            self.cloudwatch.put_metric_alarm(**kwargs)
            logger.info(f"Created alarm: {alarm_name}")
        except Exception as e:
            logger.error(f"Failed to create alarm: {e}", exc_info=True)


class SystemMetrics:
    """Track system metrics locally."""
    
    def __init__(self):
        """Initialize system metrics."""
        self.start_time = datetime.utcnow()
        self.metrics_history: Dict[str, List[float]] = {}
    
    def track_metric(self, metric_name: str, value: float) -> None:
        """
        Track a metric value.
        
        Args:
            metric_name: Metric name
            value: Metric value
        """
        if metric_name not in self.metrics_history:
            self.metrics_history[metric_name] = []
        
        self.metrics_history[metric_name].append(value)
        logger.debug(f"Tracked {metric_name}={value}")
    
    def get_metric_stats(self, metric_name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.
        
        Args:
            metric_name: Metric name
            
        Returns:
            Dictionary with min, max, mean, count, stdev
        """
        if metric_name not in self.metrics_history:
            return {}
        
        values = self.metrics_history[metric_name]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0,
            'sum': sum(values),
        }
    
    def get_uptime(self) -> timedelta:
        """Get system uptime."""
        return datetime.utcnow() - self.start_time
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics_history.clear()
        logger.info("Metrics reset")


class PerformanceTimer:
    """Context manager for timing code blocks."""
    
    def __init__(
        self,
        name: str,
        metrics_tracker: Optional[SystemMetrics] = None,
    ):
        """
        Initialize timer.
        
        Args:
            name: Timer name
            metrics_tracker: Optional SystemMetrics instance
        """
        self.name = name
        self.metrics_tracker = metrics_tracker
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self):
        """Enter context."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if self.metrics_tracker:
            self.metrics_tracker.track_metric(
                f"{self.name}_duration_seconds",
                duration
            )
        
        logger.debug(f"{self.name} took {duration:.3f}s")
    
    def elapsed(self) -> float:
        """Get elapsed time."""
        if self.end_time is None:
            raise RuntimeError("Timer not finished")
        return self.end_time - self.start_time


def emit_connection_pool_metrics(
    cloudwatch_metrics: CloudWatchMetrics,
    environment: str = "development",
) -> None:
    """
    Emit database connection pool metrics to CloudWatch.
    
    Reads pool stats from LambdaConnectionManager and publishes:
    - db.connections.active (checked out connections)
    - db.connections.idle (checked in connections)
    - db.connections.overflow (overflow connections)
    
    Args:
        cloudwatch_metrics: CloudWatchMetrics instance
        environment: Current environment name
    """
    try:
        from src.database.connection import get_lambda_connection
        conn_mgr = get_lambda_connection()
        pool_stats = conn_mgr.get_pool_stats()
    except RuntimeError:
        logger.debug("Lambda connection not initialized, skipping pool metrics")
        return
    
    dims = {'Environment': environment}
    
    for endpoint_type in ('write', 'read'):
        stats = pool_stats.get(endpoint_type, {})
        if not stats or 'checked_out' not in stats:
            continue
        
        type_dims = {**dims, 'Endpoint': endpoint_type}
        
        cloudwatch_metrics.put_metric(
            metric_name='db.connections.active',
            value=float(stats.get('checked_out', 0)),
            unit='Count',
            dimensions=type_dims,
        )
        cloudwatch_metrics.put_metric(
            metric_name='db.connections.idle',
            value=float(stats.get('checked_in', 0)),
            unit='Count',
            dimensions=type_dims,
        )
        cloudwatch_metrics.put_metric(
            metric_name='db.connections.overflow',
            value=float(stats.get('overflow', 0)),
            unit='Count',
            dimensions=type_dims,
        )
    
    logger.debug("Emitted connection pool metrics to CloudWatch")
