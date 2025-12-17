# Clean Architecture - Production Lab

## Directory Structure

```
ProductionLab/
├── core/                        # Core Business Logic (Framework Independent)
│   ├── domain/                  # Domain Models & Entities
│   │   └── models.py            # ServerInfo, SessionData, HealthStatus
│   ├── interfaces/              # Ports (Abstractions)
│   │   ├── cache_port.py        # Cache interface
│   │   └── web_port.py          # Web framework interface
│   └── services/                # Use Cases & Business Logic
│       └── app_service.py       # Main application service
├── infrastructure/              # External Concerns (Framework Specific)
│   ├── cache/                   # Cache Adapters
│   │   ├── redis_adapter.py     # Redis implementation
│   │   └── memory_adapter.py    # In-memory fallback
│   ├── web/                     # Web Framework Adapters
│   │   └── flask_adapter.py     # Flask implementation
│   └── deployment/              # Infrastructure as Code
│       ├── Dockerfile
│       └── docker-compose.yml
├── tests/                       # Unit Tests
│   └── unit/                    # Unit tests for core logic
├── docs/                        # Documentation
│   ├── CLEAN_ARCHITECTURE_GUIDE.md    # Implementation guide
│   ├── TEMPLATES.md                   # Code templates
│   ├── MIGRATION_GUIDE.md             # Migration strategies
│   └── TRANSACTION_PATTERNS.md        # Transaction handling
├── main.py                      # Composition Root (Dependency Injection)
├── requirements.txt             # Python dependencies
└── Makefile                     # Test runner commands
```

## Quick Start

### 1. Setup and Run Application
```bash
# Start the production environment
cd infrastructure/deployment
docker-compose up -d

# Check services health
docker-compose ps

# Test the application
curl http://localhost:81/health
```

### 2. Run Tests
```bash
# Install dependencies (for local testing)
pip install -r requirements.txt

# Run all tests
make test

# Run specific test suites
make test-core      # Core business logic
make test-models    # Domain models
make test-adapters  # Cache adapters
```

### 3. Development
```bash
# Run locally with memory cache
USE_REDIS=false python3 main.py

# Run locally with Redis
docker run -d -p 6379:6379 redis:6-alpine
USE_REDIS=true REDIS_HOST=localhost python3 main.py
```

## Documentation

### 📚 **Complete Implementation Guides**

- **[Clean Architecture Guide](docs/CLEAN_ARCHITECTURE_GUIDE.md)** - Step-by-step implementation (4 weeks)
- **[Code Templates](docs/TEMPLATES.md)** - Ready-to-use templates for REST API, CRUD, Microservices
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Migrate from Monolith to Clean Architecture
- **[Transaction Patterns](docs/TRANSACTION_PATTERNS.md)** - Handle transactions in Hexagonal Architecture

### 🎯 **Key Topics Covered**

- **Hexagonal Architecture** (Ports & Adapters)
- **Clean Architecture** layers and principles
- **Transaction Management** (Database, Unit of Work, Saga, Event Sourcing)
- **Testing Strategies** (Unit, Integration, Mocking)
- **Migration Patterns** (Strangler Fig, Parallel Run)
- **Deployment** (Docker, Kubernetes, CI/CD)

## Architecture Benefits

### 1. **Technology Independence**
- Core business logic has no external dependencies
- Easy to switch from Redis to Memcached/DynamoDB
- Easy to switch from Flask to FastAPI/Node.js

### 2. **Testability**
- Core logic tested without external dependencies
- Mock adapters for unit testing
- 14 unit tests covering all core functionality

### 3. **Maintainability**
- Clear separation of concerns
- Changes in infrastructure don't affect core logic
- Single responsibility principle

## Migration Examples

### Switch to Memcached
```python
# Create new adapter
class MemcachedAdapter(CachePort):
    # Implementation...

# Update main.py
cache = MemcachedAdapter(host=MEMCACHED_HOST)
```

### Switch to Node.js
1. Copy `core/` directory
2. Implement adapters in JavaScript
3. Create new composition root

### Switch to FastAPI
```python
# Create new adapter
class FastAPIAdapter(WebPort):
    # Implementation...

# Update main.py
web_adapter = FastAPIAdapter()
```

## Key Principles

1. **Dependency Inversion**: Core depends on abstractions, not concretions
2. **Ports & Adapters**: Clean interfaces between layers
3. **Composition Root**: Single place for dependency wiring
4. **Framework Independence**: Core logic works with any framework

## Transaction Handling

This project demonstrates multiple transaction patterns:

- **Database Transactions** - For single database operations
- **Unit of Work** - For complex multi-repository operations  
- **Saga Pattern** - For distributed transactions
- **Event Sourcing** - For audit trails and eventual consistency

See [Transaction Patterns](docs/TRANSACTION_PATTERNS.md) for detailed examples.
