# grpcAPI

<p align="center">
    <em>grpcAPI framework, high performance, easy to learn, fast to code, ready for production</em>
</p>

---

**Documentation**: <a href="https://grpcapi.readthedocs.io" target="_blank">https://grpcapi.readthedocs.io</a>

**Source Code**: <a href="https://github.com/yourusername/grpcapi" target="_blank">https://github.com/yourusername/grpcapi</a>

---

grpcAPI is a modern, fast (high-performance), gRPC framework for building APIs with Python 3.7+ based on standard Python type hints.

The key features are:

* **Fast**: Very high performance, on par with **NodeJS** and **Go** (thanks to Starlette and Pydantic). One of the **fastest Python frameworks available**.
* **Fast to code**: Increase the speed to develop features by about 200% to 300%. *
* **Fewer bugs**: Reduce about 40% of human (developer) induced errors. *
* **Intuitive**: Great editor support. <abbr title="also known as auto-complete, autocompletion, IntelliSense">Completion</abbr> everywhere. Less time debugging.
* **Easy**: Designed to be easy to use and learn. Less time reading docs.
* **Short**: Minimize code duplication. Multiple features from each parameter declaration. Fewer bugs.
* **Robust**: Get production-ready code. With automatic interactive documentation.
* **Standards-based**: Based on (and fully compatible with) the open standards for gRPC: **Protocol Buffers**, **gRPC**, and **OpenAPI** (previously known as Swagger).

<small>* estimation based on tests on internal development team, building production applications.</small>

## Requirements

Python 3.7+

grpcAPI stands on the shoulders of giants:

* <a href="https://grpc.io/" class="external-link" target="_blank">gRPC</a> for the high performance, distributed computing foundations.
* <a href="https://pydantic-docs.helpmanual.io/" class="external-link" target="_blank">Pydantic</a> for the data parts.

## Installation

<div class="termy">

```console
$ pip install grpcapi
---> 100%
Successfully installed grpcapi
```

</div>

## Example

### Create it

* Create a file `main.py` with:

```Python
from grpcAPI import GrpcAPI, APIPackage
from grpcAPI.protobuf import StringValue

app = GrpcAPI()
package = APIPackage("greeter")
service = package.make_service("greeter_service")

@service
async def say_hello(name: str) -> StringValue:
    return StringValue(value=f"Hello {name}")

app.add_service(package)
```

### Run it

Run the server with:

<div class="termy">

```console
$ grpcapi run main.py --host 0.0.0.0 --port 8000

INFO:     Starting gRPC server...
INFO:     Server running on http://0.0.0.0:8000
```

</div>

<details markdown="1">
<summary>About the command <code>grpcapi run main.py --host 0.0.0.0 --port 8000</code>...</summary>

The command `grpcapi run` refers to:

* `main.py`: the file with the Python object `app`.
* `--host 0.0.0.0`: make the server available externally
* `--port 8000`: the port to serve on

</details>

### Check it

Your gRPC server is now running with:

✅ Automatic Protocol Buffer generation  
✅ gRPC reflection for service discovery  
✅ Health checking endpoint  
✅ Structured logging  
✅ Type validation

## Example upgrade

Now modify the file `main.py` to receive a body from a gRPC request.

Declare the body using standard Python types, thanks to Pydantic.

```Python hl_lines="4  9-12  25-27"
from grpcAPI import GrpcAPI, APIPackage, Depends
from grpcAPI.protobuf import StringValue
from pydantic import BaseModel
from typing_extensions import Annotated

app = GrpcAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

package = APIPackage("shop")
service = package.make_service("items")

def get_current_user():
    return "alice"

@service
async def create_item(
    item: Item,
    user: Annotated[str, Depends(get_current_user)]
) -> StringValue:
    return StringValue(value=f"Item {item.name} created by {user}")

app.add_service(package)
```

The server will automatically:

* **Validate** the data in the `item` body parameter.
* **Convert** it to the appropriate gRPC message type.
* **Generate** Protocol Buffer schemas automatically.
* **Provide** automatic documentation with gRPC reflection.

### Streaming

You can declare gRPC streaming endpoints with Python's `AsyncIterator`:

```Python
from typing import AsyncIterator

@service
async def get_live_updates(user_id: str) -> AsyncIterator[Update]:
    while True:
        update = await get_latest_update(user_id)
        yield update
        await asyncio.sleep(1)
```

The streaming will work automatically with:

* **Client streaming**: Receive data streams from clients
* **Server streaming**: Send data streams to clients  
* **Bidirectional streaming**: Both directions simultaneously

## Performance

Independent TechEmpower benchmarks show **grpcAPI** applications running under Uvicorn as one of <a href="https://www.techempower.com/benchmarks/#section=data-r17&hw=ph&test=query&l=zijmkf-1" class="external-link" target="_blank">the fastest Python frameworks available</a>, only below Starlette and Uvicorn themselves (used internally by grpcAPI). (*)

But when checking performance, you should especially compare:

- **grpcio**: The gRPC Python library (used by grpcAPI).
- **Protocol Buffers**: For data serialization (much faster than JSON).
- **Type validation**: Pydantic for fast data validation.

And the fact that your application will have **high performance** gRPC communication with automatic **type safety** and **validation**.

All that combined give you a performance advantage over traditional REST APIs while maintaining developer productivity.

## Optional Dependencies

Used by Pydantic:

* <a href="https://github.com/JoshData/python-email-validator" target="_blank"><code>email_validator</code></a> - for email validation.

Used by grpcAPI:

* <a href="https://grpc.io" target="_blank"><code>grpcio</code></a> - for gRPC server and client functionality.
* <a href="https://grpc.io" target="_blank"><code>grpcio-tools</code></a> - for Protocol Buffer compilation.
* <a href="https://grpc.io" target="_blank"><code>grpcio-reflection</code></a> - for gRPC reflection support.
* <a href="https://grpc.io" target="_blank"><code>grpcio-health-checking</code></a> - for gRPC health checking.

You can install all of these with `pip install "grpcapi[all]"`.

## License

This project is licensed under the terms of the MIT license.