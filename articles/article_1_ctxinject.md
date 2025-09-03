# Building a FastAPI-Like Framework for gRPC: Part 1 - The ctxinject Foundation

FastAPI showed what Python APIs could be—declarative functions, self-documenting signatures, elegant dependency injection. Python's gRPC libraries were robust and reliable, but somehow missed that same sense of pythonic joy and simplicity.

I found myself constantly missing FastAPI's developer experience: the way function signatures told the complete story, how testing was effortless, how dependencies were explicit and beautiful. gRPC gave me performance and type safety, but at the cost of that elegant, functional flow that made Python feel... well, pythonic.

This is the story of how I brought FastAPI's developer experience to gRPC—building on top of the solid foundation (grpcio) rather than reintenving the wheel. It started with ctxinject, a dependency injection framework that became the foundation for grpcAPI.

## HTTP vs gRPC: Framework Implications

The architectural differences between HTTP and gRPC create different opportunities for framework design, and understanding these differences was crucial to building something that felt right.

### Type Safety Differences

HTTP isn't type-safe by nature—any string can be a request´s body. This is why FastAPI leverages Pydantic for data validation and serialization; it's essential to fill that gap. But gRPC uses Protocol Buffers, which are type-safe and efficient by design. Validation and serialization become less critical in gRPC (though we can still add JSON support for existing data).

### Flexibility Trade-offs

HTTP offers lots of flexibility: methods (GET/POST), headers, body formats, path/query parameters, cookies. gRPC has a more constrained request/response structure. The context object gives some flexibility to customize method handling behavior, but the mechanism feels verbose and un-pythonic.

### The Developer Experience Gap

The contrast becomes clear when you see them side by side. Here's FastAPI's approach:

```python
# Self-documenting, declarative, functional
@app.post("/users/")
async def create_user(
    user: User,  # Clear contract
    db: Database = Depends(get_db),  # Explicit dependencies
):
    return await db.create(user)  # Pure business logic
```

And here's the traditional Python gRPC approach:

```python
# Powerful, but more ceremonial
class UserServicer(user_pb2_grpc.UserServiceServicer):
    def __init__(self, db_pool, auth_service):  # Constructor injection
        self.db_pool = db_pool
        
    def CreateUser(self, request, context):
        # Always the same signature - no flexibility
        # Dependencies hidden in self
        # Business logic mixed with gRPC plumbing
```

**The Opportunity:** Since gRPC already provides type safety through Protocol Buffers, we don't need to solve validation/serialization like FastAPI does. Instead, we can focus purely on developer experience: bringing FastAPI's declarative patterns and elegant dependency injection to gRPC's solid foundation.

## The Vision: What We Want to Achieve

The goal was to combine the best of both worlds:

```python
# grpcAPI - FastAPI-style flexibility for gRPC
@user_service
async def create_user(
    user: User,  # User from protobuf - type safe!
    db: Database = Depends(get_db),  # Explicit dependencies
) -> StringValue:  # Return type mapped to protobuf
    # Clean, testable, flexible business logic
    return StringValue(value=await db.create(user))
```

The benefits I was targeting:
- Keep gRPC's performance, type safety, and ecosystem
- Add FastAPI's developer experience magic
- Self-documenting function signatures
- Easy testing and mocking
- Pythonic, functional approach
- Clean separation of concerns

## Enter ctxinject: The Foundation

### The Core Challenge

How do you make gRPC handler signatures as flexible as FastAPI? It comes down to several technical challenges:

- **Function signature analysis and transformation at runtime** - Parse any function signature and understand what each parameter needs
- **Type-safe dependency resolution with Python's type system** - Use type hints to match dependencies without losing static analysis benefits
- **Async/sync compatibility for modern Python patterns** - Handle both sync and async functions seamlessly, including contextmanager
- **Performance** - Do signature mapping at bootstrap time, enable parallel async dependency processing

### Design Principles

Building ctxinject, I followed these core principles:

1. **Type Safety First** - Leverage Python's typing system completely. No new syntax to learn.
2. **Async Native** - Built for modern async Python patterns from day one.
3. **Performance Conscious** - Minimal runtime overhead through pre-computed resolution.
4. **Extensible** - Custom Injectable subclasses for domain-specific injection patterns.

### Key Features Showcase

```bash
pip install ctxinject
```

Here's ctxinject in action:

```python
from ctxinject import inject_args, Depends, ModelFieldInject

# Simple dependency injection magic
async def get_database() -> Database:
    return Database()

class User:
    def __init__(self, username: str, active: bool):
        self.username = username
        self.active = active

async def handler(
    name: str,  # Injected by name from context
    user: User, # Injected by type from context
    username: str = ModelFieldInject(User),  # Extracted from User.username
    db: Database = Depends(get_database)  # Via factory function
):
    if user.active:
        name = username
    return await db.find(name)

# The magic transformation
context = {"name": "John", User: User('Laura', False)}
injected_func = await inject_args(handler, context)
result = await injected_func()  # Dependencies resolved automatically!
```

What makes this powerful:

- **ModelFieldInject**: Extract values from model instances' field in context
- **DependsInject**: Function dependencies with recursive resolution and contextmanager handling
- **Async optimization**: Concurrent dependency resolution when possible
- **Validation integration**: Clean, validated values guaranteed
- **Override system**: Perfect for testing and environment-specific behavior

### Advanced Features That Matter

ctxinject includes several advanced features that became crucial for production use:

**Model field injection** extracts from domain objects:
```python
@service
async def handle_request(
    user_id: str = ModelFieldInject(AuthContext), #if field name fits arg name, no need to declare
    is_admin: bool = ModelFieldInject(AuthContext, "has_admin_role") #declare field name if not
    recursive: str = ModelFieldInject(OtherClass, "field1.field2.field3") #nested class fields
):
    pass
```

**Function signature static analysis**
`func_signature_check` validates function signatures for injection compatibility. It checks the integrity of the entire signature (including circular dependency) and returns a list of all errors rather than failing on the first issue, enabling comprehensive validation feedback.
This feature sets the basis for grpcAPI's lint command

**Supertype vs Subtype handling**

- **Compatibility is one-way: subtype → supertype**
- **List[Derived] fits Iterable[Base], not the reverse**
- **Prevents unsafe narrowing**

```python
class BaseClass:
    pass
class DerivedClass(BaseClass):
    pass

class MyClass:
    def __init__(self, list1: List[str]):
        self.list1 = list1

def get_class() -> DerivedClass:
    return DerivedClass()

def func(
    list1: Iterable[str] = ModelFieldInject(MyClass), #Iterable[str] <- List[str] = "OK"
    db: BaseClass = DependsInject(get_class), # BaseClass <- DerivedClass = "OK"
):
    pass
```

This example pass `func_signature_check` due to supertype vs subtype compatibility

**In build and customized validation and casting**


**Override system** makes testing elegant:
```python
# Production
async def get_real_database() -> Database: ...
# Testing  
async def get_mock_database() -> Database: ...

async def handler(db:Database = DependsInject(get_real_database)):...

# Simple override
overrides = {get_real_database: get_mock_database}
injected = await inject_args(handler, context, overrides=overrides)
```

**Validation system**

In built and customized validation and casting. Optional pydantic casting.

```python
from ctxinject import DependsInject, ModelFieldInject, Validation

def custom_validator(word: str) -> str:
    if not word.isalpha():
        raise ValueError("Invalid input: only alphabetic characters are allowed.")
    return word.upper()

def func(
    name: str = Validation(min_length=2, pattern=r"^[a-zA-Z]+$"), #inject by name
    lastname: str = Validation(validator=custom_validator), #inject by name
    array: Iterable[str] = ModelFieldInject(MyClass, min_length=2, max_length=100), #inject by type
    db_str: str = DependsInject(get_db, max_length=256),
):
    pass

```

**Pydantic Example**

Optional pydantic casting from str and bytes (`model_validate_json`)

```bash
pip install ctxinject[pydantic]
```

```python
class MyModel(BaseModel):
    name: str
    age: int

class BaseClass:
    def __init__(self, model: str):
        self.model = model

def handler(
    mymodel: MyModel = CastType(str), #injected by name
    model: MyModel = ModelFieldInject(BaseClass) #injected by type
): ...

mymodel = '{"name": "John", "age": 42}'
ctx = {mymodel: mymodel, BaseClass: BaseClass(mymodel)}
```

This can enable  json_string -> Pydantic convertion from protobuf str and bytes field

## Real-World Impact: Before and After

The transformation in developer experience was dramatic:

**Before ctxinject - Traditional Class-based:**
```python
class AccountServicer:
    def __init__(self, db, validator, id_gen):
        self.db = db
        self.validator = validator  
        self.id_gen = id_gen
        
    def SignUp(self, request, context):
        # Tightly coupled, hard to test
        # Dependencies hidden in constructor
        # Business logic mixed with gRPC plumbing
        try:
            validated = self.validator.validate(request.account_info)
            account_id = self.id_gen.generate()
            return self.db.create_account(account_id, validated)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            return AccountResponse()
```

**After ctxinject - Functional & Clean:**
```python
@account_services
async def signup_account(
    account_info: AccountInfo,
    id: Annotated[str, Depends(make_account_id)],
    acc_repo: AccountRepository,
) -> StringValue:
    # Pure business logic, easy to test
    # Dependencies explicit in signature
    # Self-documenting contract
    return StringValue(value=await acc_repo.create_account(id, account_info))
```

**Testing becomes trivial:**
```python
# Unit test - no gRPC server needed!
context = {
    AccountInfo: mock_account,
    AccountRepository: mock_repo,
    str: "generated-id"  # For the Depends(make_account_id) result
}
injected = await inject_args(signup_account, context)
result = await injected()
assert result.value == "expected-account-id"
```

The difference is night and day. Dependencies are explicit, testing is straightforward, and the business logic is completely separated from gRPC concerns.

## Performance Characteristics

One concern with dependency injection is performance overhead. ctxinject addresses this through several optimizations:

- **Signature analysis happens once** at startup, not per request
- **Dependency resolution is pre-computed** into an execution plan
- **Context Manager handling** sync and async
- **Async dependencies run concurrently** when order allows
- **Type lookups use efficient hash maps** rather than iteration
- **Validation occurs only when configured**, not by default

In practice, the injection overhead is negligible compared to typical gRPC business logic, and the async concurrency can actually improve performance for I/O-bound dependencies.

## Ctxinject usage in grpcAPI

In grpcAPI, the ctxinject types are derived for the following classes
- **Depends** just a rename for DependsInject
- **FromRequest** ModelFieldInject from your request protobuf type
- **FromContext** ModelFieldInject from grpcio context object

See examples:

```python
@user_services(tags=["write:ride", "read:account"])
async def request_ride(
    request: RideRequest,
    passenger_id: Annotated[str, FromRequest(RideRequest,validator=passenger_id_validator)],
    id: Annotated[str, Depends(make_ride_id)],
) -> StringValue:
```

In the above case, `RideRequest` is a protobuf class. `request` if the instance itself, and passenger_id is taken from `RideRequest` in order to add a validation only

```python
@serviceapi(request_type_input=AccountInput, response_type_input=Empty)
    async def log_accountinput(
        name: str,
        email: EmailStr, #need pydantic installed
        payload: Struct,
        itens: ListValue,
        db: str = Depends(get_db),
    ):...
```

In the above case, `AccountInput` is the protobuf class request. Empty is a google well known type

```protobuf
syntax = "proto3";

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";

message AccountInput {
    string name=1;
    string email=2;
    google.protobuf.Struct payload = 3;
    google.protobuf.ListValue itens = 4;
}
```
As it is declared in the decorator, you can declare an arg with the same name as the message field.

## Coming Next: Building the Complete Framework

ctxinject solved the core dependency injection challenge, but building a complete FastAPI-like experience for gRPC required tackling much bigger problems:

**Part 2: "Taming protoc"** - How do you automatically generate gRPC servicers and descriptors from decorated Python functions? Auto-generating .proto files from Python function signatures with proper error reporting and linting.

**Part 3: "Production Tooling"** - Server plugins, service filtering, language options to .proto files addition, grpc-gateway config inclusion, custom service processing utilities, and a testing client that makes gRPC feel as approachable as HTTP.

**Part 5: "Guber Case Study"** - A real ride-sharing application that demonstrates transforming from monolith to microservices using just configuration and dependency overrides.

**Spoiler alerts:** The built-in linting catches type mismatches before they become debugging marathons. Service filtering lets you run different microservice configurations from the same codebase. And the testing story gets really, really elegant.

---

*Want to try ctxinject standalone? It works great outside of gRPC too. Check out the [ctxinject documentation](https://github.com/bellirodrigo2/ctxinject) or star the [grpcAPI repo](https://github.com/bellirodrigo2/grpcAPI). What gRPC pain points are you facing? I'd love to hear about them in the comments.*

*Next week: How I reverse-engineered protoc to make gRPC servicers generate themselves from function signatures. It involves more reflection than I initially expected...*