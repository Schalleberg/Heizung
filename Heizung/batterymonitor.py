import socket
import json

import requests

import databases


if __name__ == '__main__':
    host = "192.168.2.1"
    #host = "172.19.12.50"
    
    port = 80  # socket server port number

    #
    resp = requests.get("http://" + host + "/?measurements")
    print(resp) 
    print(resp.text)
    deserialzedData = json.loads(resp.text)
    print(deserialzedData)
    
    #databases.sendToFirebase("battery/batteryVoltage", deserialzedData["voltage"],"Batteriespannung")
    databases.sendToVolkszaehler("localhost", "0f8549e0-6669-11f0-98b0-cf5b56a3e9e5", deserialzedData["voltage"], "Batteriespannung")
    