<p align="center">
  <img src="assets/logo.jpg" alt="grpcAPI Logo" width="300" height="auto">
</p>

<p align="center">
    <b> + pythonic, + flexibility, - learning curve</b>
</p>

grpcAPI is a modern gRPC framework for building APIs with Python 3.8+ based on standard Python type hints and grpcio library.

The key features are:

* **Type-Safe Service Definitions**: Use Python type hints to define gRPC services with automatic validation
* **Advanced Function Signatures**: Powerful parameter extraction with `FromRequest`, `FromValue`, `FromContext` - extract specific fields from protobuf messages, apply custom validators, FastAPI `Depends` like dependency injection, and define complex input/output mappings all through function signatures
* **Streaming Support**: Full support for client streaming, server streaming, and bidirectional streaming
* **Automatic Protocol Buffer Generation**: Generate service `.proto` files automatically from Python functions signature, with lint tool
* **Service Processing Pipeline**: Powerful post-processing system with service filtering, protocol buffer language options (`AddLanguageOptions`), HTTP gateway annotations (`AddGateway`), and custom module headers
* **Dependency Injection**: Built-in dependency injection system with `Depends`, `FromRequest`, and `FromContext`
* **Extensible Plugin System**: `grpc.aio.Server` wrapper with decoupled plugin architecture - includes built-in health check and reflection plugins, with support for custom user plugins
* **CLI Tools**: Command-line interface for running servers, building protos, function signature lint and validation
* **Test Client**: Built-in test client for testing services without network calls

**Note**: grpcAPI requires protobuf classes (from `protoc` compilation) for request/response types. Use the built-in `grpcapi protoc` command to compile `.proto` files with mypy stub generation.

## Requirements

Python 3.8+

Main dependencies:

* **grpcio** - The official gRPC Python library
* **grpcio-tools** - Protocol Buffer compilation tools
* **ctxinject** - Dependency injection and type mapping

Optional dependency:
* **pydantic** - For automatic validation and casting from protobuf string/bytes fields to Python types

## Installation

```bash
pip install grpcapi
pip install grpcapi[pydantic]
```

## Basic Example

Create a file `main.py`:

```python
from grpcAPI import GrpcAPI, APIService
from grpcAPI.protobuf import StringValue

app = GrpcAPI(name="myapp", version="v1") #name and version are optional (default: GrpcAPI and v1)
service = APIService("greeter_service")

@service
async def say_hello(name: StringValue) -> StringValue:
    return StringValue(value=f"Hello {name.value}")

app.add_service(service)
```

Run the server:

```bash
grpcapi run main.py
```

This starts a gRPC server using your service definitions. Additional features like protocol buffer file generation, reflection, and health checking are available through configuration.

```bash
grpcapi build main.py
```
This command analyzes your Python service definitions and generates a complete protocol buffer ecosystem: service `.proto` files derived from your Python function signatures, message and enum definitions for all referenced types, proper import relationships, and language-specific options - creating a production-ready gRPC API specification from your Python code.

## Function Signature Alternatives
*Powered by ctxinject library*

grpcAPI offers multiple ways to define service methods, from simple to advanced:

```python
from typing import Annotated, List
from grpcAPI import APIService, Depends, FromRequest, FromContext, Validation
from grpcAPI.protobuf import StringValue, BytesValue
from lib.my_lib_pb2 import User  # Generated protobuf class

service = APIService("user_service")

# Simple: Direct protobuf types
@service
async def create_user(user: User, ctx: AsyncContext) -> StringValue:
    pass

@service(request_type_input=User)
async def create_user(
    name: str = Validation(min_length=3, max_length=100),
    tags: List[str] = Validation(lambda x: list(set(x)))  # Remove duplicates
) -> StringValue:
    pass

# Advanced: Field extraction with constraints
@service
async def create_user(
    name: Annotated[str, FromRequest(User, min_length=3, max_length=100)],
    tags: Annotated[List[str], FromRequest(User, validator=lambda x: list(set(x)))],
    peer: Annotated[str, FromContext()]  # Get client IP
) -> StringValue:
    pass

# Dependency injection
def get_database():
    db = Database()
    yield db
    db.close()

@service
async def create_user_di(
    name: StringValue,
    db: Annotated[Database, Depends(get_database)]
) -> StringValue:
    pass

# Pydantic integration (optional)
from pydantic import BaseModel
class UserModel(BaseModel):
    name: str
    email: str

@service(request_type_input=BytesValue)
async def pydantic_user(user: UserModel) -> Empty:  # Auto JSON conversion from str or bytes fiels
    pass

# Streaming example
@service
async def stream_users(
    request: AsyncIterator[User],  # Client streaming has less flexibility
    metadata: Metadata  # Mapping[str,str] from context.invocation_metadata()
) -> Empty:
    pass
```

## Lint Tool

The `grpcapi lint` command validates all service function signatures and reports errors comprehensively rather than stopping at the first issue found.

```python
from grpcAPI import GrpcAPI, APIService
from grpcAPI.protobuf import StringValue, BytesValue

app = GrpcAPI()

service = APIService('service1')


@service
async def my_service(
    strvalue: StringValue,
    bytesvalue: BytesValue,  # two diferent request protobuf objects
) -> StringValue:  # no return type annotation
    pass


@service
async def my_service2(
    bytesvalue: BytesValue,
):  # no return type annotation
    pass

app.add_service(service)

```
![Lint Error Report](assets/lint_error.png)

Validates types, names, imports, signatures, and custom rules across all services with structured error reporting.

## CLI Commands

```bash
# Initialize new project, creating a config file
grpcapi init

# Run development server
grpcapi run app.py

# Build .proto files  
grpcapi build app.py --output ./proto

# Validate service definitions
grpcapi lint app.py

# List all services
grpcapi list app.py
```


## Service Organization

grpcAPI offers flexible service organization from simple to complex projects:

### Quick Start (Simple)
```python
# Direct service creation - no package, module defaults to "service"
service = APIService("my_service")
app.add_service(service)
```

### Package Level (Intermediate)  
```python
# Custom package, module defaults to "service"
package = APIPackage("account")
service = package.make_service("user_service")
app.add_service(package)
```

### Full Control (Complex)
```python
# Complete control over package/module structure
package = APIPackage("account")
module = package.make_module("user")  # Creates user.proto
service = module.make_service("user_actions")
app.add_service(package)
```

This creates the hierarchy:
```
GrpcAPI
├── APIPackage ("account")
│   ├── APIModule ("user") → generates user.proto
│   │   └── APIService ("user_actions")
│   │       └── @service decorated methods
```

## Configuration

Configure grpcAPI using `grpcapi.config.json`:

```json
{
  "host": "localhost",
  "port": 50051,
  "lint": true, // Enable proto validation
  "service_filter": {
    "tags": {"exclude": ["internal"]},
    "package": {"include": ["api", "public"]},
    "rule_logic": "AND"
  },
  "plugins": {
    "health_check": {},
    "reflection": {},
    "server_logger": {}
  },
  "tls": {
    "enabled": true,
    "certificate": "path/to/cert.crt",
    "key": "path/to/cert.key"
  }
}
```

**Available Settings:**
- **Server**: Host, port, TLS configuration, compression, worker limits
- **Service Filtering**: Include/exclude by package, module, or tags
- **Plugins**: Health check, reflection, custom logging configuration
- **Protocol Buffers**: Output paths, compilation options, file overwrite settings
- **Environment**: Set environment variables for the application

## Testing

Built-in test client for unit testing services without network overhead:

```python
import pytest
from grpcAPI.testclient import TestClient, ContextMock

async def test_service_with_context_tracking():
    client = TestClient(app, settings={})
    context = ContextMock(peer="127.0.0.1:12345", deadline=30.0)
    
    response = await client.run(
        func=create_user, #imported from source code
        request=user_data, #input protobuf variable
        context=context
    )
    
    # Verify response
    assert response.value.startswith("user_")
    
    # Verify context interactions (MagicMock-like tracking)
    context.tracker.peer.assert_called_once()
    context.tracker.time_remaining.assert_called()
    assert context.tracker.set_code.call_count == 0
    
    # Reset for next test
    context.tracker.reset_mock()
```

**TestClient Features:**
- **Direct method calls**: `client.run(func, request, context)` or `client.run_by_label(package, service, method, request)`
- **Dependency override**: Use `app.dependency_overrides` for mocking dependencies
- **Context simulation**: Full `AsyncContext` mock with peer info, timeouts, metadata
- **Call tracking**: `ContextMock.tracker` works like `MagicMock` with `assert_called_once()`, `call_count`, etc.
- **Streaming support**: Test server/client/bidirectional streaming patterns
- **pytest integration**: Works seamlessly with async fixtures


## Built-in tools

### Service Filtering with Tags

Services and methods can be tagged for filtering during builds or deployments:

```python
# Tag services and methods
@account_services(tags=["write:account"])
async def create_user(user_data: UserInfo) -> StringValue:
    # Implementation
    pass

@account_services(tags=["read:account", "internal"])
async def get_internal_data(user_id: str) -> UserData:
    # Implementation  
    pass
```

Filter services using configuration, with `fnmatch` syntax:

```json
{
  "service_filter": {
    "tags": {
      "exclude": ["internal", "write*"]
    },
    "package": {
      "include": ["account", "ride"]
    },
    "rule_logic": "AND"
  }
}
```

This enables:
- **Microservice deployment**: Include only specific packages per service
- **Environment-specific builds**: Exclude internal/debug methods from production
- **API versioning**: Filter by version tags
- **Permission-based filtering**: Include only authorized service methods

### Protocol Buffer File Level Options Inclusion

#### Language options

Add language-specific options to generated `.proto` files using configuration:

```json
"language_options":{
    "kv_map":{
        "java_package": "com.{name}.{version}.{package}",
        "java_outer_classname": "{module}Proto",
        "java_multiple_files": true,
        "go_package": "github.com/{name}/{package}/{module}pb",
        "csharp_namespace": "MyCompany.{package}.{module}",
        "cc_enable_arenas": true
        }
  },
```

Generated `.proto` file will include:
```protobuf
syntax = "proto3";

option java_package = "com.my_app.v1.users";
option java_outer_classname = "user_serviceProto";
option java_multiple_files = true;
option go_package = "github.com/my_app.users/user_servicepb";
option csharp_namespace = "MyCompany.users.user_service";
option cc_enable_arenas = true;

package com.example.users;
// ... rest of proto file
```

**Template Variables:**
- `{name}` - Replaced with the app name
- `{version}` - Replaced with the app version
- `{package}` - Replaced with the service package name
- `{module}` - Replaced with the module name (proto filename)


#### Gateway Syntax - `grpc-gateway`

```python
@service(gateway={"get": "/api/users/{user_id}"})
async def get_user(user_id: StringValue) -> UserInfo:
    pass

@service(gateway={"post": "/api/users", "body": "*"})
async def create_user(user: UserInfo) -> StringValue:
    pass
```

## Plugin System

grpcAPI wraps `grpc.aio.Server` with a decoupled plugin system.
**Note**: You can pass your own server instance: `GrpcAPI(server=my_server)`.

Built-in plugins include:

- **Health Check Plugin**: Automatic health checking endpoints with graceful shutdown
- **Reflection Plugin**: gRPC reflection for service discovery  
- **Server Logger Plugin**: Structured logging for requests

Create custom plugins by implementing the `ServerPlugin` protocol with lifecycle hooks:
- `on_register()` - Called when plugin is registered
- `on_add_service()` - Called when services are added  
- `on_start()` - Called when server starts
- `on_stop()` - Called when server stops

## Example Application

See the complete [Guber ride-sharing example](https://github.com/bellirodrigo2/guber) for:
- Domain-driven design patterns
- SQLAlchemy integration
- Streaming operations  
- Comprehensive tests
- Production configuration
- Monolith to microservice deployment by configs and dependency_override

## License

This project is licensed under the terms of the MIT license.