import socket
import json
import threading

from utils import *
from network import *
from message import Message

HOST = "127.0.0.1"

filesOnNetwork = []
fileChunks = {}
lock = threading.Lock()


def waitRegisteredFilesMessage(clientSocket):
    data = receiveData(clientSocket)
    if data is None:
        return
    jsonData = json.loads(data)

    print("Following files have been registered with the server:\n")
    filesList = jsonData.get("files_list")
    for file in filesList:
        print(f'File: {file["filename"]} Status: {file["status"]}')


def handleRegisterFilesRequest(clientSocket, ip, port, dir):
    data = receiveData(clientSocket)
    if data is None:
        return

    if data == Message.REGISTER_REQUEST_ACK.value:
        fileInfoList, totalFiles = crawlDirectory(dir)

        fileInfoData = convertToJsonAndEncode(
            {
                "file_info_list": fileInfoList,
                "total_files": totalFiles,
                "port": port,
                "ip": ip,
            }
        )

        sendBytesData(clientSocket, fileInfoData)
        waitRegisteredFilesMessage(clientSocket)


def handleFileListRequest(clientSocket):
    data = clientSocket.recv(1024)
    receivedData = json.loads(data)

    filesList = receivedData.get("files_list")
    fileCount = receivedData.get("file_count")
    print("\nTotal files: ", fileCount)
    for file in filesList:
        print(f'Name: {file["filename"]} Size: {file["size"]}')
    print()

    filesOnNetwork.extend(filesList)


def handleFileLocationRequest(clientSocket, filename):
    data = receiveData(clientSocket)
    if data is None:
        return

    if data == Message.FILE_LOCATION_REQUEST_ACK.value:
        sendStringMessage(clientSocket, filename)

        endpointsData = receiveData(clientSocket)
        if endpointsData is None:
            return

        endpointsDict = json.loads(endpointsData)

        return endpointsDict.get("endpoints")


def shareChunkOnRequest(clientSocket, dirPath):
    initRequest = receiveData(clientSocket)
    if initRequest is None:
        return

    if initRequest == Message.FILE_CHUNK_REQUEST_INIT.value:
        sendStringMessage(clientSocket, Message.FILE_CHUNK_REQUEST_ACK.value)
        data = receiveData(clientSocket)
        if data is None:
            return

        chunkRequest = json.loads(data)

        chunkId = chunkRequest.get("id")
        filename = chunkRequest.get("name")
        
        currentDir = os.getcwd()
        filePath = os.path.join(currentDir, dirPath, filename)

        fileData = readFileInBytes(filePath)

        if fileData is not None:
            requestedChunkData = fileData[chunkId * 1000 : (chunkId + 1) * 1000]
            sendBytesData(clientSocket, requestedChunkData)


def downloadChunk(endpoint, filename, chunkId):
    print(f"Downloading Chunk {chunkId} from {endpoint.get('ip')}:{endpoint.get('port')}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, endpoint.get("port")))
        sendStringMessage(s, Message.FILE_CHUNK_REQUEST_INIT.value)
        data = receiveData(s)
        if data is None:
            return

        if data == Message.FILE_CHUNK_REQUEST_ACK.value:
            chunkRequest = convertToJsonAndEncode({"id": chunkId, "name": filename})
            sendBytesData(s, chunkRequest)

            chunkData = receiveData(s)
            if chunkData is None:
                return
            else:
                with lock:
                    if filename not in fileChunks:
                        fileChunks[filename] = {}

                    fileChunks[filename][chunkId] = chunkData
        
        s.close()


def downloadFile(clientSocket, filename, relativeDir):
    endpoints = handleFileLocationRequest(clientSocket, filename)
    filesize = 0
    fileHash = 0

    for file in filesOnNetwork:
        if filename == file["filename"]:
            filesize = file["size"]
            fileHash = file["hash"]  

    chunksCount = filesize // 1000

    if chunksCount > 0:
        print(f"\nDownloading file: {filename}\n")
        i = 0

        threads = [
            threading.Thread(
                target=downloadChunk, args=(endpoints[i % len(endpoints)], filename, i)
            )
            for i in range(chunksCount + 1)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        print("\nFinished Downloading file\n")
        writeDownloadedFile(fileChunks, filename, relativeDir)

        currentDir = os.getcwd()
        filePath = os.path.join(currentDir, relativeDir, filename)

        hashHex = getHashOfFile(filePath)
        if hashHex == fileHash:
            print("Downloaded file passed integrity check\n")
        else:
            print("Downloaded file did not pass integrity check\n")
            print(f"Deleting file: {filename}\n")
            deleteFile(filePath)



def handlePeerRequest(clientPort, dirPath):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, clientPort))
        s.listen(5)

        while True:
            conn, addr = s.accept()
            requestHandler = threading.Thread(
                target=shareChunkOnRequest, args=(conn, dirPath)
            )
            requestHandler.start()


def clientThread(serverPort, clientPort, dirPath):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, serverPort))
        sendStringMessage(s, Message.REGISTER_REQUEST_INIT.value)
        handleRegisterFilesRequest(s, HOST, clientPort, dirPath)
        s.close()

    while True:
        input, filename = takeUserInput()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, serverPort))

            if input == InputEnum.FILE_LIST.value:
                sendStringMessage(s, Message.FILE_LIST_REQUEST.value)
                handleFileListRequest(s)
            elif input == InputEnum.DOWNLOAD_FILE.value:
                sendStringMessage(s, Message.FILE_LOCATION_REQUEST_INIT.value)
                downloadFile(s, filename, dirPath)
            
            s.close()


def main():
    args = parseArguments()

    clientHandler = threading.Thread(
        target=clientThread, args=(args.sp, args.cp, args.dir)
    )
    peerRequestHandler = threading.Thread(
        target=handlePeerRequest, args=(args.cp, args.dir)
    )

    clientHandler.start()
    peerRequestHandler.start()


if __name__ == "__main__":
    main()
