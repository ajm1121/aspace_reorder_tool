#!/usr/bin/env python3
"""
Validation Manager for ArchivesSpace Reorder Tool
Handles validation of parent and child records.
"""

from typing import Dict, Any, List, Tuple, Optional
from aspace_client import ArchivesSpaceClient

def validate_parent_record(client: ArchivesSpaceClient, parent_type: str, parent_id: int) -> Tuple[bool, Dict[str, Any]]:
    """Validate the parent record and return validation result."""
    try:
        validation_result = client.validate_parent_record(parent_type, parent_id)
        
        if validation_result['exists']:
            return True, validation_result
        else:
            return False, validation_result
            
    except Exception as e:
        return False, {'exists': False, 'error': str(e)}

def validate_child_records(client: ArchivesSpaceClient, records: List[Dict[str, Any]], 
                         parent_id: int, resource_id: int, max_samples: int = 10) -> Tuple[bool, Dict[str, Any]]:
    """Validate child records and return validation result."""
    try:
        object_ids = [record['id'] for record in records]
        validation_results = client.validate_child_records(object_ids, parent_id, resource_id, max_samples)
        
        # Consider validation successful if we have valid records and no critical errors
        is_valid = validation_results['valid_records'] > 0 and validation_results['invalid_records'] == 0
        
        return is_valid, validation_results
        
    except Exception as e:
        return False, {'error': str(e)}

def extract_resource_id_from_parent(client: ArchivesSpaceClient, parent_type: str, parent_id: int) -> Optional[int]:
    """Extract resource ID from parent record."""
    if parent_type == "resources":
        return parent_id
    
    try:
        # For archival_objects, get the resource ID from the parent record
        parent_record = client.get_record(parent_type, parent_id)
        resource_ref = parent_record.get('resource', {}).get('ref', '')
        
        if resource_ref:
            # Extract resource ID from ref like "/repositories/2/resources/9290"
            resource_id = int(resource_ref.split('/')[-1])
            return resource_id
        else:
            return None
            
    except Exception as e:
        print(f"⚠️  Warning: Could not extract resource ID: {e}")
        return None

def validate_excel_file_processing(excel_processor, file_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Validate Excel file processing and return records."""
    try:
        records = excel_processor.process_excel_file(file_path)
        
        if not records:
            return False, []
        
        return True, records
        
    except Exception as e:
        return False, []

def validate_user_confirmation(parent_validation: bool, child_validation: bool, 
                             parent_info: Dict[str, Any], records: List[Dict[str, Any]], 
                             child_results: Optional[Dict[str, Any]] = None) -> bool:
    """Validate that user wants to proceed based on validation results."""
    if not parent_validation or not child_validation:
        return False
    
    # Additional validation checks could be added here
    # For example, checking if the number of records is reasonable
    
    return True

def get_validation_summary(parent_validation: bool, child_validation: bool, 
                          parent_info: Dict[str, Any], records: List[Dict[str, Any]], 
                          child_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get a summary of validation results."""
    operation_type = "REORDERING"
    if child_results and child_results.get('reparenting_detected'):
        operation_type = "REPARENTING"
    
    return {
        'operation_type': operation_type,
        'parent_validation': parent_validation,
        'child_validation': child_validation,
        'parent_info': parent_info,
        'total_records': len(records),
        'child_results': child_results,
        'can_proceed': parent_validation and child_validation
    }
