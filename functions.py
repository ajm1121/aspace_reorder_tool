import requests
import json
import config

#Move one object at a time
def movObj(w, x, y, z, sess):
    url = f"{config.aspacebaseurl}repositories/2/{w}/{x}/accept_children?children[]=/repositories/2/archival_objects/{y}&position={z}"
    payload = {}
    headers = {
    'X-ArchivesSpace-Session': sess
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    res_object = json.loads(response.text)
    return res_object

#Move multiple objects at once, y will be a string of the form "children[]=/repositories/2/archival_objects/id1&children[]=/repositories/2/archival_objects/id2..."  Position will set the position of id1 and all subsequent children will come after
def movObjMult(w, x, y, z, sess):
    url = f"{config.aspacebaseurl}repositories/2/{w}/{x}/accept_children?{y}&position={z}"
    payload = {}
    headers = {
    'X-ArchivesSpace-Session': sess
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    res_object = json.loads(response.text)
    return res_object

#Ask for archival object id input
def get_record_info():
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

# Retrieve an ASpace object where x is an ASpace uri
def objRec(x, sess):
    url = config.aspacebaseurl + x
    
    # current session
    s = open('./login_materials/current_sess.txt', 'r')
    curSession = s.read()
    
    payload = {}
    headers = {
    'X-ArchivesSpace-Session': str(curSession)
    }
    response = requests.get(url, headers=headers)  
    res_object = json.loads(response.text)
    return res_object