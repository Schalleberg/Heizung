import socket
import json
import os

import requests
import http.client
import urllib
import argparse
import pathlib

import databases

BATTERY_LOW_THRESHOLD = 11.5
BATTERY_LOW_HYSTERESE = 0.5

SOUND_NR_ALERT = "8"
SOUND_NR_NO_ALERT = "5"

STATUSFILE_DEFAULT_FILENAME = pathlib.Path( __file__).stem + "_ringbuffer.json"

def send_push_notification(title, message, privateKey, soundNr):
    conn = http.client.HTTPSConnection("pushsafer.com:443")
    conn.request("POST", "/api",
      urllib.parse.urlencode({
        "k": privateKey,                # Your Private or Alias Key
        "m": message,                   # Message Text
        "t": title,                     # Title of message
        "i": "1",                      # Icon number 1-98
        "s": soundNr,                     # Sound number 0-28
        "v": "0",                 # Vibration number 0-3
#        "p": "<PICTURE>",                   # Picture Data URL with Base64-encoded string
      }), { "Content-type": "application/x-www-form-urlencoded" })
    response = conn.getresponse()
    
    print(response.status, response.reason)
    data = response.read()
    print(data)



if __name__ == '__main__':
    argParser = argparse.ArgumentParser(description='Battery Monitor')
    
    argParser.add_argument('--privateKey', required=True,
                    help='File with PushSafer private key.')
    
    argParser.add_argument('--statusFilePath', required=True,
                    help='Path for the file where the alarm status will be stored in.')
        
    args = argParser.parse_args()
    
    pushSaferPrivateKey = args.privateKey
    
    try:
        pushSaferPrivateKey = ""
        with open(args.privateKey, 'r') as f:
            pushSaferPrivateKey =  f.read();
    except:
        print("load file with private key failed. file:" + args.privateKey)
        exit(1)
    
    
    if (os.path.isfile(args.statusFilePath)):
        statusFilePath = args.statusFilePath
    else:
        statusFilePath = os.path.join(args.statusFilePath, STATUSFILE_DEFAULT_FILENAME)
    
    
    dictStatusFile = {}
    try:
        dictStatusFile = json.load(open(statusFilePath))
    except:
        pass
    
    # initialize status file
    if not "battery_low_alarm_active" in dictStatusFile.keys():
        dictStatusFile["battery_low_alarm_active"] = False
    
    
    host = "192.168.2.1"
    #host = "172.19.12.50"
    
    port = 80  # socket server port number

    #
    resp = requests.get("http://" + host + "/?measurements")
    print(resp) 
    print(resp.text)
    deserialzedData = json.loads(resp.text)
    print(deserialzedData)
    
    databases.sendToFirebase("battery/batteryVoltage", deserialzedData["voltage"],"Batteriespannung")
    databases.sendToVolkszaehler("localhost", "0f8549e0-6669-11f0-98b0-cf5b56a3e9e5", deserialzedData["voltage"], "Batteriespannung")
    

    if dictStatusFile["battery_low_alarm_active"] == False:
        if deserialzedData["voltage"] < BATTERY_LOW_THRESHOLD:
            print("BATTERY LOW ALARM! U=" + deserialzedData["voltage"])
            dictStatusFile["battery_low_alarm_active"] = True
            try:
                send_push_notification(title="Temperature Monitor",
                                       message="BATTERY LOW ALARM: " + "U=%.1f"%(deserialzedData["voltage"]),
                                       privateKey=pushSaferPrivateKey,
                                       soundNr=SOUND_NR_ALERT)
            except:
                pass
    else:
        if deserialzedData["voltage"] > (BATTERY_LOW_THRESHOLD + BATTERY_LOW_HYSTERESE):
                print("BATTERY LOW ALARM INACTIVE U=%.1f"%(deserialzedData["voltage"]))
                dictStatusFile["battery_low_alarm_active"] = True
                try:
                    send_push_notification(title="Temperature Monitor",
                                           message="BATTERY LOW ALARM INACTIVE U=%.1f"%(deserialzedData["voltage"]),
                                           privateKey=pushSaferPrivateKey,
                                           soundNr=SOUND_NR_NO_ALERT)
                except:
                    pass

    
    json.dump(dictStatusFile, open(statusFilePath, 'w'),default=str,indent=4)
    