def receiveData(clientSocket):
    data = clientSocket.recv(1024)
    if not data:
        return None
    return data.decode("utf-8")

def sendStringMessage(clientSocket, message):
    clientSocket.sendall(message.encode('utf-8'))

def sendBytesData(clientSocket, data):
    clientSocket.sendall(data)