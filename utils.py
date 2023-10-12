import argparse
import os
import json
import sys
import hashlib
import random

from message import InputEnum


def parseArguments():
    parser = argparse.ArgumentParser(description="Command-line argument example")

    parser.add_argument("--sp", type=int, help="Server port number")
    parser.add_argument("--cp", type=int, help="Client port number")
    parser.add_argument("--dir", type=str, help="Directory path")

    args = parser.parse_args()

    if args.sp is None or args.dir is None or args.cp is None:
        print("Error: One of the required arguments is missing")
        sys.exit(1)

    return args


def getHashOfFile(filePath):
    hashObject = hashlib.sha256()
    fileBytes = readFileInBytes(filePath)
    hashObject.update(fileBytes)
    hashHex = hashObject.hexdigest()

    return hashHex


def crawlDirectory(directoryPath):
    totalFiles = 0
    fileInfoList = []

    if not os.path.isdir(directoryPath):
        raise ValueError("The provided path is not a valid directory.")

    for root, _, files in os.walk(directoryPath):
        for filename in files:
            filePath = os.path.join(root, filename)
            fileSize = os.path.getsize(filePath)
            hashHex = getHashOfFile(filePath)
            fileInfoList.append(
                {"filename": filename, "size": fileSize, "hash": hashHex}
            )
            totalFiles += 1

    return fileInfoList, totalFiles


def printReceivedFiles(receivedFiles):
    print("Total files received:", len(receivedFiles))
    print("Files received:")
    for fileInfo in receivedFiles:
        filename = fileInfo.get("filename")
        size = fileInfo.get("size")
        print(f"  Filename: {filename}, Size: {size} bytes")
    print()


def registerFiles(files, lock, receivedFiles, port, ip):
    registeredFiles = []
    with lock:
        for fileInfo in receivedFiles:
            filename = fileInfo.get("filename")
            if filename:
                if filename not in files:
                    chunks = [i for i in range(1 + fileInfo.get("size") // 1000)]
                    files[filename] = {
                        "size": fileInfo.get("size"),
                        "endpoints": [{"port": port, "ip": ip, "chunks": chunks}],
                        "hash": fileInfo.get("hash"),
                    }
                else:
                    chunks = [i for i in range(1 + fileInfo.get("size") // 1000)]
                    files[filename]["endpoints"].append({"port": port, "ip": ip, "chunks": chunks})
            registeredFiles.append({"filename": filename, "status": "Registered"})

    return registeredFiles


def convertToJsonAndEncode(dataDict):
    try:
        jsonData = json.dumps(dataDict).encode("utf-8")
        return jsonData
    except Exception as e:
        print(f"Error encoding dictionary to JSON: {e}")
        return None


def readFileInBytes(filePath):
    try:
        with open(filePath, "rb") as file:
            fileData = file.read()
        return fileData
    except FileNotFoundError:
        return None
    except Exception as e:
        return str(e)


def takeUserInput():
    print("\nChoose an option:")
    print("1. Print list of files")
    print("2. Download a file")

    try:
        choice = int(input("Enter your choice (1/2): "))
    except ValueError:
        print("Invalid input. Please enter a valid number.")

    if choice == 1:
        return InputEnum.FILE_LIST.value, ""
    elif choice == 2:
        filename = input("Write the name of the file to download: ")
        return InputEnum.DOWNLOAD_FILE.value, filename
    else:
        print("Invalid choice")


def writeDownloadedFile(fileChunks, filename, relativeDir):
    currentDir = os.getcwd()
    filePath = os.path.join(currentDir, relativeDir, filename)

    try:
        sortedChunkIds = sorted(fileChunks[filename].keys())

        with open(filePath, "wb") as file:
            for chunkId in sortedChunkIds:
                chunk = fileChunks[filename][chunkId]
                chunk = chunk.encode("utf-8")
                file.write(chunk)
    except Exception as e:
        print(f"Error: {e}")

def printEndpointsInfo(endpoints):
    print("\nFile endpoints info:\n")
    for endpoint in endpoints:
        print(f"{endpoint['ip']}:{endpoint['port']} has chunks {endpoint['chunks']}\n")

def printEndpointsChunkDivisionInfo(endpoints):
    print("Chunks division info:\n")
    for endpoint in endpoints:
        print(f"{endpoint['ip']}:{endpoint['port']} will send chunks {endpoint['chunks']}\n")

def divideChunksAmongEndpoints(endpoints):
    freq = {}
    chunkEndpoints = {}
    endpointChunksDivisionInfo = []

    for endpoint in endpoints:
        endpointChunksDivisionInfo.append({"port": endpoint["port"], "ip": endpoint["ip"], "chunks":[]})
        for chunkId in endpoint['chunks']:
            if chunkId not in freq:
                freq[chunkId] = 1
            else:
                freq[chunkId] += 1

            if chunkId not in chunkEndpoints:
                chunkEndpoints[chunkId] = [{"port": endpoint["port"], "ip": endpoint["ip"]}]
            else:
                chunkEndpoints[chunkId].append({"port": endpoint["port"], "ip": endpoint["ip"]})

    sortedItems = sorted(freq.items(), key=lambda item: item[1])

    for chunkId, _ in sortedItems:
        selectionEndpoint = random.choice(chunkEndpoints[chunkId])
        for endpoint in endpointChunksDivisionInfo:
            if endpoint["port"] == selectionEndpoint["port"] and endpoint["ip"] == selectionEndpoint["ip"]:
                endpoint["chunks"].append(chunkId)

    return endpointChunksDivisionInfo

def deleteFile(filePath):
    try:
        os.remove(filePath)
        print(f"File '{filePath}' has been successfully deleted.")
    except OSError as e:
        print(f"Error: {e}")
