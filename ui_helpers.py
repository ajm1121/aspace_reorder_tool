#!/usr/bin/env python3
"""
UI Helpers for ArchivesSpace Reorder Tool
Display and user interaction functions.
"""

import os
import sys
from typing import Dict, Any, List, Optional

def preview_excel_file(excel_processor, file_path: str) -> bool:
    """Preview the Excel file structure."""
    print("\n" + "=" * 50)
    print("Excel File Preview")
    print("=" * 50)
    
    try:
        preview = excel_processor.preview_excel_file(file_path)
        
        if 'error' in preview:
            print(f"Error previewing file: {preview['error']}")
            return False
        
        # Condensed summary in 5-10 lines
        print(f"📄 File: {os.path.basename(file_path)}")
        print(f"📊 Structure: {preview['total_rows']} rows, {preview['total_columns']} columns")
        
        # Cleaning summary
        if 'cleaning_info' in preview and preview['cleaning_info']:
            cleaning = preview['cleaning_info']
            print(f"🧹 Cleaning: {cleaning['rows_removed']} rows removed → {cleaning['rows_after_cleaning']} data rows")
        
        # Essential columns
        if 'essential_columns' in preview and preview['essential_columns']:
            cols = ", ".join(preview['essential_columns'])
            print(f"✅ Essential columns: {cols}")
        
        # ID column and sample
        if preview['id_column_found']:
            sample_ids = preview['sample_ids'][:3]  # Show only first 3 IDs
            print(f"🆔 ID column: '{preview['id_column_found']}' (samples: {sample_ids})")
        
        # Show first data row as sample
        if 'first_few_rows' in preview and preview['first_few_rows']:
            first_row = preview['first_few_rows'][0]
            if 'Id' in first_row and 'Title' in first_row:
                print(f"📋 Sample: ID {first_row['Id']}, Title: {first_row['Title'][:30]}...")
        
        return True
        
    except Exception as e:
        print(f"Error during preview: {e}")
        return False

def display_parent_validation_result(validation_result: Dict[str, Any]) -> None:
    """Display parent record validation results."""
    if validation_result['exists']:
        print(f"✅ Parent record validation successful!")
        print(f"   Title: {validation_result['title']}")
    else:
        print(f"❌ Parent record validation failed!")
        print(f"   Error: {validation_result['error']}")

def display_child_validation_results(validation_results: Dict[str, Any], parent_id: int) -> None:
    """Display child record validation results."""
    print(f"✅ Child record validation complete!")
    print(f"   Records checked: {validation_results['total_checked']}")
    print(f"   Valid relationships: {validation_results['valid_records']}")
    print(f"   Invalid relationships: {validation_results['invalid_records']}")
    
    # Check for reparenting operations
    if validation_results['reparenting_detected']:
        print(f"\n🔄 REPARENTING OPERATION DETECTED!")
        print(f"   Some objects will be moved to a different parent record.")
        print(f"   Current parent → New parent:")
        
        for obj_id, current_parent in validation_results['current_parents'].items():
            print(f"   • Object {obj_id}: {current_parent} → {parent_id}")

def display_validation_confirmation(parent_validation: bool, child_validation: bool, 
                                  parent_info: Dict[str, Any], records: List[Dict[str, Any]], 
                                  child_results: Optional[Dict[str, Any]] = None) -> bool:
    """Display validation results and ask for user confirmation."""
    print("\n" + "=" * 50)
    print("Validation Summary")
    print("=" * 50)
    
    # Determine operation type
    operation_type = "REORDERING"
    if child_results and child_results.get('reparenting_detected'):
        operation_type = "REPARENTING"
    
    print(f"Operation Type: {operation_type}")
    print(f"Parent Record: {parent_info['title']}")
    print(f"Total Objects: {len(records)}")
    
    # Validation status
    print(f"\nValidation Results:")
    print(f"   Parent Record: {'✅ Valid' if parent_validation else '❌ Invalid'}")
    print(f"   Child Records: {'✅ Valid' if child_validation else '❌ Invalid'}")
    
    if not parent_validation or not child_validation:
        print("\n❌ Validation failed. Cannot proceed with the operation.")
        return False
    
    # Confirmation prompt
    if operation_type == "REPARENTING":
        print(f"\n⚠️  This operation will move objects to a different parent record.")
        proceed = input("Do you want to proceed with the reparenting? (y/N): ").strip().lower()
    else:
        print(f"\n✅ All validations passed. Ready to proceed with reordering.")
        proceed = input("Do you want to proceed with the reordering? (y/N): ").strip().lower()
    
    return proceed in ['y', 'yes']

def display_reorder_method_choice() -> str:
    """Display reorder method options and get user choice."""
    print("\nChoose reorder method:")
    print("1. Individual moves (one API call per object) - Recommended for small datasets")
    print("2. Bulk move (single API call for all objects) - Faster but may have limits")
    
    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Please enter 1 or 2.")

def display_individual_move_progress(record: Dict[str, Any], success: bool, error: str = None) -> None:
    """Display progress for individual move operations."""
    if success:
        print(f"✓ Moved object {record['id']} to position {record['position']}")
    else:
        print(f"✗ Failed to move object {record['id']}: {error}")

def display_bulk_move_progress(total_records: int) -> None:
    """Display bulk move progress information."""
    print(f"\n🔄 Starting bulk move of {total_records} objects...")
    print("   • Processing in batches of 50 objects")
    print("   • Rate limiting: 100ms between requests, 1s between batches")
    print("   • Progress updates every 10 objects")

def display_bulk_move_results(result: Dict[str, Any]) -> None:
    """Display bulk move completion results."""
    print(f"\n✅ Bulk move completed!")
    print(f"   • Total objects: {result['total_records']}")
    print(f"   • Successful: {result['success_count']}")
    print(f"   • Failed: {result['error_count']}")
    
    if result['error_count'] > 0:
        print(f"   ⚠️  {result['error_count']} objects failed to move")
        print("   Check the log file for details on failed objects")

def display_operation_completion() -> None:
    """Display operation completion message."""
    print("\nReorder operation completed!")
    print("Check the log file 'aspace_reorder.log' for detailed information.")

def display_error_and_exit(message: str, exit_code: int = 1) -> None:
    """Display error message and exit."""
    print(f"\nERROR: {message}")
    sys.exit(exit_code)

def display_cancellation() -> None:
    """Display operation cancellation message."""
    print("\nOperation cancelled by user.")
    sys.exit(0)
