import socket
import threading
from message import Message
import json

HOST = "127.0.0.1"
PORT = 65456

files = {}
lock = threading.Lock()


def handleRegisterRequest(clientSocket):
    data = clientSocket.recv(1024)

    if not data:
        print("No data received from the client.")
    else:
        dataStr = data.decode("utf-8")
        receivedData = json.loads(dataStr)

        fileInfoList = receivedData.get("file_info_list")
        totalFiles = receivedData.get("total_files")
        port = receivedData.get("port")
        ip = receivedData.get("ip")

        print("Total files received:", totalFiles)
        print("Files received:")
        for fileInfo in fileInfoList:
            print(f"  Filename: {fileInfo['filename']}, Size: {fileInfo['size']} bytes")

        global files
        registeredFiles = []
        with lock:
            for fileInfo in fileInfoList:
                if fileInfo["filename"]:
                    if fileInfo["filename"] not in files:
                        files[fileInfo["filename"]] = {
                            "size": fileInfo["size"],
                            "endpoints": [
                                {
                                    "port": port,
                                    "ip": ip,
                                }
                            ],
                        }
                    else:
                        files[fileInfo["filename"]]["endpoints"].append(
                            {
                                "port": port,
                                "ip": ip,
                            }
                        )
                registeredFiles.append(
                    {"filename": fileInfo["filename"], "status": "Registered"}
                )

        clientSocket.sendall(
            json.dumps({"files_list": registeredFiles}).encode("utf-8")
        )


def handleFileListRequest(clientSocket):
    global files
    filesList = []
    for file in files:
        filesList.append({"filename": file, "size": files[file]["size"]})

    clientSocket.sendall(
        json.dumps({"files_list": filesList, "file_count": len(filesList)}).encode(
            "utf-8"
        )
    )

def handleFileLocationRequest(clientSocket):
    data = clientSocket.recv(1024)

    if not data:
        print("No data received from the client.")
    else:
        filename = data.decode("utf-8")
        global files
        
        if filename in files:
            print(files[filename]["endpoints"])
            clientSocket.sendall(json.dumps({ "endpoints" : files[filename]["endpoints"]}).encode("utf-8"))

def handleClient(clientSocket):
    try:
        # Receive and send data to the client
        data = clientSocket.recv(1024)
        messageType = data.decode("utf-8")
        print(messageType)

        if messageType == Message.REGISTER_REQUEST.value:
            handleRegisterRequest(clientSocket)
        elif messageType == Message.FILE_LIST_REQUEST.value:
            handleFileListRequest(clientSocket)
        elif messageType == Message.FILE_LOCATION_REQUEST.value:
            clientSocket.sendall(b"Send file name")
            handleFileLocationRequest(clientSocket)
        elif messageType == Message.CHUNK_REGISTER_REQUEST.value:
            print("Handling a Chunk Register Request.")
        elif messageType == Message.FILE_CHUNK_REQUEST.value:
            print("Handling a File Chunk Request.")

        # while data:
        #     client_socket.send(b"Received: " + data)
        #     data = client_socket.recv(1024)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        clientSocket.close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        clientHandler = threading.Thread(target=handleClient, args=(conn,))
        clientHandler.start()
