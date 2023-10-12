import socket
import threading
import json

from message import Message
from utils import *
from network import *

HOST = "127.0.0.1"
PORT = 65460

files = {}
lock = threading.Lock()
chunkRegisterLock = threading.Lock()


def handleRegisterRequest(clientSocket):
    sendStringMessage(clientSocket, Message.REGISTER_REQUEST_ACK.value)
    data = receiveData(clientSocket)
    if data is None:
        return

    jsonData = json.loads(data)

    fileInfoList = jsonData.get("file_info_list")
    totalFiles = jsonData.get("total_files")
    port = jsonData.get("port")
    ip = jsonData.get("ip")

    printReceivedFiles(fileInfoList)

    registeredFiles = registerFiles(files, lock, fileInfoList, port, ip)

    clientSocket.sendall(json.dumps({"files_list": registeredFiles}).encode("utf-8"))

    clientSocket.close()


def handleFileListRequest(clientSocket):
    global files
    filesList = []
    for file in files:
        filesList.append(
            {"filename": file, "size": files[file]["size"], "hash": files[file]["hash"]}
        )

    clientSocket.sendall(
        json.dumps({"files_list": filesList, "file_count": len(filesList)}).encode(
            "utf-8"
        )
    )


def handleFileLocationRequest(clientSocket):
    sendStringMessage(clientSocket, Message.FILE_LOCATION_REQUEST_ACK.value)
    filename = receiveData(clientSocket)
    if filename is None:
        return

    else:
        global files

        if filename in files:
            clientSocket.sendall(
                json.dumps({"endpoints": files[filename]["endpoints"]}).encode("utf-8")
            )
    clientSocket.close()

def handleChunkRegister(clientSocket):
    sendStringMessage(clientSocket, Message.CHUNK_REGISTER_REQUEST_ACK.value)
    data = receiveData(clientSocket)
    chunkRegisterinfo = json.loads(data)

    filename = chunkRegisterinfo.get("filename")
    chunkId = chunkRegisterinfo.get("chunkId")
    ip = chunkRegisterinfo.get("ip")
    port = chunkRegisterinfo.get("port")

    with chunkRegisterLock:
        endpointFound = False
        for endpoint in files[filename]["endpoints"]:
            if endpoint.get("ip") == ip and endpoint.get("port") == port:
                endpoint.get("chunks").append(chunkId)
                endpointFound = True

        if endpointFound == False:
            files[filename]["endpoints"].append(
                {"port": port, "ip": ip, "chunks": [chunkId]}
            )

        print(f"{ip}:{port} registered chunk {chunkId} for {filename}\n")


def handleClient(clientSocket):
    try:
        data = clientSocket.recv(1024)
        messageType = data.decode("utf-8")
        print(messageType + "\n")

        if messageType == Message.REGISTER_REQUEST_INIT.value:
            handleRegisterRequest(clientSocket)
        elif messageType == Message.FILE_LIST_REQUEST.value:
            handleFileListRequest(clientSocket)
        elif messageType == Message.FILE_LOCATION_REQUEST_INIT.value:
            handleFileLocationRequest(clientSocket)
        elif messageType == Message.CHUNK_REGISTER_REQUEST_INIT.value:
            handleChunkRegister(clientSocket)

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
