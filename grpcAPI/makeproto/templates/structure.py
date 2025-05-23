class block:
    block_type: Literal['enum','oneof','message','service']
    name:str
    description:str
    options: list[str] # ex: "key = value"
    reserveds: tuple[str,str] # first is key reserveds: and second is index related reserveds...properly formated
{
    "block_type": "message",
    "name": "MyMessage",
    "description": "This is MyMessage",
    "options": ["deprecated = true", "map_entry = false"],
    "reserveds": ['"foo", "bar"', '1,4,5 to 8,12'],
    "fields": ["string name = 1;", "int32 id = 2;"]
}
class field:
    name:str
    ftype:Optional[str]
    number:int
    description: str
    options: list[str] # ex: "key = value"
    
{
    "name": "id",
    "ftype": "int32",
    "number": 1,
    "description": "Primary key",
    "options": ["deprecated = true", "packed = false"]
}

class method:
    name:str
    request_type:str
    request_stream:bool
    response_type:str
    response_stream: bool
    description: str
    options: list[str] # ex: "key = value"

{
    "name": "GetUser",
    "request_type": "GetUserRequest",
    "request_stream": False,
    "response_type": "User",
    "response_stream": True,
    "description": "Fetches a user.",
    "options": ["idempotency_level = IDEMPOTENT"]
}

PROTOFILE
{
    "version": "3",
    "description": "Protofile for user services.",
    "imports": ["google/protobuf/empty.proto"],
    "package": "user",
    "options": ["java_package = \"com.example.user\""],
    "blocks": [ ... strings ou renderizados ... ]
}
