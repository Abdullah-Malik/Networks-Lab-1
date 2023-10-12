from enum import Enum

class Message(Enum):
    REGISTER_REQUEST_INIT = "Register Request Init"
    REGISTER_REQUEST_ACK = "Register Request Ack"
    FILE_LIST_REQUEST = "File List Request"
    FILE_LOCATION_REQUEST_INIT = "File Location Request Init"
    FILE_LOCATION_REQUEST_ACK = "File Location Request Ack"
    CHUNK_REGISTER_REQUEST_INIT = "Chunk Register Request Init"
    CHUNK_REGISTER_REQUEST_ACK = "Chunk Register Request Ack"
    FILE_CHUNK_REQUEST_INIT = "File Chunk Request Init"
    FILE_CHUNK_REQUEST_ACK = "File Chunk Request Ack"

class InputEnum(Enum):
    FILE_LIST = "Files list"
    DOWNLOAD_FILE = "Download file"