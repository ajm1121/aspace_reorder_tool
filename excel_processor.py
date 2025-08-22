import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

class ExcelProcessor:
    """Process Excel files for ArchivesSpace reordering."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Common variations of ID column names
        self.id_column_variations = [
            'Id', 'ID', 'id', 'Object ID', 'ObjectID', 'Archival Object ID',
            'ArchivalObjectID', 'Record ID', 'RecordID', 'Identifier',
            'ASpace ID', 'ASpaceID', 'Aspace ID', 'AspaceID'
        ]
    
    def load_excel_file(self, file_path: str) -> pd.DataFrame:
        """Load and validate the Excel file."""
        try:
            # Suppress the openpyxl warning about data validation
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Data Validation extension is not supported")
                # Try to read the Excel file
                df = pd.read_excel(file_path)
            
            self.logger.info(f"Successfully loaded Excel file: {file_path}")
            self.logger.info(f"Found {len(df.columns)} columns, {len(df)} rows")
            return df
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")
    
    def clean_archivesspace_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the DataFrame to handle ArchivesSpace spreadsheet format."""
        original_count = len(df)
        df_cleaned = df.copy()
        
        # Remove the header row (index 0)
        if len(df_cleaned) > 0:
            df_cleaned = df_cleaned.drop(df_cleaned.index[0])
            self.logger.info(f"Removed header row - {original_count} -> {len(df_cleaned)} rows")
        
        # Check if there's a data validation row (second row in original file)
        # This row typically has non-ID values or validation text
        if len(df_cleaned) > 0:
            first_data_row = df_cleaned.iloc[0]
            id_column = self.find_id_column(df)
            
            if id_column and id_column in first_data_row:
                try:
                    # Try to convert the first row's ID to int - if it fails, it might be a validation row
                    int(first_data_row[id_column])
                    self.logger.info("First data row has valid ID - no validation row to remove")
                except (ValueError, TypeError):
                    # This might be a validation row, remove it
                    df_cleaned = df_cleaned.drop(df_cleaned.index[0])
                    self.logger.info(f"Removed data validation row - {len(df_cleaned) + 1} -> {len(df_cleaned)} rows")
        
        # Reset index to ensure proper row numbering starting from 0
        df_cleaned = df_cleaned.reset_index(drop=True)
        
        # Remove any completely empty rows
        df_cleaned = df_cleaned.dropna(how='all')
        
        self.logger.info(f"Final count after cleaning: {len(df_cleaned)} rows")
        
        return df_cleaned
    
    def find_id_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the ID column using various common naming patterns."""
        # First, try exact matches
        for col_name in self.id_column_variations:
            if col_name in df.columns:
                self.logger.info(f"Found ID column: '{col_name}'")
                return col_name
        
        # If no exact match, try partial matches
        for col in df.columns:
            col_lower = col.lower()
            if any(variation.lower() in col_lower for variation in ['id', 'identifier', 'object']):
                self.logger.info(f"Found potential ID column by partial match: '{col}'")
                return col
        
        # If still no match, look for columns that might contain numeric IDs
        for col in df.columns:
            try:
                # Try to convert to numeric to see if it contains IDs
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if not numeric_col.isnull().all() and numeric_col.dtype in ['int64', 'float64']:
                    self.logger.info(f"Found potential ID column by numeric content: '{col}'")
                    return col
            except:
                continue
        
        return None
    
    def validate_dataframe(self, df: pd.DataFrame) -> tuple[bool, str]:
        """Validate that the DataFrame has a valid ID column."""
        # Find the ID column
        id_column = self.find_id_column(df)
        
        if not id_column:
            available_columns = list(df.columns)
            raise ValueError(
                f"Could not find ID column. Available columns: {available_columns}\n"
                f"Please ensure your spreadsheet has a column containing archival object IDs.\n"
                f"Common column names: {', '.join(self.id_column_variations[:5])}"
            )
        
        # Check if ID column contains valid data
        if df[id_column].isnull().all():
            raise ValueError(f"ID column '{id_column}' contains no valid data")
        
        # Convert ID column to numeric, removing any non-numeric values
        try:
            df[id_column] = pd.to_numeric(df[id_column], errors='coerce')
            # Remove rows with NaN values in ID column
            df_clean = df.dropna(subset=[id_column])
            if df_clean.empty:
                raise ValueError(f"No valid IDs found in column '{id_column}'")
            
            # Update the dataframe with cleaned data
            df = df_clean.copy()
            
        except Exception as e:
            raise ValueError(f"Error processing ID column '{id_column}': {e}")
        
        self.logger.info(f"DataFrame validation successful. Found {len(df)} valid records using column '{id_column}'.")
        return True, id_column
    
    def prepare_reorder_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Prepare the data for reordering."""
        try:
            # Validate the DataFrame and get the ID column name
            is_valid, id_column = self.validate_dataframe(df)
            
            if not is_valid:
                raise ValueError("DataFrame validation failed")
            
            # Convert DataFrame to list of dictionaries
            records = []
            position_counter = 1  # Start positions at 1
            
            for index, row in df.iterrows():
                try:
                    # Ensure the ID is a valid integer
                    obj_id = int(row[id_column])
                    record = {
                        'id': obj_id,
                        'position': position_counter,  # Sequential position starting from 1
                        'row_number': position_counter,  # Human-readable row number
                        'original_row': index  # Keep track of original DataFrame row position
                    }
                    records.append(record)
                    position_counter += 1  # Increment for next valid record
                except (ValueError, TypeError) as e:
                    # Skip rows with invalid IDs but don't increment position counter
                    self.logger.warning(f"Skipping DataFrame row {index} with invalid ID '{row[id_column]}': {e}")
                    continue
            
            if not records:
                raise ValueError("No valid records found after processing")
            
            self.logger.info(f"Prepared {len(records)} records for reordering")
            return records
            
        except Exception as e:
            self.logger.error(f"Error preparing reorder data: {e}")
            raise
    
    def process_excel_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Complete processing of Excel file for reordering."""
        try:
            # Load the Excel file
            df = self.load_excel_file(file_path)
            
            # Clean the DataFrame (remove second row, empty rows, etc.)
            df_cleaned = self.clean_archivesspace_dataframe(df)
            
            # Prepare the data for reordering
            records = self.prepare_reorder_data(df_cleaned)
            
            return records
            
        except Exception as e:
            self.logger.error(f"Error processing Excel file: {e}")
            raise
    
    def get_sample_file_path(self) -> str:
        """Get the path to the input Excel file."""
        sample_path = Path("input/input.xlsx")
        
        if not sample_path.exists():
            raise FileNotFoundError(f"Input file not found at: {sample_path}")
        
        return str(sample_path)
    
    def preview_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Preview the Excel file structure without processing."""
        try:
            df = self.load_excel_file(file_path)
            
            # Show simplified structure with only essential columns
            essential_columns = ['Id', 'Title', 'Level of Description']
            available_essential = [col for col in essential_columns if col in df.columns]
            
            # Create simplified preview with only essential columns
            df_simplified = df[available_essential] if available_essential else df.iloc[:, :3]  # First 3 columns if no essential found
            
            preview = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'essential_columns': available_essential,
                'first_few_rows': df_simplified.head(3).to_dict('records'),
                'id_column_found': None,
                'cleaning_info': {}
            }
            
            # Try to find ID column
            id_column = self.find_id_column(df)
            if id_column:
                preview['id_column_found'] = id_column
                preview['sample_ids'] = df[id_column].head(5).tolist()
            
            # Show what cleaning would do
            df_cleaned = self.clean_archivesspace_dataframe(df)
            preview['cleaning_info'] = {
                'rows_after_cleaning': len(df_cleaned),
                'rows_removed': len(df) - len(df_cleaned),
                'second_row_removed': len(df) > 1
            }
            
            return preview
            
        except Exception as e:
            return {'error': str(e)}
