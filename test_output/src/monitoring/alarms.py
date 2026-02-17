"""CloudWatch Alarms - Alarm Management and Configuration."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

import boto3

logger = logging.getLogger(__name__)


@dataclass
class AlarmConfig:
    """Alarm configuration."""
    alarm_name: str
    metric_name: str
    namespace: str
    threshold: float
    comparison_operator: str  # GreaterThanThreshold, LessThanThreshold, etc.
    statistic: str = "Average"  # Average, Sum, Maximum, Minimum
    period: int = 300
    evaluation_periods: int = 1
    alarm_description: str = ""
    alarm_actions: Optional[List[str]] = None
    ok_actions: Optional[List[str]] = None
    insufficient_data_actions: Optional[List[str]] = None


@dataclass
class MetricAlarm:
    """Metric alarm details."""
    alarm_name: str
    state: str  # ALARM, OK, INSUFFICIENT_DATA
    state_reason: str
    state_updated_timestamp: datetime
    alarm_description: str
    metric_name: str
    namespace: str
    threshold: float
    comparison_operator: str
    
    def is_alarming(self) -> bool:
        """Check if alarm is in alarm state."""
        return self.state == "ALARM"


class AlarmManager:
    """Manage CloudWatch alarms."""
    
    def __init__(self, region: str = "ap-south-1"):
        """
        Initialize alarm manager.
        
        Args:
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.alarms: Dict[str, AlarmConfig] = {}
    
    def create_alarm(self, config: AlarmConfig) -> None:
        """
        Create CloudWatch alarm.
        
        Args:
            config: Alarm configuration
        """
        try:
            kwargs = {
                'AlarmName': config.alarm_name,
                'MetricName': config.metric_name,
                'Namespace': config.namespace,
                'Statistic': config.statistic,
                'Period': config.period,
                'EvaluationPeriods': config.evaluation_periods,
                'Threshold': config.threshold,
                'ComparisonOperator': config.comparison_operator,
            }
            
            if config.alarm_description:
                kwargs['AlarmDescription'] = config.alarm_description
            
            if config.alarm_actions:
                kwargs['AlarmActions'] = config.alarm_actions
            
            if config.ok_actions:
                kwargs['OKActions'] = config.ok_actions
            
            if config.insufficient_data_actions:
                kwargs['InsufficientDataActions'] = config.insufficient_data_actions
            
            self.cloudwatch.put_metric_alarm(**kwargs)
            self.alarms[config.alarm_name] = config
            
            logger.info(f"Created alarm: {config.alarm_name}")
        
        except Exception as e:
            logger.error(f"Failed to create alarm: {e}", exc_info=True)
    
    def delete_alarm(self, alarm_name: str) -> None:
        """
        Delete CloudWatch alarm.
        
        Args:
            alarm_name: Name of the alarm
        """
        try:
            self.cloudwatch.delete_alarms(AlarmNames=[alarm_name])
            
            if alarm_name in self.alarms:
                del self.alarms[alarm_name]
            
            logger.info(f"Deleted alarm: {alarm_name}")
        
        except Exception as e:
            logger.error(f"Failed to delete alarm: {e}", exc_info=True)
    
    def get_alarm_state(self, alarm_name: str) -> Optional[MetricAlarm]:
        """
        Get alarm state.
        
        Args:
            alarm_name: Name of the alarm
            
        Returns:
            MetricAlarm object or None
        """
        try:
            response = self.cloudwatch.describe_alarms(
                AlarmNames=[alarm_name]
            )
            
            if response['MetricAlarms']:
                alarm_data = response['MetricAlarms'][0]
                
                return MetricAlarm(
                    alarm_name=alarm_data['AlarmName'],
                    state=alarm_data['StateValue'],
                    state_reason=alarm_data['StateReason'],
                    state_updated_timestamp=alarm_data['StateUpdatedTimestamp'],
                    alarm_description=alarm_data.get('AlarmDescription', ''),
                    metric_name=alarm_data['MetricName'],
                    namespace=alarm_data['Namespace'],
                    threshold=alarm_data['Threshold'],
                    comparison_operator=alarm_data['ComparisonOperator'],
                )
        
        except Exception as e:
            logger.error(f"Failed to get alarm state: {e}", exc_info=True)
        
        return None
    
    def get_all_alarms(self) -> List[MetricAlarm]:
        """Get all alarms."""
        try:
            response = self.cloudwatch.describe_alarms()
            
            alarms = []
            for alarm_data in response.get('MetricAlarms', []):
                alarm = MetricAlarm(
                    alarm_name=alarm_data['AlarmName'],
                    state=alarm_data['StateValue'],
                    state_reason=alarm_data['StateReason'],
                    state_updated_timestamp=alarm_data['StateUpdatedTimestamp'],
                    alarm_description=alarm_data.get('AlarmDescription', ''),
                    metric_name=alarm_data['MetricName'],
                    namespace=alarm_data['Namespace'],
                    threshold=alarm_data['Threshold'],
                    comparison_operator=alarm_data['ComparisonOperator'],
                )
                alarms.append(alarm)
            
            return alarms
        
        except Exception as e:
            logger.error(f"Failed to get alarms: {e}", exc_info=True)
            return []
    
    def get_alarming_alarms(self) -> List[MetricAlarm]:
        """Get all alarms in alarm state."""
        return [a for a in self.get_all_alarms() if a.is_alarming()]
    
    def create_performance_alarms(
        self,
        namespace: str = "InsuranceClaims",
        sns_topic: Optional[str] = None,
    ) -> None:
        """Create standard performance alarms."""
        alarm_actions = [sns_topic] if sns_topic else None
        
        # High latency alarm
        config = AlarmConfig(
            alarm_name="HighProcessingLatency",
            metric_name="ProcessingDuration",
            namespace=namespace,
            threshold=5000,  # 5 seconds
            comparison_operator="GreaterThanThreshold",
            statistic="Average",
            period=300,
            evaluation_periods=2,
            alarm_description="Alert when processing latency exceeds 5 seconds",
            alarm_actions=alarm_actions,
        )
        self.create_alarm(config)
        
        # High error rate alarm
        config = AlarmConfig(
            alarm_name="HighErrorRate",
            metric_name="ErrorCount",
            namespace=namespace,
            threshold=10,
            comparison_operator="GreaterThanThreshold",
            statistic="Sum",
            period=300,
            evaluation_periods=1,
            alarm_description="Alert when error count exceeds 10",
            alarm_actions=alarm_actions,
        )
        self.create_alarm(config)
        
        # Low model accuracy alarm
        config = AlarmConfig(
            alarm_name="LowModelAccuracy",
            metric_name="ModelAccuracy",
            namespace=namespace,
            threshold=0.85,
            comparison_operator="LessThanThreshold",
            statistic="Average",
            period=3600,
            alarm_description="Alert when accuracy drops below 85%",
            alarm_actions=alarm_actions,
        )
        self.create_alarm(config)
    
    def create_infrastructure_alarms(
        self,
        namespace: str = "InsuranceClaims",
        sns_topic: Optional[str] = None,
    ) -> None:
        """Create infrastructure alarms."""
        alarm_actions = [sns_topic] if sns_topic else None
        
        # High database connections
        config = AlarmConfig(
            alarm_name="HighDatabaseConnections",
            metric_name="DatabaseConnections",
            namespace=namespace,
            threshold=80,
            comparison_operator="GreaterThanThreshold",
            statistic="Maximum",
            period=300,
            alarm_description="Alert when DB connections exceed 80",
            alarm_actions=alarm_actions,
        )
        self.create_alarm(config)
        
        # Lambda errors
        config = AlarmConfig(
            alarm_name="LambdaErrors",
            metric_name="LambdaErrors",
            namespace=namespace,
            threshold=5,
            comparison_operator="GreaterThanThreshold",
            statistic="Sum",
            period=300,
            alarm_description="Alert on Lambda function errors",
            alarm_actions=alarm_actions,
        )
        self.create_alarm(config)