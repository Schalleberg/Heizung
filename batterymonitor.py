import socket
import json

import requests


if __name__ == '__main__':
    host = "172.19.12.50"#socket.gethostname()  # as both code is running on same pc
    port = 80  # socket server port number

    #
    resp = requests.get("http://" + host + "/?measurements")
    print(resp) 
    print(resp.text)
    deserialzedData = json.loads(resp.text)
    print(deserialzedData)
    
    