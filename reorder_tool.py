#!/usr/bin/env python3
"""
ArchivesSpace Reorder Tool
A secure tool to reorder archival objects in ArchivesSpace based on Excel spreadsheet data.
"""

import sys
import logging
from pathlib import Path
from aspace_client import ArchivesSpaceClient
from excel_processor import ExcelProcessor
from ui_helpers import (
    preview_excel_file, display_parent_validation_result, display_child_validation_results,
    display_validation_confirmation, display_reorder_method_choice, display_individual_move_progress,
    display_bulk_move_progress, display_bulk_move_results, display_operation_completion,
    display_error_and_exit, display_cancellation
)
from validation_manager import (
    validate_parent_record, validate_child_records, extract_resource_id_from_parent,
    validate_excel_file_processing
)

# UI functions moved to ui_helpers.py

# Validation functions moved to validation_manager.py

def main():
    """Main function to run the reorder tool."""
    print("=" * 60)
    print("ArchivesSpace Reorder Tool")
    print("=" * 60)
    
    try:
        # Initialize the ArchivesSpace client
        print("Initializing ArchivesSpace client...")
        client = ArchivesSpaceClient()
        
        # Authenticate with ArchivesSpace
        print("Authenticating with ArchivesSpace...")
        if not client.authenticate():
            print("ERROR: Authentication failed. Please check your credentials in the .env file.")
            sys.exit(1)
        
        print("✓ Authentication successful!")
        
        # Initialize Excel processor
        excel_processor = ExcelProcessor()
        
        # Get the Excel file path
        try:
            excel_file_path = excel_processor.get_sample_file_path()
            print(f"Using Excel file: {excel_file_path}")
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            print("Please ensure the input_sample.xlsx file exists in the 01_reorder_tool/in/ directory.")
            sys.exit(1)
        
        # Preview the Excel file
        if not preview_excel_file(excel_processor, excel_file_path):
            print("ERROR: Failed to preview Excel file")
            sys.exit(1)
        
        # Ask user if they want to proceed
        proceed = input("\nDo you want to proceed with processing this file? (y/N): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)
        
        # Process the Excel file
        print("\nProcessing Excel file...")
        success, records = validate_excel_file_processing(excel_processor, excel_file_path)
        
        if not success or not records:
            display_error_and_exit("Failed to process Excel file. Please check the file format and ensure it contains valid archival object IDs.")
        
        print(f"✓ Successfully processed {len(records)} records from Excel file")
        
        # Get parent record information
        print("\n" + "=" * 40)
        print("Parent Record Information")
        print("=" * 40)
        parent_type, parent_id = client.get_record_info()
        
        # Validate parent record
        print(f"\n🔍 Validating parent record: {parent_type} {parent_id}")
        parent_validation, parent_info = validate_parent_record(client, parent_type, parent_id)
        display_parent_validation_result(parent_info)
        
        if not parent_validation:
            display_error_and_exit("Parent record validation failed. Cannot proceed.")
        
        # Get resource ID from parent record
        resource_id = extract_resource_id_from_parent(client, parent_type, parent_id)
        if resource_id:
            print(f"📋 Resource ID extracted from parent: {resource_id}")
        else:
            print("⚠️  Warning: Could not extract resource ID from parent record")
        
        # Validate sample child records
        print(f"\n🔍 Validating {min(len(records), 10)} sample child records...")
        child_validation, child_results = validate_child_records(client, records, parent_id, resource_id, max_samples=10)
        display_child_validation_results(child_results, parent_id)
        
        # Confirm validation results
        if not display_validation_confirmation(parent_validation, child_validation, parent_info, records, child_results):
            display_cancellation()
        
        # Choose reorder method
        choice = display_reorder_method_choice()
        
        # Execute the reordering
        print(f"\nExecuting reorder operation...")
        
        if choice == '1':
            # Individual moves
            success_count = 0
            error_count = 0
            
            for record in records:
                try:
                    result = client.move_object(
                        parent_type=parent_type,
                        parent_id=parent_id,
                        object_id=record['id'],
                        position=record['position']
                    )
                    display_individual_move_progress(record, True)
                    success_count += 1
                except Exception as e:
                    display_individual_move_progress(record, False, str(e))
                    error_count += 1
            
            print(f"\nOperation completed!")
            print(f"Successfully moved: {success_count} objects")
            print(f"Errors: {error_count} objects")
            
        else:
            # Bulk move with rate limiting and batching
            display_bulk_move_progress(len(records))
            
            try:
                result = client.move_multiple_objects(
                    parent_type=parent_type,
                    parent_id=parent_id,
                    records=records
                )
                
                display_bulk_move_results(result)
                
            except Exception as e:
                print(f"✗ Bulk move failed: {e}")
                print("You may want to try the individual move method instead.")
        
        display_operation_completion()
        
    except KeyboardInterrupt:
        display_cancellation()
    except Exception as e:
        display_error_and_exit(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
