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

# The function is used to wait for the server's acknowledgment of registered files 
# and prints the registered files 
def waitRegisteredFilesMessage(clientSocket):
    data = receiveData(clientSocket)
    if data is None:
        return
    jsonData = json.loads(data)

    print("Following files have been registered with the server:\n")
    filesList = jsonData.get("files_list")
    for file in filesList:
        print(f'File: {file["filename"]} Status: {file["status"]}')

# Function is used to register files with server
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

# Function is used to get the list of files on the network from the server
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

# Function is used to get information regarding the location of file 
# The servers sends information regarding endpoints and chunks
def handleFileLocationRequest(clientSocket, filename):
    data = receiveData(clientSocket)
    if data is None:
        return

    if data == Message.FILE_LOCATION_REQUEST_ACK.value:
        sendStringMessage(clientSocket, filename)

        fileLocationInfo = ""
        while True:
            endpointsData = receiveData(clientSocket)
            
            if endpointsData is None:
                break
            else:
                fileLocationInfo += endpointsData

        endpointsDict = json.loads(fileLocationInfo)

        return endpointsDict.get("endpoints")

# The function is used to send a chunk to a peer upon request
def shareChunkOnRequest(clientSocket, dirPath):
    initRequest = receiveData(clientSocket)
    if initRequest is None:
        return

    if initRequest == Message.FILE_CHUNK_REQUEST_INIT.value:
        sendStringMessage(clientSocket, Message.FILE_CHUNK_REQUEST_ACK.value)
        while True:
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

# The function is used to register a downloaded chunk with the server
def handleRegisterChunkRequest(filename, chunkId, ip, port, serverPort):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, serverPort))
        sendStringMessage(s, Message.CHUNK_REGISTER_REQUEST_INIT.value)

        data = receiveData(s)
        if data is None:
            return

        if data == Message.CHUNK_REGISTER_REQUEST_ACK.value:
            chunkRequest = convertToJsonAndEncode(
                {"filename": filename, "chunkId": chunkId, "ip": ip, "port": port}
            )
            sendBytesData(s, chunkRequest)

        s.close()

# The function handles downloading chunks from given peer 
# After downloading the chunk. A connection is opened with the server
# to get the downloaded chunk registered with the server
def downloadChunks(endpoint, filename, serverPort, clientPort):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, endpoint.get("port")))
        sendStringMessage(s, Message.FILE_CHUNK_REQUEST_INIT.value)
        data = receiveData(s)
        if data is None:
            return

        if data == Message.FILE_CHUNK_REQUEST_ACK.value:
            for chunkId in endpoint["chunks"]:
                print(
                    f"Downloading Chunk {chunkId} from {endpoint.get('ip')}:{endpoint.get('port')}"
                )
                chunkRequest = convertToJsonAndEncode({"id": chunkId, "name": filename})
                sendBytesData(s, chunkRequest)

                chunkData = receiveData(s)
                if chunkData is None:
                    s.close()
                    return
                else:
                    with lock:
                        if filename not in fileChunks:
                            fileChunks[filename] = {}

                        fileChunks[filename][chunkId] = chunkData

                chunkRegisterThread = threading.Thread(
                    target=handleRegisterChunkRequest,
                    args=(filename, chunkId, HOST, clientPort, serverPort),
                )
                chunkRegisterThread.start()

        s.close()

# The function handles downloading file 
# TCP connections are opened at the same time with mulitiple peers who has the file 
# Division of chunks to be downloaded from each peer is also done in the function
# After the download is complete, integrity of the downloaded file is also checked
def downloadFile(clientSocket, filename, relativeDir, serverPort, clientPort):
    endpoints = handleFileLocationRequest(clientSocket, filename)
    
    printEndpointsInfo(endpoints)
    endpointChunksDivisionInfo = divideChunksAmongEndpoints(endpoints)
    printEndpointsChunkDivisionInfo(endpointChunksDivisionInfo)

    filesize = 0
    fileHash = 0

    for file in filesOnNetwork:
        if filename == file["filename"]:
            filesize = file["size"]
            fileHash = file["hash"]

    chunksCount = filesize // 1000

    if chunksCount > 0:
        print(f"\nDownloading file: {filename}\n")

        threads = [
            threading.Thread(
                target=downloadChunks,
                args=(
                    endpointChunksDivisionInfo[i],
                    filename,
                    serverPort,
                    clientPort,
                ),
            )
            for i in range(len(endpointChunksDivisionInfo))
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
                downloadFile(s, filename, dirPath, serverPort, clientPort)

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
