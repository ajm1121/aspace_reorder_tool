# ArchivesSpace Reorder Tool

A secure and improved tool to reorder archival objects in ArchivesSpace based on Excel spreadsheet data.

## Features

- **Secure Authentication**: Uses environment variables (.env file) for secure credential management
- **Excel Support**: Directly reads from `input.xlsx` files
- **Flexible Column Detection**: Automatically finds ID columns with various naming patterns
- **ArchivesSpace Format Support**: Automatically removes second row (data validation row)
- **Safety Validation**: Validates parent and child records before reordering to prevent detached objects
- **Automatic Authentication**: No need to run separate authentication scripts
- **Better Error Handling**: Comprehensive logging and error reporting
- **Flexible Reordering**: Support for both individual and bulk object moves
- **Input Validation**: Validates Excel data before processing
- **File Preview**: Shows spreadsheet structure before processing

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and update it with your ArchivesSpace credentials:

```bash
cp env.example .env
```

Edit the `.env` file with your ArchivesSpace configuration:

```env
AS_USERNAME=your_username
AS_PASSWORD=your_password
AS_BASE_URL=https://your-aspace-instance.com
AS_REPOSITORY_ID=2
LOG_LEVEL=INFO
```

### 3. Prepare Your Excel File

1. Export your ArchivesSpace container list to Excel
2. Reorder the objects in the spreadsheet to match your desired order
3. Save the file as `input.xlsx` in the `input/` directory
4. **Important**: Ensure the file has a column containing archival object IDs

#### Supported ID Column Names

The tool automatically detects ID columns with these common names:
- `Id`, `ID`, `id`
- `Object ID`, `ObjectID`
- `Archival Object ID`, `ArchivalObjectID`
- `Record ID`, `RecordID`
- `Identifier`
- `ASpace ID`, `ASpaceID`, `Aspace ID`, `AspaceID`

The tool will also try partial matches and numeric content detection if exact matches aren't found.

#### ArchivesSpace Spreadsheet Format

The tool automatically handles the standard ArchivesSpace spreadsheet format:
- **Second Row Removal**: Automatically removes the second row which contains data validation information
- **Flexible Structure**: Works with any number of additional columns
- **Row Order**: The order of data rows (after removing the second row) determines the final order in ArchivesSpace

### 4. Run the Tool

```bash
python reorder_tool.py
```

The tool will:
- Automatically authenticate with ArchivesSpace
- Preview your Excel file structure (including cleaning information)
- Load and validate your Excel file
- Prompt for parent record information
- **Validate parent and child records for safety**
- Execute the reordering operation

## Safety Features

### 🛡️ **Record Validation**

The tool includes comprehensive safety checks to prevent objects from becoming detached:

1. **Parent Record Validation**: Verifies that the parent record exists and is accessible
2. **Child Record Sampling**: Checks up to 10 sample objects from your spreadsheet to ensure they exist
3. **Title Confirmation**: Shows record titles to help you confirm you're working with the correct records
4. **User Confirmation**: Requires explicit confirmation before proceeding with reordering

### 🔍 **Validation Process**

```
🔍 Validating parent record...
   Type: resources
   ID: 12345
   ✓ Parent record found!
   Title: John Smith Papers, 1900-1950

🔍 Validating sample child records...
   Checking first 10 records:
   ✓ ID 67890: Correspondence, 1900-1905
   ✓ ID 67891: Photographs, 1900-1950
   ✓ ID 67892: Diaries, 1900-1945
   ...

   Validation Summary:
   ✓ Valid records: 10
   ❌ Invalid records: 0
```

### ⚠️ **Safety Warnings**

The tool will warn you if:
- Parent record doesn't exist
- Child records don't exist
- Records are not accessible
- There are validation errors

## File Structure

```
aspace_reorder_tool/
├── reorder_tool.py          # Main reorder tool
├── aspace_client.py         # ArchivesSpace API client
├── excel_processor.py       # Excel file processing
├── requirements.txt         # Python dependencies
├── env.example             # Environment configuration example
├── input/                  # Input files directory
│   └── input.xlsx          # Your input Excel file
├── 01_reorder_tool/        # Legacy tools
└── README.md
```

## Excel File Requirements

### Required
- **ID Column**: Must contain a column with archival object IDs (numeric values)
- **Data**: At least one row with valid archival object IDs

### Optional
- **Additional Columns**: The tool ignores extra columns and only uses the ID column
- **Column Names**: Flexible naming - the tool will try to find the right column automatically
- **Row Order**: The order of rows in the Excel file determines the final order in ArchivesSpace
- **Second Row**: The tool automatically removes the second row (data validation row)

### Example Excel Structure

| Id | Title | Date | Notes | Other Columns... |
|----|-------|------|-------|------------------|
| 123 | Document 1 | 2023 | Some notes | ... |
| id | title | date | notes | ... | ← **This row is automatically removed**
| 456 | Document 2 | 2023 | More notes | ... |
| 789 | Document 3 | 2023 | Final notes | ... |

The tool will:
1. Find the "Id" column automatically
2. Remove the second row (data validation row)
3. Extract IDs: 123, 456, 789
4. Validate all records exist in ArchivesSpace
5. Reorder them in ArchivesSpace based on their Excel row position

## Important Notes

⚠️ **WARNING**: This tool is for reordering objects within the same collection/resource. Do NOT use it to move objects between different collections.

### Limitations

- Only works for single-level hierarchy reordering
- Cannot move objects between different resources/collections
- Bulk operations may have API limits (tested up to 300 records)

### Before Running

1. **Backup your data**: Always backup your ArchivesSpace data before running reorder operations
2. **Test on small datasets**: Test with a small number of records first
3. **Verify parent record**: Ensure you're targeting the correct parent record type and ID
4. **Check Excel format**: Ensure your Excel file has a column with archival object IDs
5. **Review validation results**: Carefully review the safety validation output before proceeding

## Reorder Methods

The tool offers two reordering methods:

1. **Individual Moves**: One API call per object (recommended for small datasets)
2. **Bulk Move**: Single API call for all objects (faster but may have limits)

## Logging

The tool creates detailed logs in `aspace_reorder.log` for troubleshooting and audit purposes.

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check your credentials in the `.env` file
2. **Excel File Not Found**: Ensure `input.xlsx` exists in `input/`
3. **No ID Column Found**: 
   - Check that your Excel file has a column with archival object IDs
   - Try renaming your ID column to one of the supported names
   - Ensure the ID column contains numeric values
4. **Invalid IDs**: Check that your Excel file has valid numeric IDs
5. **Parent Record Not Found**: Verify the parent record ID and type are correct
6. **Child Records Not Found**: Ensure the objects in your spreadsheet exist in ArchivesSpace
7. **API Errors**: Check the log file for detailed error messages

### Getting Help

If you encounter issues:
1. Check the log file (`aspace_reorder.log`)
2. Verify your ArchivesSpace credentials
3. Ensure your Excel file format is correct
4. Test with a small dataset first
5. Use the preview feature to verify the tool can read your Excel file
6. Review the validation results carefully

## Security

⚠️ **Important Security Notes:**

- **Never commit your `.env` file** to version control
- Keep your ArchivesSpace credentials secure and private
- Log files may contain sensitive information - they are excluded from git by default
- Review the `.gitignore` file to ensure all sensitive files are excluded
- The `.env` file should contain your actual credentials and is ignored by git

## Legacy Tools

The original tools are still available in the `00_set_aspace_session/` and `01_reorder_tool/` directories for reference, but the new `reorder_tool.py` is recommended for all new operations.

