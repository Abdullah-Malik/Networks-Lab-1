import argparse
import os
import json

def parseArguments():
    parser = argparse.ArgumentParser(description="Command-line argument example")

    parser.add_argument("--port", type=int, help="Port number")
    parser.add_argument("--dir", type=str, help="Directory path")

    args = parser.parse_args()

    return args

def crawlDirectory(directoryPath):
    totalFiles = 0
    fileInfoList = []

    if not os.path.isdir(directoryPath):
        raise ValueError("The provided path is not a valid directory.")

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

def printReceivedFiles(receivedFiles):
    print("Total files received:", len(receivedFiles))
    print("Files received:")
    for fileInfo in receivedFiles:
        filename = fileInfo.get("filename")
        size = fileInfo.get("size")
        print(f"  Filename: {filename}, Size: {size} bytes")

def registerFiles(files, lock, receivedFiles, port, ip):
    registeredFiles = []
    with lock:
        for fileInfo in receivedFiles:
            filename = fileInfo.get("filename")
            if filename:
                if filename not in files:
                    files[filename] = {
                        "size": fileInfo.get("size"),
                        "endpoints": [{"port": port, "ip": ip}],
                    }
                else:
                    files[filename]["endpoints"].append({"port": port, "ip": ip})
            registeredFiles.append({"filename": filename, "status": "Registered"})
    return registeredFiles

def convertToJsonAndEncode(dataDict):
    try:
        jsonData = json.dumps(dataDict).encode('utf-8')
        return jsonData
    except Exception as e:
        print(f"Error encoding dictionary to JSON: {e}")
        return None