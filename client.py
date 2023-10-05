import sys
import socket
import json

from utils import *
from network import *
from message import Message


HOST = "127.0.0.1"

def waitRegisteredFilesMessage(clientSocket):
    data = receiveData(clientSocket)
    if data is None:
        return
    jsonData = json.loads(data)

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
    print("Total files: ", fileCount)
    for file in filesList:
        print(f'Name: {file["filename"]} Size: {file["size"]}')


def handleFileLocationRequest(clientSocket, filename):
    data = receiveData(clientSocket)
    if data is None:
        return

    if data == Message.FILE_LOCATION_REQUEST_ACK.value:
        sendStringMessage(clientSocket, filename)

        endpointsData = receiveData(clientSocket)
        if endpointsData is None:
            return 
        
        print(endpointsData)
        return endpointsData

def main():
    args = parseArguments()

    if args.port is None or args.dir is None:
        print("Error: Both --port and --dir are required arguments.")
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, args.port))
        messageType = Message.FILE_LOCATION_REQUEST_INIT.value
        sendStringMessage(s, messageType)

        if messageType == Message.REGISTER_REQUEST_INIT.value:
            handleRegisterFilesRequest(s, HOST, args.port, args.dir)
        elif messageType == Message.FILE_LIST_REQUEST.value:
            handleFileListRequest(s)
        elif messageType == Message.FILE_LOCATION_REQUEST_INIT.value:
            handleFileLocationRequest(s, "networks_history.txt")

if __name__ == "__main__":
    main()
