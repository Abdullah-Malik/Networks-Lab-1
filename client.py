import socket
import argparse
import sys
import os
from message import Message
import json

HOST = "127.0.0.1"

def sendRegisterRequest(clientSocket, ip, port, dir):
    fileInfoList, totalFiles = crawlDirectory(dir)

    fileInfoData = json.dumps({
        "file_info_list": fileInfoList,
        "total_files": totalFiles,
        "port": port,
        "ip": ip
    }).encode('utf-8')
    clientSocket.sendall(fileInfoData)

def waitRegisterReply(clientSocket):
    data = clientSocket.recv(1024)
    receivedData = json.loads(data)

    filesList = receivedData.get("files_list")
    for file in filesList:
        print(f'File: {file["filename"]} Status: {file["status"]}')

def sendFileLocationRequest(clientSocket, filename):
    clientSocket.sendall(filename.encode('utf-8'))

def waitFileLocationReply(clientSocket):
    data = clientSocket.recv(1024)
    receivedData = data.decode('utf-8')
    print(receivedData)

def waitFileListRequest(clientSocket):
    data = clientSocket.recv(1024)
    receivedData = json.loads(data)

    filesList = receivedData.get("files_list")
    fileCount = receivedData.get("file_count")
    print("Total files: ", fileCount)
    for file in filesList:
        print(f'Name: {file["filename"]} Size: {file["size"]}')

def crawlDirectory(directoryPath):
    totalFiles = 0
    fileInfoList = []

    # Check if the given path is a valid directory
    if not os.path.isdir(directoryPath):
        raise ValueError("The provided path is not a valid directory.")

    # Walk through the directory and its subdirectories
    for root, _, files in os.walk(directoryPath):
        for filename in files:
            filePath = os.path.join(root, filename)
            fileSize = os.path.getsize(filePath)
            fileInfoList.append({
                "filename": filename,
                "size": fileSize
            })
            totalFiles += 1

    return fileInfoList, totalFiles

def parseArguments():
    parser = argparse.ArgumentParser(description="Command-line argument example")

    parser.add_argument("--port", type=int, help="Port number")
    parser.add_argument("--dir", type=str, help="Directory path")

    args = parser.parse_args()

    return args

def main():
    args = parseArguments()

    if args.port is None or args.dir is None:
        print("Error: Both --port and --dir are required arguments.")
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, args.port))
        messageType = Message.FILE_LOCATION_REQUEST.value
        s.sendall(messageType.encode('utf-8'))
        print(messageType)

        if messageType == Message.REGISTER_REQUEST.value:
            sendRegisterRequest(s, HOST, args.port, args.dir)
            waitRegisterReply(s)
        elif messageType == Message.FILE_LIST_REQUEST.value:
            waitFileListRequest(s)
        elif messageType == Message.FILE_LOCATION_REQUEST.value:
            waitFileLocationReply(s)
            sendFileLocationRequest(s, "networks_history.txt")
            waitFileLocationReply(s)
        elif messageType == Message.CHUNK_REGISTER_REQUEST.value:
            print("Handling a Chunk Register Request.")
        elif messageType == Message.FILE_CHUNK_REQUEST.value:
            print("Handling a File Chunk Request.")

    # print(f"Received {data!r}")
    

if __name__ == "__main__":
    main()