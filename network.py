# The function is used to receive data from the socket and decode the bytes
def receiveData(clientSocket):
    data = clientSocket.recv(1024)
    if not data:
        return None
    return data.decode("utf-8")

# The function sends a string message into the socket
def sendStringMessage(clientSocket, message):
    clientSocket.sendall(message.encode('utf-8'))

# The function sends bytes data into the socket
def sendBytesData(clientSocket, data):
    clientSocket.sendall(data)