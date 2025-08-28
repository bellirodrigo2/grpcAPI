# 🚀 **grpc**_API_

<p align="center">
    <b>🔥 grpcAPI framework, high performance, easy to learn, fast to code, ready for production 🔥</b>
</p>

grpcAPI is a modern gRPC framework for building APIs with Python 3.8+ based on standard Python type hints and the official gRPC library.

**Note**: grpcAPI requires protobuf classes (from `protoc` compilation) for request/response types. Use the built-in `grpcapi protoc` command to compile `.proto` files with mypy stub generation.

The key features are:

* **Automatic Protocol Buffer Generation**: Generate `.proto` files automatically from Python service definitions
* **Type-Safe Service Definitions**: Use Python type hints to define gRPC services with automatic validation
* **Dependency Injection**: Built-in dependency injection system with `Depends`, `FromRequest`, and `FromContext`
* **Streaming Support**: Full support for client streaming, server streaming, and bidirectional streaming
* **Extensible Plugin System**: `grpc.aio.Server` wrapper with decoupled plugin architecture - includes built-in health check and reflection plugins, with support for custom user plugins
* **CLI Tools**: Command-line interface for running servers, building protos, function signature lint and validation
* **Test Client**: Built-in test client for testing services without network calls

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
```

## Basic Example

Create a file `main.py`:

```python
from grpcAPI import GrpcAPI, APIPackage
from grpcAPI.protobuf import StringValue

app = GrpcAPI()
service = APIService("greeter_service")

@service
async def say_hello(name: str) -> StringValue:
    return StringValue(value=f"Hello {name}")

app.add_service(service)
```

Run the server:

```bash
grpcapi run main.py
```

This starts a gRPC server using your service definitions. Additional features like protocol buffer file generation, reflection, and health checking are available through configuration.

## Dependency Injection Example

```python
from grpcAPI import GrpcAPI, APIPackage, Depends
from grpcAPI.protobuf import StringValue
from typing_extensions import Annotated

app = GrpcAPI()
service = APIService("user_service")

def get_database():
    return {"users": []}

@service
async def create_user(
    name: str,
    db: Annotated[dict, Depends(get_database)]
) -> StringValue:
    db["users"].append({"name": name})
    return StringValue(value=f"User {name} created")

app.add_service(service)
```

## Streaming Example

```python
from typing import AsyncIterator

@service
async def stream_messages(user_id: str) -> AsyncIterator[StringValue]:
    for i in range(5):
        yield StringValue(value=f"Message {i} for {user_id}")
```

## CLI Commands

```bash
# Initialize new project
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

## Service Filtering with Tags

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

Filter services using configuration:

```json
{
  "service_filter": {
    "tags": {
      "exclude": ["internal"]
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

## Protocol Buffer Options

Add language-specific options to generated `.proto` files using the module header system:

```python
from grpcAPI.process_service.add_module_header import AddLanguageOptions

# Add language-specific options with template variables
language_options = AddLanguageOptions({
    "java_package": "com.mycompany.{package}",
    "java_outer_classname": "{module}Proto", 
    "java_multiple_files": "true",
    "go_package": "github.com/mycompany/{package}/{module}pb",
    "csharp_namespace": "MyCompany.{package}.{module}",
    "option cc_enable_arenas": "true"
})

# Apply to all services, or filter by package/module/tags
app.add_process_service(language_options)
```

Generated `.proto` file will include:
```protobuf
syntax = "proto3";

option java_package = "com.mycompany.com.example.users";
option java_outer_classname = "user_serviceProto";
option java_multiple_files = true;
option go_package = "github.com/mycompany/com.example.users/user_servicepb";
option csharp_namespace = "MyCompany.com.example.users.user_service";
option cc_enable_arenas = true;

package com.example.users;
// ... rest of proto file
```

**Template Variables:**
- `{package}` - Replaced with the service package name
- `{module}` - Replaced with the module name (proto filename)

**Filtering Support:**
```python
# Apply options only to specific packages/modules
AddLanguageOptions(
    {"java_package": "com.api.{package}"},
    package=IncludeExclude(include=["com.example.*"]),
    module=IncludeExclude(exclude=["internal*"]),
    tags=IncludeExclude(include=["public"]),
    rule_logic="AND"
)
```

## Plugin System

grpcAPI wraps `grpc.aio.Server` with a decoupled plugin system. Built-in plugins include:

- **Health Check Plugin**: Automatic health checking endpoints with graceful shutdown
- **Reflection Plugin**: gRPC reflection for service discovery  
- **Server Logger Plugin**: Structured logging for requests

Create custom plugins by implementing the `ServerPlugin` protocol with lifecycle hooks:
- `on_register()` - Called when plugin is registered
- `on_add_service()` - Called when services are added  
- `on_start()` - Called when server starts
- `on_stop()` - Called when server stops

## Example Application

See the complete [Guber ride-sharing example](./example/guber/) for:
- Domain-driven design patterns
- SQLAlchemy integration
- Streaming operations  
- Comprehensive tests
- Production configuration

## License

This project is licensed under the terms of the MIT license.