# Guber - grpcAPI Example Application

This directory contains **Guber**, a ride-sharing application that demonstrates the power and flexibility of grpcAPI through a Domain-Driven Design (DDD) architecture. It serves as a comprehensive proof of concept showcasing how grpcAPI can seamlessly transition between monolithic and microservices architectures.

## 🏗️ Architecture Overview

The example follows **Domain-Driven Design** principles with clear separation of concerns:

- **Domain Layer**: Business entities, value objects, and rules
- **Application Layer**: Use cases, repositories, and gateways 
- **Infrastructure Layer**: Database adapters (SQLAlchemy) and external service implementations
- **Presentation Layer**: gRPC services and protocol buffer definitions

## 🚀 Two Deployment Models

### 1. Monolithic Mode
Run all services in a single process:
```bash
grpcapi run .\server\app.py -s .\server\grpcapi.config.json
python -m client.run
```

### 2. Microservices Mode  
Split services across multiple processes with separate databases:
```bash
python -m server.microservice
python -m client.run -p2 50052
```

**The beauty of grpcAPI**: The same codebase runs both ways with zero code changes - only configuration differs!

## 📁 Project Structure

```
example/guber/
├── client/                    # gRPC client implementations
│   ├── account/              # Account service client calls
│   ├── ride/                 # Ride service client calls  
│   └── run.py               # Main client runner
├── server/
│   ├── adapters/            # Infrastructure layer
│   │   └── repo/           # SQLAlchemy repository implementations
│   ├── application/         # Application layer
│   │   ├── usecase/        # Business use cases (account.py, ride.py)
│   │   ├── repo/           # Repository interfaces
│   │   └── gateway/        # External service gateways
│   ├── domain/             # Domain layer
│   │   ├── entity/         # Business entities and rules
│   │   └── vo/            # Value objects
│   ├── microservice/       # Microservice deployment configs
│   │   ├── __main__.py     # Microservice runner
│   │   ├── account.config.json
│   │   └── ride.config.json
│   ├── app.py             # Monolithic app configuration
│   └── grpcapi.config.json # Monolithic config
├── proto/                  # Protocol buffer definitions
├── lib/                   # Generated protobuf code
└── certs/                # TLS certificates
```

## 🔧 Key Features Demonstrated

### Dependency Injection
The application showcases grpcAPI's powerful dependency injection system:
```python
# Easy repository swapping
app.dependency_overrides[get_account_repo] = get_account_sqlalchemy_repo

# Mock external services  
app.dependency_overrides[get_payment_gateway] = mock_payment_gateway
```

### Service Filtering
**Monolithic**: All services run together
**Microservices**: Services filtered by package:
- Account service: `"include": ["account"]` on port 50051
- Ride service: `"include": ["ride"]` on port 50052

### TLS Security
Both deployment modes support TLS encryption with certificate management.

### Database per Service
In microservice mode, each service gets its own database:
- Account service: `testaccount.db`  
- Ride service: `testride.db`

## 🎯 Business Domain: Ride-Sharing

The application implements a complete ride-sharing flow:

1. **Account Management**
   - User signup (passengers & drivers)
   - Profile updates (email, car plates)
   - Account retrieval

2. **Ride Lifecycle**
   - Ride requests from passengers
   - Ride acceptance by drivers  
   - Real-time position tracking (streaming)
   - Ride completion and payment

3. **Real-time Features**
   - Bidirectional streaming for position updates
   - Server-side streaming for position monitoring

## 🚀 Running the Example

### Prerequisites
```bash
pip install grpcapi[example]
```

### Quick Start - Monolithic
```bash
cd example/guber
grpcapi run .\server\app.py -s .\server\grpcapi.config.json
# In another terminal:
python -m client.run
```

### Quick Start - Microservices
```bash
cd example/guber  
python -m server.microservice  # Starts both services
# In another terminal:
python -m client.run -p1 50051 -p2 50052
```

## 🔄 Flexibility Showcase

This example perfectly demonstrates grpcAPI's core philosophy: **"Write once, deploy anywhere"**

- **Same business logic** works in both monolithic and microservice architectures
- **Same protocol definitions** serve both deployment models
- **Configuration-driven architecture** - no code changes needed
- **Repository pattern** makes database implementations easily swappable
- **Gateway pattern** enables easy mocking and service substitution

The power lies in grpcAPI's ability to let you focus on business logic while providing the flexibility to evolve your architecture as needs change.