from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

macros = env.get_template("macros.j2")
render_block = macros.module.render_block
protofile_template = env.get_template("protofile.j2")
render_protofile = protofile_template.render
if __name__ == "__main__":

    message_block = {
        "block_type": "message",
        "name": "Person",
        "options": ["deprecated = true"],
        "reserveds": ['"name"', "1, 2, 3"],
        "fields": [
            {"name": "id", "ftype": "int32", "number": 1, "options": []},
            {
                "name": "email",
                "ftype": "string",
                "number": 2,
                "options": ["max_length = 255"],
            },
            {
                "block_type": "oneof",
                "name": "contact",
                "fields": [
                    {"name": "phone", "ftype": "string", "number": 3, "options": []},
                    {"name": "address", "ftype": "string", "number": 4, "options": []},
                ],
            },
        ],
    }

    enum_block = {
        "block_type": "enum",
        "name": "Status",
        "options": [],
        "reserveds": ["", ""],
        "fields": [
            {"name": "ACTIVE", "ftype": None, "number": 0, "options": []},
            {"name": "INACTIVE", "ftype": None, "number": 1, "options": []},
        ],
    }

    service_block = {
        "block_type": "service",
        "name": "UserService",
        "options": ["deprecated = true"],
        "reserveds": ["", ""],
        "fields": [
            {
                "name": "GetUser",
                "request_type": "GetUserRequest",
                "request_stream": False,
                "response_type": "GetUserResponse",
                "response_stream": False,
                "options": ['timeout = "30s"'],
            },
            {
                "name": "ListUsers",
                "request_type": "ListUsersRequest",
                "request_stream": True,
                "response_type": "ListUsersResponse",
                "response_stream": True,
                "options": [],
            },
        ],
    }

    message_rendered = render_block(message_block)
    enum_rendered = render_block(enum_block)
    service_rendered = render_block(service_block)

    proto_context = {
        "version": "3",
        "imports": ["google/protobuf/timestamp.proto"],
        "package": "example.v1",
        "options": ["java_multiple_files = true", 'java_package = "com.example.v1"'],
        "blocks": [message_rendered, enum_rendered, service_rendered],
    }

    protofile_content = protofile_template.render(proto_context)

    print(protofile_content)
