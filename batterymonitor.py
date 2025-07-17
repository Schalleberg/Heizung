import socket
import json

import requests


if __name__ == '__main__':
    host = "172.19.12.50"#socket.gethostname()  # as both code is running on same pc
    port = 80  # socket server port number


    resp = requests.get("http://" + host + "/?measurements")
    print(resp)
    
    print(resp.text)
    
    exit()
    
    request = {}
    request["command"]="getMeasurements"
    
    jsonReq = json.dumps(request)
    
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    strReq = "GET /?measurements HTTP/1.1"
    client_socket.send(strReq.encode())
    
#    client_socket.send(jsonReq.encode())  # send message
    
    
    data = client_socket.recv(1024).decode()  # receive response
    
    print('Received from server: ' + data)  # show in terminal
    
    deserialzedData = json.loads(data)
    print(deserialzedData)
    
    client_socket.close()  # close the connection