from enum import Enum

class Message(Enum):
    REGISTER_REQUEST = "Register Request"
    FILE_LIST_REQUEST = "File List Request"
    FILE_LOCATIONS_REQUEST = "File Locations Request"
    CHUNK_REGISTER_REQUEST = "Chunk Register Request"
    FILE_CHUNK_REQUEST = "File Chunk Request"