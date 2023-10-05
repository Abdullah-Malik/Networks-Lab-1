from enum import Enum

class Message(Enum):
    REGISTER_REQUEST_INIT = "Register Request Init"
    REGISTER_REQUEST_ACK = "Register Request Ack"
    FILE_LIST_REQUEST = "File List Request"
    FILE_LOCATION_REQUEST_INIT = "File Location Request Init"
    FILE_LOCATION_REQUEST_ACK = "File Location Request Ack"
    CHUNK_REGISTER_REQUEST = "Chunk Register Request"
    FILE_CHUNK_REQUEST = "File Chunk Request"