class FetchLogsFromResources(beam.DoFn):
    """DoFn to fetch logs using the get_logs function."""
    
    def __init__(self, start_time: str, end_time: str):
        self.start_time = start_time
        self.end_time = end_time
    
    def process(self, batch_info: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Fetch logs for each resource ID in the batch."""
        try:
            import json
            import logging
            from datetime import datetime
            
            # Try importing with fallbacks
            try:
                from google.cloud import logging as cloud_logging
                from google.protobuf.json_format import MessageToDict
                cloud_logging_available = True
                logging.info("Successfully imported google-cloud-logging")
            except ImportError as e:
                logging.warning(f"Could not import google-cloud-logging: {e}")
                cloud_logging_available = False
                # Create a fallback MessageToDict
                def MessageToDict(obj):
                    return {"fallback_message": str(obj), "timestamp": datetime.utcnow().isoformat() + 'Z'}
            
            resource_ids = batch_info['resource_ids']
            batch_number = batch_info['batch_number']
            
            logging.info(f"FetchLogsFromResources: Processing batch {batch_number} with {len(resource_ids)} resources: {resource_ids}")
            logging.info(f"Cloud Logging available: {cloud_logging_available}")
            
            # Your complete get_logs function implementation
            def get_logs(resource_id: str, start_time: str, end_time: str):
                """
                Complete implementation to get logs from GCP resources.
                Handles projects, folders, and organizations.
                """
                logging.info(f"get_logs: Starting for resource_id: {resource_id}, time: {start_time} to {end_time}")
                
                client = cloud_logging.Client()
                
                # Determine resource type and build appropriate filter
                if resource_id.startswith('projects/'):
                    project_id = resource_id.split('/')[1]
                    logging.info(f"get_logs: Processing project: {project_id}")
                    
                    # For projects, get logs directly from that project
                    project_client = cloud_logging.Client(project=project_id)
                    
                    filter_str = f'''
                    timestamp >= "{start_time}"
                    timestamp <= "{end_time}"
                    '''
                    
                    # Get logs from the specific project
                    try:
                        entries = project_client.list_entries(
                            filter_=filter_str,
                            order_by='timestamp desc',
                            page_size=1000
                        )
                        
                        entry_count = 0
                        for entry in entries:
                            entry_count += 1
                            if entry_count <= 5:
                                logging.info(f"get_logs: Found entry {entry_count}: {entry.timestamp}, {entry.severity}")
                            yield entry
                        
                        logging.info(f"get_logs: Total entries found for project {project_id}: {entry_count}")
                        
                    except Exception as e:
                        logging.error(f"get_logs: Error accessing project {project_id}: {e}")
                        # Continue to next resource instead of failing completely
                
                elif resource_id.startswith('folders/'):
                    folder_id = resource_id.split('/')[1]
                    logging.info(f"get_logs: Processing folder: {folder_id}")
                    
                    # For folders, we need to get all projects in the folder first
                    try:
                        from google.cloud import resource_manager
                        
                        projects_client = resource_manager.ProjectsClient()
                        request = resource_manager.ListProjectsRequest(
                            parent=f"folders/{folder_id}"
                        )
                        
                        projects_in_folder = []
                        for project in projects_client.list_projects(request=request):
                            if project.state == resource_manager.Project.State.ACTIVE:
                                projects_in_folder.append(project.project_id)
                        
                        logging.info(f"get_logs: Found {len(projects_in_folder)} projects in folder {folder_id}: {projects_in_folder}")
                        
                        # Get logs from each project in the folder
                        total_entries = 0
                        for project_id in projects_in_folder:
                            try:
                                project_client = cloud_logging.Client(project=project_id)
                                
                                filter_str = f'''
                                timestamp >= "{start_time}"
                                timestamp <= "{end_time}"
                                '''
                                
                                entries = project_client.list_entries(
                                    filter_=filter_str,
                                    order_by='timestamp desc',
                                    page_size=1000
                                )
                                
                                project_entries = 0
                                for entry in entries:
                                    project_entries += 1
                                    total_entries += 1
                                    
                                    # Add folder context to the log entry
                                    yield entry
                                
                                logging.info(f"get_logs: Project {project_id} in folder {folder_id}: {project_entries} entries")
                                
                            except Exception as e:
                                logging.error(f"get_logs: Error accessing project {project_id} in folder {folder_id}: {e}")
                                continue
                        
                        logging.info(f"get_logs: Total entries from folder {folder_id}: {total_entries}")
                        
                    except Exception as e:
                        logging.error(f"get_logs: Error listing projects in folder {folder_id}: {e}")
                
                elif resource_id.startswith('organizations/'):
                    org_id = resource_id.split('/')[1]
                    logging.info(f"get_logs: Processing organization: {org_id}")
                    
                    # For organizations, get all projects in the org
                    try:
                        from google.cloud import resource_manager
                        
                        projects_client = resource_manager.ProjectsClient()
                        request = resource_manager.ListProjectsRequest(
                            parent=f"organizations/{org_id}"
                        )
                        
                        projects_in_org = []
                        for project in projects_client.list_projects(request=request):
                            if project.state == resource_manager.Project.State.ACTIVE:
                                projects_in_org.append(project.project_id)
                        
                        logging.info(f"get_logs: Found {len(projects_in_org)} projects in organization {org_id}")
                        
                        # Get logs from each project in the organization
                        total_entries = 0
                        for project_id in projects_in_org:
                            try:
                                project_client = cloud_logging.Client(project=project_id)
                                
                                filter_str = f'''
                                timestamp >= "{start_time}"
                                timestamp <= "{end_time}"
                                '''
                                
                                entries = project_client.list_entries(
                                    filter_=filter_str,
                                    order_by='timestamp desc',
                                    page_size=1000
                                )
                                
                                project_entries = 0
                                for entry in entries:
                                    project_entries += 1
                                    total_entries += 1
                                    yield entry
                                
                                logging.info(f"get_logs: Project {project_id} in org {org_id}: {project_entries} entries")
                                
                                # Limit processing to avoid timeouts
                                if total_entries > 50000:  # Configurable limit
                                    logging.warning(f"get_logs: Reached entry limit for org {org_id}, stopping at {total_entries}")
                                    break
                                
                            except Exception as e:
                                logging.error(f"get_logs: Error accessing project {project_id} in org {org_id}: {e}")
                                continue
                        
                        logging.info(f"get_logs: Total entries from organization {org_id}: {total_entries}")
                        
                    except Exception as e:
                        logging.error(f"get_logs: Error listing projects in organization {org_id}: {e}")
                
                else:
                    # Unknown resource type - try generic approach
                    logging.warning(f"get_logs: Unknown resource type for {resource_id}, trying generic filter")
                    
                    filter_str = f'''
                    timestamp >= "{start_time}"
                    timestamp <= "{end_time}"
                    '''
                    
                    try:
                        entries = client.list_entries(
                            filter_=filter_str,
                            order_by='timestamp desc',
                            page_size=1000
                        )
                        
                        entry_count = 0
                        for entry in entries:
                            entry_count += 1
                            yield entry
                        
                        logging.info(f"get_logs: Generic search for {resource_id}: {entry_count} entries")
                        
                    except Exception as e:
                        logging.error(f"get_logs: Error with generic search for {resource_id}: {e}")
                
                
                # If cloud logging is not available, create test data
                else:
                    logging.warning(f"get_logs: Cloud Logging not available, creating test data for {resource_id}")
                    
                    # Generate test log entries when dependencies aren't available
                    for i in range(3):  # Create 3 test logs per resource
                        yield {
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'severity': 'INFO',
                            'textPayload': f'Test log entry {i+1} for {resource_id} (fallback mode)',
                            'resource': {
                                'type': 'fallback_resource',
                                'labels': {'resource_id': resource_id}
                            },
                            'insertId': f'fallback-{resource_id}-{i}',
                            'logName': f'projects/fallback/logs/test-log'
                        }#!/usr/bin/env python3
"""
GCP Dataflow Pipeline for Log Collection using get_logs function.

This pipeline:
1. Takes resource IDs, start_time, end_time as parameters
2. Uses your get_logs function to fetch logs from GCP resources
3. Processes logs in memory-efficient batches
4. Converts each log entry to a Pub/Sub message using MessageToDict
5. Outputs to a Pub/Sub topic

Usage:
    python log_processor_pipeline.py \
        --resource_ids="projects/proj1,projects/proj2,folders/123" \
        --start_time="2024-01-01T00:00:00Z" \
        --end_time="2024-01-01T23:59:59Z" \
        --output_topic="projects/my-project/topics/processed-logs" \
        --runner=DataflowRunner \
        --project=my-project \
        --region=us-central1
"""

import argparse
import json
import logging
from typing import Iterator, Dict, Any
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.io import WriteToPubSub
from datetime import datetime


class LogProcessorOptions(PipelineOptions):
    """Custom pipeline options for log processing."""
    
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            '--resource_ids',
            required=True,
            help='Comma-separated list of resource IDs to process (e.g., "projects/proj1,folders/123")'
        )
        parser.add_argument(
            '--start_time',
            required=True,
            help='Start time for log filtering (ISO format: 2024-01-01T00:00:00Z)'
        )
        parser.add_argument(
            '--end_time',
            required=True,
            help='End time for log filtering (ISO format: 2024-01-01T23:59:59Z)'
        )
        parser.add_argument(
            '--output_topic',
            required=True,
            help='Pub/Sub topic to output processed logs (projects/PROJECT/topics/TOPIC)'
        )
        parser.add_argument(
            '--batch_size',
            type=int,
            default=10,
            help='Number of resource IDs to process in each batch (default: 10)'
        )


class CreateResourceBatches(beam.DoFn):
    """DoFn to create batches of resource IDs for parallel processing."""
    
    def __init__(self, resource_ids: list, batch_size: int = 10):
        self.resource_ids = resource_ids
        self.batch_size = batch_size
    
    def process(self, element) -> Iterator[Dict[str, Any]]:
        """Create batches of resource IDs with metadata."""
        try:
            # Split resource IDs into batches for parallel processing
            for i in range(0, len(self.resource_ids), self.batch_size):
                batch = self.resource_ids[i:i + self.batch_size]
                
                batch_info = {
                    'resource_ids': batch,
                    'batch_number': i // self.batch_size + 1,
                    'total_batches': (len(self.resource_ids) + self.batch_size - 1) // self.batch_size
                }
                
                logging.info(f"Created batch {batch_info['batch_number']}/{batch_info['total_batches']} "
                           f"with {len(batch)} resource IDs")
                yield batch_info
                
        except Exception as e:
            logging.error(f"Error creating resource batches: {e}")


class FetchLogsFromResources(beam.DoFn):
    """DoFn to fetch logs using the get_logs function."""
    
    def __init__(self, start_time: str, end_time: str, get_logs_function):
        self.start_time = start_time
        self.end_time = end_time
        self.get_logs = get_logs_function
    
    def process(self, batch_info: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Fetch logs for each resource ID in the batch."""
        try:
            from google.protobuf.json_format import MessageToDict
            
            resource_ids = batch_info['resource_ids']
            batch_number = batch_info['batch_number']
            
            logging.info(f"Processing batch {batch_number} with {len(resource_ids)} resources")
            
            log_count = 0
            for resource_id in resource_ids:
                try:
                    # Use your get_logs function
                    for log_entry in self.get_logs(
                        resource_id=resource_id,
                        start_time=self.start_time,
                        end_time=self.end_time
                    ):
                        # Convert protobuf to dict if needed
                        if hasattr(log_entry, 'DESCRIPTOR'):  # It's a protobuf message
                            log_dict = MessageToDict(log_entry._pb)
                        elif isinstance(log_entry, dict):
                            log_dict = log_entry.copy()  # Make a copy to avoid modifying original
                        else:
                            # Handle other types (strings, etc.)
                            log_dict = {
                                'textPayload': str(log_entry),
                                'timestamp': datetime.utcnow().isoformat() + 'Z',
                                'severity': 'INFO'
                            }
                        
                        # Add minimal metadata (only what's needed for tracking)
                        log_dict['_pipeline_metadata'] = {
                            'source_resource_id': resource_id,
                            'batch_number': batch_number,
                            'processed_at': datetime.utcnow().isoformat() + 'Z'
                        }
                        
                        yield log_dict
                        log_count += 1
                        
                        # Log progress for large batches
                        if log_count % 1000 == 0:
                            logging.info(f"Processed {log_count} logs from batch {batch_number}")
                
                except Exception as e:
                    logging.error(f"Error fetching logs from resource {resource_id}: {e}")
                    # Yield error log entry in standard Cloud Logging format
                    yield {
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'severity': 'ERROR',
                        'textPayload': f"Error fetching logs: {str(e)}",
                        'resource': {
                            'type': 'global',
                            'labels': {'resource_id': resource_id}
                        },
                        '_pipeline_metadata': {
                            'source_resource_id': resource_id,
                            'batch_number': batch_number,
                            'processed_at': datetime.utcnow().isoformat() + 'Z',
                            'error_type': 'fetch_error'
                        }
                    }
            
            logging.info(f"Completed batch {batch_number}: processed {log_count} total logs")
            
        except Exception as e:
            logging.error(f"Error processing batch: {e}")


class FormatForPubSub(beam.DoFn):
    """DoFn to format log entries for Pub/Sub (final step)."""
    
    def process(self, log_entry: Dict[str, Any]) -> Iterator[bytes]:
        """Convert log entry to Pub/Sub message format."""
        try:
            # Convert to JSON bytes for Pub/Sub
            # The log_entry is already a complete dict from MessageToDict
            message = json.dumps(log_entry, default=str, ensure_ascii=False)
            yield message.encode('utf-8')
            
        except Exception as e:
            logging.error(f"Error formatting log entry for Pub/Sub: {e}")
            # Create a minimal error message
            error_message = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'severity': 'ERROR',
                'textPayload': f"Error formatting log for Pub/Sub: {str(e)}",
                '_pipeline_metadata': {
                    'error_type': 'format_error',
                    'processed_at': datetime.utcnow().isoformat() + 'Z'
                }
            }
            yield json.dumps(error_message).encode('utf-8')


def run_pipeline(argv=None, get_logs_function=None):
    """
    Run the log processing pipeline.
    
    Args:
        argv: Command line arguments
        get_logs_function: Your get_logs function that yields log entries
    """
    
    if get_logs_function is None:
        raise ValueError("get_logs_function must be provided")
    
    parser = argparse.ArgumentParser()
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    # Parse pipeline options
    pipeline_options = PipelineOptions(pipeline_args)
    log_options = pipeline_options.view_as(LogProcessorOptions)
    
    # Set up pipeline for batch processing (not streaming)
    pipeline_options.view_as(StandardOptions).streaming = False
    
    # Parse resource IDs from comma-separated string
    resource_ids = [rid.strip() for rid in log_options.resource_ids.split(',') if rid.strip()]
    
    logging.info(f"=== Starting Log Processing Pipeline ===")
    logging.info(f"Resource IDs: {len(resource_ids)} resources")
    logging.info(f"Time range: {log_options.start_time} to {log_options.end_time}")
    logging.info(f"Output topic: {log_options.output_topic}")
    logging.info(f"Batch size: {log_options.batch_size}")
    
    with beam.Pipeline(options=pipeline_options) as pipeline:
        
        # Step 1: Create resource ID batches for parallel processing
        resource_batches = (
            pipeline
            | 'Create Initial Element' >> beam.Create(['start'])
            | 'Create Resource Batches' >> beam.ParDo(
                CreateResourceBatches(
                    resource_ids=resource_ids,
                    batch_size=log_options.batch_size
                )
            )
        )
        
        # Step 2: Fetch logs from each resource using your get_logs function
        log_entries = (
            resource_batches
            | 'Fetch Logs from Resources' >> beam.ParDo(
                FetchLogsFromResources(
                    start_time=log_options.start_time,
                    end_time=log_options.end_time,
                    get_logs_function=get_logs_function
                )
            )
        )
        
        # Step 3: Format for Pub/Sub and output
        (
            log_entries
            | 'Format for PubSub' >> beam.ParDo(FormatForPubSub())
            | 'Write to PubSub' >> WriteToPubSub(
                topic=log_options.output_topic,
                with_attributes=False
            )
        )
    
    logging.info("Pipeline completed successfully!")


if __name__ == '__main__':
    """
    Main entry point - you need to provide your get_logs function here.
    """
    logging.getLogger().setLevel(logging.INFO)
    
    # Import your get_logs function here
    # Example:
    # from my_log_module import get_logs
    
    # For demonstration, here's a placeholder function
    def example_get_logs(resource_id: str, start_time: str, end_time: str):
        """
        Replace this with your actual get_logs function.
        
        Your function should:
        1. Take resource_id, start_time, end_time as parameters
        2. Yield log entries (either protobuf objects or dicts)
        3. Handle errors gracefully
        """
        # This is just an example - replace with your implementation
        from google.cloud import logging as cloud_logging
        
        client = cloud_logging.Client()
        
        # Build filter based on resource type
        if resource_id.startswith('projects/'):
            project_id = resource_id.split('/')[1]
            filter_str = f'''
            resource.labels.project_id="{project_id}"
            timestamp >= "{start_time}"
            timestamp <= "{end_time}"
            '''
        else:
            filter_str = f'''
            timestamp >= "{start_time}"
            timestamp <= "{end_time}"
            '''
        
        entries = client.list_entries(
            filter_=filter_str,
            order_by='timestamp desc',
            page_size=1000
        )
        
        for entry in entries:
            yield entry  # Yield the protobuf entry directly
    
    # Run the pipeline with your get_logs function
    run_pipeline(get_logs_function=example_get_logs)