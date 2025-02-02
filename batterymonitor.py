import socket

if __name__ == '__main__':
    # create an INET, STREAMing socket
    serversocket = socket.socket()
    # bind the socket to a public host, and a well-known port
    serversocket.bind(("", 1234))
    # become a server socket
    serversocket.listen(5)
    
    print ("socket is listening")            
 
    # a forever loop until we interrupt it or 
    # an error occurs 
    while True: 
     
        # Establish connection with client. 
        c, addr = serversocket.accept()     
        print ('Got connection from', addr )
        
        print (c.recv(1024))
        
        
        # send a thank you message to the client. encoding to send byte type. 
        c.send('Thank you for connecting'.encode()) 
        
        # Close the connection with the client 
        c.close()
         
