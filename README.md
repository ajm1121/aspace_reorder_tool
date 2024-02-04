# aspace_reorder_tool
A tool to reorder container lists in ArchivesSpace

# 00_set_aspace_session
Use this first to establish a session with ASpace.  Requires valid credentials and API base url saved in a file called config.py (example provided).  Sets the current session in a current_see.txt file.

# 01_reorder_tool
Takes as input a slightly edited csv version of the ArchivesSpace Bulk Reorder spreadsheet.  Before running the tool, the user should 

1) Update the order of the objects on the spreadsheet to match the desired order of the objects in the container list nested under the target parent object
2) Delete the second row of the update tab(with 'id' in cell A2) and the 'enums' tab from the spreadsheet
3) Save the edited spreadsheet into the in folder in the 01_reorder_tool folder of the tool with the filename 'input.csv' 

This tool will not sort multiple levels of hierarchy at one time, just a single flat resource or series.  Nested subseries will probably be moved, but I haven't tested this yet.  

The user must input the type of parent record (archival object or resource) they are reordering into and the id of the parent record.  This is because there are separate API endpoints for parent resources and archival objects.  

There are two versions of the tool:
1) reorder.py: This tool will submit one API call each row in input.csv, setting the position in the container list based on the index of the row.    
2) reorder_multiple.py: This tool with submit a single API call for the entire csv.  All of the ids in the Id column are concatenated into a single string which is passed as a parameter.  [WARNING: I am not clear on the limits around such a call.]  This version of the tool only inserts the csv into the position directly under the parent object (position 0).  This could be changed by editing the position variable in the function that calls the api from 0 to something else (movObj(parent_id[0], parent_id[1], objectString, [CHANGE THIS], c)).  CURRENT LARGEST NUMBER OF RECORDS UPDATED WITH THIS TOOL: 169

Things to note:  
1) If any rows from the spreadsheet are removed, it appearts they will sort to the bootom of the container list in the order that they currently appear.
2) As far as I can tell, archival objects from any collection can be moved into the container list of any other collection.  This could cause significant confusion if an object id is misentered.