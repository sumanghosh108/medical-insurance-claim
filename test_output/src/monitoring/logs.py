"""CloudWatch Logs - Log Aggregation and Analysis."""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import logging

import boto3

logger = logging.getLogger(__name__)


@dataclass
class LogAlert:
    """Log-based alert configuration."""
    alert_id: str
    pattern: str
    message: str
    log_group: str
    threshold: int
    alert_level: str  # INFO, WARNING, CRITICAL
    timestamp: str
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class LogAggregator:
    """Aggregate and send logs to CloudWatch."""
    
    def __init__(self, log_group: str, region: str = "ap-south-1"):
        """
        Initialize log aggregator.
        
        Args:
            log_group: CloudWatch log group name
            region: AWS region
        """
        self.log_group = log_group
        self.logs = boto3.client('logs', region_name=region)
        self.log_stream = f"app-{datetime.utcnow().strftime('%Y%m%d')}"
        self._ensure_log_group()
        self._ensure_log_stream()
    
    def _ensure_log_group(self) -> None:
        """Ensure log group exists."""
        try:
            self.logs.create_log_group(logGroupName=self.log_group)
        except self.logs.exceptions.ResourceAlreadyExistsException:
            pass
    
    def _ensure_log_stream(self) -> None:
        """Ensure log stream exists."""
        try:
            self.logs.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
            )
        except self.logs.exceptions.ResourceAlreadyExistsException:
            pass
    
    def write_log(
        self,
        message: str,
        log_level: str = "INFO",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Write log to CloudWatch.
        
        Args:
            message: Log message
            log_level: Log level (INFO, WARNING, ERROR, CRITICAL)
            timestamp: Log timestamp
            metadata: Additional metadata
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Format log entry
            log_entry = f"[{log_level}] {message}"
            if metadata:
                log_entry += f" | {metadata}"
            
            # Put log event
            self.logs.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        'message': log_entry,
                        'timestamp': int(timestamp.timestamp() * 1000),
                    }
                ],
            )
            
            logger.debug(f"Logged to CloudWatch: {log_entry}")
        
        except Exception as e:
            logger.error(f"Failed to write log: {e}", exc_info=True)
    
    def query_logs(
        self,
        query_string: str,
        start_time: int,
        end_time: int,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Query logs using CloudWatch Logs Insights.
        
        Args:
            query_string: CloudWatch Insights query
            start_time: Start time (unix timestamp)
            end_time: End time (unix timestamp)
            limit: Max results
            
        Returns:
            List of log records
        """
        try:
            response = self.logs.start_query(
                logGroupName=self.log_group,
                startTime=start_time,
                endTime=end_time,
                queryString=query_string,
                limit=limit,
            )
            
            query_id = response['queryId']
            
            # Wait for query to complete
            import time
            while True:
                response = self.logs.get_query_results(queryId=query_id)
                
                if response['status'] == 'Complete':
                    return response['results']
                
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Failed to query logs: {e}", exc_info=True)
            return []


class LogAnalyzer:
    """Analyze logs for patterns and anomalies."""
    
    def __init__(self):
        """Initialize log analyzer."""
        self.patterns: Dict[str, re.Pattern] = {}
        self.event_counts: Dict[str, int] = defaultdict(int)
    
    def add_pattern(self, name: str, pattern: str) -> None:
        """
        Add log pattern to detect.
        
        Args:
            name: Pattern name
            pattern: Regex pattern
        """
        try:
            self.patterns[name] = re.compile(pattern)
            logger.info(f"Added pattern: {name}")
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
    
    def analyze_logs(self, logs: List[str]) -> Dict[str, List[str]]:
        """
        Analyze logs for patterns.
        
        Args:
            logs: List of log messages
            
        Returns:
            Dictionary mapping pattern names to matching logs
        """
        results = defaultdict(list)
        
        for log in logs:
            for pattern_name, pattern in self.patterns.items():
                if pattern.search(log):
                    results[pattern_name].append(log)
                    self.event_counts[pattern_name] += 1
        
        return dict(results)
    
    def detect_anomalies(
        self,
        logs: List[str],
        baseline_count: Dict[str, int],
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Detect anomalies in logs.
        
        Args:
            logs: List of log messages
            baseline_count: Baseline event counts
            threshold: Anomaly threshold (0-1)
            
        Returns:
            Dictionary with anomaly details
        """
        analyzed = self.analyze_logs(logs)
        anomalies = {}
        
        for pattern_name, matches in analyzed.items():
            baseline = baseline_count.get(pattern_name, 0)
            current = len(matches)
            
            if baseline > 0:
                ratio = current / baseline
                if ratio > (1 + threshold) or ratio < (1 - threshold):
                    anomalies[pattern_name] = {
                        'baseline': baseline,
                        'current': current,
                        'ratio': ratio,
                        'change_percent': (ratio - 1) * 100,
                    }
        
        return anomalies
    
    def get_statistics(self) -> Dict[str, int]:
        """Get event count statistics."""
        return dict(self.event_counts)
    
    def identify_errors(self, logs: List[str]) -> Dict[str, int]:
        """
        Identify and count error types.
        
        Args:
            logs: List of log messages
            
        Returns:
            Dictionary mapping error types to counts
        """
        error_pattern = re.compile(r'\[ERROR\].*?(\w+Error|\w+Exception)')
        errors = defaultdict(int)
        
        for log in logs:
            match = error_pattern.search(log)
            if match:
                error_type = match.group(1)
                errors[error_type] += 1
        
        return dict(errors)
    
    def identify_slow_operations(
        self,
        logs: List[str],
        threshold_ms: float = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Identify slow operations from logs.
        
        Args:
            logs: List of log messages
            threshold_ms: Threshold in milliseconds
            
        Returns:
            List of slow operations sorted by duration
        """
        slow_ops = []
        duration_pattern = re.compile(r'duration[:\s=]+(\d+(?:\.\d+)?)\s*m?s')
        
        for log in logs:
            match = duration_pattern.search(log)
            if match:
                duration = float(match.group(1))
                
                if duration > threshold_ms:
                    slow_ops.append({
                        'log': log,
                        'duration_ms': duration,
                    })
        
        return sorted(slow_ops, key=lambda x: x['duration_ms'], reverse=True)
    
    def extract_metrics_from_logs(
        self,
        logs: List[str],
    ) -> Dict[str, List[float]]:
        """
        Extract numeric metrics from logs.
        
        Args:
            logs: List of log messages
            
        Returns:
            Dictionary mapping metric names to values
        """
        metrics = defaultdict(list)
        metric_pattern = re.compile(r'(\w+)[:\s=]+(\d+(?:\.\d+)?)')
        
        for log in logs:
            matches = metric_pattern.findall(log)
            for metric_name, value in matches:
                try:
                    metrics[metric_name].append(float(value))
                except ValueError:
                    pass
        
        return dict(metrics)