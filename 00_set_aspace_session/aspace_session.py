import requests
import json
import os
import sys

#gets the config file from the parent directory 
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import config

#sets the url for authentication
url = config.aspacebaseurl + "/users/" + config.username + "/login?password=" + config.password

payload = ""
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

#print(response.text)
y = json.loads(response.text)

print(y["session"])

#records the session token for use in other tools
with open ('current_sess.txt', 'w') as c:
  c.write(y["session"])
  c.close()