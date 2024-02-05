import requests
import json
import os
import sys
import csv
from io import StringIO
import logging

# Setup logging to write to a file
logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

#gets the config and function files from the parent directory 
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from config import aspacebaseurl
from functions import get_record_info
from functions import movObj

#get the current session token
s = open('current_sess.txt', 'r')
c = s.read()

parent_id = get_record_info()

print (f"{parent_id} is being updated.")

#Open the input csv
with open('01_reorder_tool/in/input.csv', 'r', encoding='utf8') as input_file:
    csv_reader = csv.DictReader(input_file, delimiter=',')
    for row_number, row in enumerate(csv_reader, start=0):
        print(f"Archival object {row['Id']} moving to position {row_number} under {parent_id[0]} {parent_id[1]}")

        try:
            moved_obj = movObj(parent_id[0], parent_id[1], row['Id'], row_number, c)
            print(moved_obj["status"])
        
        #Handles errors and logs them to the errors.log file
        except Exception as e:
            error_message = f"Error processing row {row_number}: {e}"
            print(error_message)
            logging.error(error_message)
            continue



