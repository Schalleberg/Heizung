import socket
import json


if __name__ == '__main__':
    host = "172.19.12.50"#socket.gethostname()  # as both code is running on same pc
    port = 5678  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server


    msg = "voltage"
    client_socket.send(msg.encode())  # send message
    data = client_socket.recv(1024).decode()  # receive response

    print('Received from server: ' + data)  # show in terminal

    deserialzedData = json.loads(data)
    print(deserialzedData)

    client_socket.close()  # close the connection