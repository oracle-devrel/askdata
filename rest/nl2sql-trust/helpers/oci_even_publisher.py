# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

#!/usr/bin/env python3
"""
OCI Monitoring Event Publisher
Sends custom events to OCI Monitoring following Landing Zone structure
"""

import oci
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCIEventPublisher:
    """
    Publisher for sending custom events to OCI Monitoring
    Follows Landing Zone naming conventions and structure
    """
    
    def __init__(self, 
                 config_profile: str = "DEFAULT",
                 compartment_id: Optional[str] = None,
                 region: Optional[str] = None):
        """
        Initialize OCI Event Publisher
        
        Args:
            config_profile: OCI config profile name
            compartment_id: Target compartment OCID (defaults to config compartment)
            region: OCI region (defaults to config region)
        """
        try:
            # Initialize OCI config
            self.config = oci.config.from_file(profile_name=config_profile)
            
            # Override region if provided
            if region:
                self.config['region'] = region
                
            # Initialize monitoring client
            self.monitoring_client = oci.monitoring.MonitoringClient(self.config)
            
            # Set compartment ID
            self.compartment_id = compartment_id or self.config.get('compartment-id')
            if not self.compartment_id:
                raise ValueError("Compartment ID must be provided either in config or as parameter")
                
            # Landing Zone naming convention
            self.namespace = "custom_application_events"  # Following LZ naming
            
            logger.info(f"Initialized OCI Event Publisher for compartment: {self.compartment_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OCI Event Publisher: {e}")
            raise
    
    def send_unable_to_certify_event(self, 
                                   application_name: str,
                                   error_details: Optional[Dict] = None,
                                   severity: str = "CRITICAL",
                                   additional_dimensions: Optional[Dict] = None) -> bool:
        """
        Send unableToCertify event to OCI Monitoring
        
        Args:
            application_name: Name of the application experiencing the issue
            error_details: Additional error information
            severity: Event severity (INFO, WARNING, CRITICAL)
            additional_dimensions: Extra dimensions for filtering/grouping
            
        Returns:
            bool: True if event was sent successfully
        """
        try:
            # Prepare event dimensions (following LZ tagging strategy)
            dimensions = {
                "applicationName": application_name,
                "eventType": "unableToCertify",
                "severity": severity,
                "environment": os.getenv("OCI_ENVIRONMENT", "production"),
                "source": "custom_monitoring"
            }
            
            # Add additional dimensions if provided
            if additional_dimensions:
                dimensions.update(additional_dimensions)
            
            # Prepare metric data
            metric_data = oci.monitoring.models.MetricDataDetails(
                namespace=self.namespace,
                compartment_id=self.compartment_id,
                name="unable_to_certify_event",
                dimensions=dimensions,
                datapoints=[
                    oci.monitoring.models.Datapoint(
                        timestamp=datetime.now(timezone.utc),
                        value=1.0,  # Event occurrence count
                        count=1
                    )
                ],
                metadata={
                    "displayName": "Unable to Certify Event",
                    "unit": "count"
                }
            )
            
            # Send the metric
            post_metric_data_details = oci.monitoring.models.PostMetricDataDetails(
                metric_data=[metric_data]
            )
            
            response = self.monitoring_client.post_metric_data(
                post_metric_data_details=post_metric_data_details
            )
            
            if response.status == 200:
                logger.info(f"Successfully sent unableToCertify event for {application_name}")
                if error_details:
                    logger.info(f"Error details: {json.dumps(error_details, indent=2)}")
                return True
            else:
                logger.error(f"Failed to send event. Status: {response.status}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending unableToCertify event: {e}")
            return False
    
    def send_custom_event(self,
                         event_name: str,
                         metric_value: float,
                         dimensions: Dict[str, str],
                         metric_unit: str = "count") -> bool:
        """
        Send a custom event to OCI Monitoring
        
        Args:
            event_name: Name of the custom event/metric
            metric_value: Numeric value for the metric
            dimensions: Dimensions for filtering and grouping
            metric_unit: Unit of measurement
            
        Returns:
            bool: True if event was sent successfully
        """
        try:
            # Ensure required dimensions for Landing Zone compliance
            base_dimensions = {
                "environment": os.getenv("OCI_ENVIRONMENT", "production"),
                "source": "custom_monitoring"
            }
            base_dimensions.update(dimensions)
            
            metric_data = oci.monitoring.models.MetricDataDetails(
                namespace=self.namespace,
                compartment_id=self.compartment_id,
                name=event_name,
                dimensions=base_dimensions,
                datapoints=[
                    oci.monitoring.models.Datapoint(
                        timestamp=datetime.now(timezone.utc),
                        value=float(metric_value),
                        count=1
                    )
                ],
                metadata={
                    "unit": metric_unit
                }
            )
            
            post_metric_data_details = oci.monitoring.models.PostMetricDataDetails(
                metric_data=[metric_data]
            )
            
            response = self.monitoring_client.post_metric_data(
                post_metric_data_details=post_metric_data_details
            )
            
            success = response.status == 200
            if success:
                logger.info(f"Successfully sent custom event: {event_name}")
            else:
                logger.error(f"Failed to send custom event. Status: {response.status}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending custom event {event_name}: {e}")
            return False
    
    def create_alarm_for_event(self,
                              alarm_name: str,
                              metric_name: str,
                              topic_id: str,
                              threshold: float = 1.0,
                              severity: str = "CRITICAL") -> Optional[str]:
        """
        Create an alarm that triggers when the event occurs
        
        Args:
            alarm_name: Name for the alarm
            metric_name: Metric to monitor
            topic_id: OCID of the notification topic
            threshold: Threshold value for triggering alarm
            severity: Alarm severity
            
        Returns:
            str: Alarm OCID if created successfully, None otherwise
        """
        try:
            # Initialize monitoring client for alarms
            monitoring_client = oci.monitoring.MonitoringClient(self.config)
            
            # Create alarm query
            query = f'{metric_name}[1m].sum() >= {threshold}'
            
            # Create alarm details
            create_alarm_details = oci.monitoring.models.CreateAlarmDetails(
                display_name=alarm_name,
                compartment_id=self.compartment_id,
                metric_compartment_id=self.compartment_id,
                namespace=self.namespace,
                query=query,
                severity=severity,
                destinations=[topic_id],
                is_enabled=True,
                body=f"Alert: {alarm_name} has been triggered. Event detected in monitoring.",
                pending_duration="PT1M",  # 1 minute
                resolution="1m",
                evaluation_slack_duration="PT3M"  # 3 minutes
            )
            
            response = monitoring_client.create_alarm(
                create_alarm_details=create_alarm_details
            )
            
            if response.data:
                alarm_id = response.data.id
                logger.info(f"Successfully created alarm: {alarm_name} with ID: {alarm_id}")
                return alarm_id
            else:
                logger.error("Failed to create alarm")
                return None
                
        except Exception as e:
            logger.error(f"Error creating alarm: {e}")
            return None


def main():
    """
    Example usage of the OCI Event Publisher
    """
    try:
        # Initialize publisher
        # You can set these via environment variables or OCI config
        publisher = OCIEventPublisher(
            config_profile="DEFAULT",
            compartment_id=os.getenv("OCI_COMPARTMENT_ID"),
            region=os.getenv("OCI_REGION")
        )
        
        # Example 1: Send unableToCertify event
        success = publisher.send_unable_to_certify_event(
            application_name="MyApplication",
            error_details={
                "error_code": "CERT_001",
                "message": "Certificate validation failed",
                "timestamp": datetime.now().isoformat()
            },
            severity="CRITICAL",
            additional_dimensions={
                "module": "certificate_validator",
                "version": "1.0.0"
            }
        )
        
        if success:
            print("✓ Successfully sent unableToCertify event")
        else:
            print("✗ Failed to send unableToCertify event")
        
        # Example 2: Send custom event
        custom_success = publisher.send_custom_event(
            event_name="application_startup",
            metric_value=1.0,
            dimensions={
                "applicationName": "MyApplication",
                "eventType": "startup"
            }
        )
        
        if custom_success:
            print("✓ Successfully sent custom event")
        else:
            print("✗ Failed to send custom event")
            
        # Example 3: Create alarm (uncomment and provide topic_id to use)
        # alarm_id = publisher.create_alarm_for_event(
        #     alarm_name="UnableToCertify-Alarm",
        #     metric_name="unable_to_certify_event",
        #     topic_id="ocid1.onstopic.oc1...",  # Replace with your topic OCID
        #     threshold=1.0,
        #     severity="CRITICAL"
        # )
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())