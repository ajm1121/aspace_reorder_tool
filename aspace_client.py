import os
import requests
import json
import logging
from dotenv import load_dotenv
from typing import Tuple, Dict, Any, Optional, List

class ArchivesSpaceClient:
    """Client for interacting with ArchivesSpace API with secure authentication."""
    
    def __init__(self):
        """Initialize the client and load environment variables."""
        load_dotenv()
        self.base_url = os.getenv('AS_BASE_URL')
        self.username = os.getenv('AS_USERNAME')
        self.password = os.getenv('AS_PASSWORD')
        self.repository_id = os.getenv('AS_REPOSITORY_ID', '2')
        self.session_token = None
        
        # Setup logging
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        verbose_logging = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'
        
        # If verbose logging is disabled, set console logging to WARNING+ only
        # But keep file logging at INFO level for debugging
        if verbose_logging:
            console_level = getattr(logging, log_level)
            log_format = '%(asctime)s - %(levelname)s - %(message)s'
        else:
            console_level = logging.WARNING  # Only show warnings and errors in console
            log_format = '%(levelname)s - %(message)s'
        
        # Setup file handler (always detailed)
        file_handler = logging.FileHandler('aspace_reorder.log')
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Setup console handler (conditional verbosity)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,  # Set root to DEBUG to capture everything
            handlers=[file_handler, console_handler]
        )
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required environment variables are set."""
        required_vars = ['AS_USERNAME', 'AS_PASSWORD', 'AS_BASE_URL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Keep the trailing slash as it's expected by the API
        # The original working code uses the full URL with trailing slash
    
    def authenticate(self) -> bool:
        """Authenticate with ArchivesSpace and store session token."""
        try:
            # Use the same URL format as the original working code
            url = f"{self.base_url}/users/{self.username}/login?password={self.password}"
            payload = ""
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            data = response.json()
            self.session_token = data.get('session')
            
            if not self.session_token:
                raise ValueError("No session token received from ArchivesSpace")
            
            self.logger.info("Successfully authenticated with ArchivesSpace")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
        except (KeyError, ValueError) as e:
            self.logger.error(f"Invalid response from ArchivesSpace: {e}")
            return False
    
    def get_record(self, record_type: str, record_id: int) -> Dict[str, Any]:
        """Retrieve a record from ArchivesSpace by type and ID."""
        if not self.session_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            url = f"{self.base_url}/repositories/{self.repository_id}/{record_type}/{record_id}"
            headers = {'X-ArchivesSpace-Session': self.session_token}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            record = response.json()
            self.logger.info(f"Successfully retrieved {record_type} {record_id}")
            return record
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve {record_type} {record_id}: {e}")
            raise
    
    def get_record_title(self, record_type: str, record_id: int) -> str:
        """Get the title of a record from ArchivesSpace."""
        try:
            record = self.get_record(record_type, record_id)
            
            # Extract title based on record type
            if record_type == "resources":
                title = record.get('title', 'No title found')
                if isinstance(title, list) and len(title) > 0:
                    title = title[0]
            elif record_type == "archival_objects":
                title = record.get('title', 'No title found')
                if isinstance(title, list) and len(title) > 0:
                    title = title[0]
            else:
                title = record.get('title', 'No title found')
            
            return str(title) if title else "No title found"
            
        except Exception as e:
            self.logger.error(f"Failed to get title for {record_type} {record_id}: {e}")
            return f"Error retrieving title: {e}"
    
    def validate_parent_record(self, parent_type: str, parent_id: int) -> Dict[str, Any]:
        """Validate that a parent record exists and return its information."""
        try:
            record = self.get_record(parent_type, parent_id)
            title = self.get_record_title(parent_type, parent_id)
            
            validation_result = {
                'exists': True,
                'type': parent_type,
                'id': parent_id,
                'title': title,
                'record': record
            }
            
            self.logger.info(f"Parent record validation successful: {parent_type} {parent_id} - {title}")
            return validation_result
            
        except Exception as e:
            validation_result = {
                'exists': False,
                'type': parent_type,
                'id': parent_id,
                'title': None,
                'error': str(e)
            }
            
            self.logger.error(f"Parent record validation failed: {parent_type} {parent_id} - {e}")
            return validation_result
    
    def validate_child_records(self, object_ids: List[int], parent_id: int, resource_id: int, max_samples: int = 10) -> Dict[str, Any]:
        """Validate that child records exist and detect reparenting operations."""
        validation_results = {
            'total_checked': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'errors': [],
            'reparenting_detected': False,
            'current_parents': {}
        }
        
        # Limit the number of records to validate
        sample_ids = object_ids[:max_samples]
        
        for obj_id in sample_ids:
            validation_results['total_checked'] += 1
            
            try:
                record = self.get_record("archival_objects", obj_id)
                
                # Check if record exists and has required fields
                if not record or 'ancestors' not in record or 'resource' not in record:
                    validation_results['invalid_records'] += 1
                    validation_results['errors'].append(f"Record {obj_id}: Missing ancestors or resource field")
                    continue
                
                # Check parent relationship (should be in ancestors array)
                parent_found = False
                current_parent = None
                for ancestor in record['ancestors']:
                    # Check if the ancestor reference contains the parent ID
                    # The ancestor could be either a resource or archival_object
                    ancestor_ref = ancestor.get('ref', '')
                    if f"/{parent_id}" in ancestor_ref:
                        parent_found = True
                        break
                    # Track current parent (first non-resource ancestor)
                    if 'archival_objects' in ancestor_ref:
                        current_parent = ancestor_ref.split('/')[-1]
                
                # Check resource relationship
                resource_ref = record.get('resource', {}).get('ref', '')
                expected_resource_ref = f"/repositories/{self.repository_id}/resources/{resource_id}"
                resource_matches = resource_ref == expected_resource_ref
                
                # Detect reparenting
                if not parent_found and current_parent and current_parent != str(parent_id):
                    validation_results['reparenting_detected'] = True
                    validation_results['current_parents'][obj_id] = current_parent
                
                if parent_found and resource_matches:
                    validation_results['valid_records'] += 1
                    self.logger.info(f"Record {obj_id}: Valid parent and resource relationships")
                else:
                    validation_results['invalid_records'] += 1
                    if not parent_found:
                        validation_results['errors'].append(f"Record {obj_id}: Parent {parent_id} not found in ancestors")
                    if not resource_matches:
                        validation_results['errors'].append(f"Record {obj_id}: Resource {resource_id} mismatch (found: {resource_ref})")
                
            except Exception as e:
                validation_results['invalid_records'] += 1
                validation_results['errors'].append(f"Record {obj_id}: {str(e)}")
                self.logger.error(f"Child record validation failed: archival_objects {obj_id} - {e}")
        
        return validation_results
    
    def move_object(self, parent_type: str, parent_id: int, object_id: int, position: int, log_individual: bool = True) -> Dict[str, Any]:
        """Move a single archival object to a new position."""
        if not self.session_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            url = f"{self.base_url}/repositories/{self.repository_id}/{parent_type}/{parent_id}/accept_children"
            params = {
                'children[]': f'/repositories/{self.repository_id}/archival_objects/{object_id}',
                'position': position
            }
            headers = {'X-ArchivesSpace-Session': self.session_token}
            
            response = requests.post(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            if log_individual:
                self.logger.info(f"Successfully moved object {object_id} to position {position}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to move object {object_id}: {e}")
            raise
    
    def move_multiple_objects(self, parent_type: str, parent_id: int, records: list) -> Dict[str, Any]:
        """Move multiple archival objects with rate limiting and batching for scale."""
        if not self.session_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            total_records = len(records)
            self.logger.info(f"Starting bulk move of {total_records} objects with rate limiting")
            
            # Rate limiting settings
            batch_size = 50  # Process in batches of 50
            delay_between_batches = 1.0  # 1 second delay between batches
            delay_between_requests = 0.1  # 100ms delay between individual requests
            
            import time
            results = []
            success_count = 0
            error_count = 0
            
            # Process in batches
            for i in range(0, total_records, batch_size):
                batch = records[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_records + batch_size - 1) // batch_size
                
                self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} objects)")
                
                # Process individual objects in this batch
                batch_success = 0
                batch_errors = 0
                
                for j, record in enumerate(batch):
                    try:
                        result = self.move_object(
                            parent_type=parent_type,
                            parent_id=parent_id,
                            object_id=record['id'],
                            position=record['position'],
                            log_individual=False  # Disable individual logging for bulk operations
                        )
                        results.append(result)
                        success_count += 1
                        batch_success += 1
                        
                        # Small delay between individual requests
                        if delay_between_requests > 0:
                            time.sleep(delay_between_requests)
                            
                    except Exception as e:
                        error_count += 1
                        batch_errors += 1
                        self.logger.error(f"Failed to move object {record['id']}: {e}")
                        results.append({'error': str(e), 'object_id': record['id']})
                
                # Report on batch completion (always visible to user)
                progress = (i + len(batch)) / total_records * 100
                print(f"✅ Batch {batch_num}/{total_batches} complete: {batch_success} successful, {batch_errors} failed (Progress: {progress:.1f}%)")
                self.logger.info(f"Batch {batch_num}/{total_batches} complete: {batch_success} successful, {batch_errors} failed (Progress: {progress:.1f}%)")
                
                # Delay between batches (except for the last batch)
                if i + batch_size < total_records and delay_between_batches > 0:
                    self.logger.info(f"Waiting {delay_between_batches}s before next batch...")
                    time.sleep(delay_between_batches)
            
            self.logger.info(f"Bulk move completed: {success_count} successful, {error_count} failed")
            return {
                'status': 'completed',
                'total_records': total_records,
                'success_count': success_count,
                'error_count': error_count,
                'results': results
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to move multiple objects: {e}")
            raise
    
    def get_record_info(self) -> Tuple[str, int]:
        """Get parent record information from user input."""
        while True:
            record_type = input("Enter the type of parent record to update (archival_objects/resources): ").strip().lower()
            if record_type not in ["archival_objects", "resources"]:
                print("Invalid input. Please enter 'archival_objects' or 'resources'.")
                continue

            while True:
                try:
                    record_id = int(input(f"Enter the ID for the parent {record_type} you want to move or resort into: "))
                    return record_type, record_id
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
