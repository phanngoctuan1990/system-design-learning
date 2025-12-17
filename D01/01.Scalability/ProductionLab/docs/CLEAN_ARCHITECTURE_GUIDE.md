# Clean Architecture Implementation Guide

## Tổng quan

Clean Architecture giúp tách biệt business logic khỏi technical details, làm cho code dễ test, maintain và thay đổi technology.

## Cấu trúc thư mục chuẩn

```
project/
├── core/                    # Business Logic (Framework Independent)
│   ├── domain/             # Entities & Value Objects
│   ├── interfaces/         # Ports (Abstractions)
│   └── services/          # Use Cases & Business Logic
├── infrastructure/         # Technical Implementation
│   ├── database/          # Database adapters
│   ├── web/              # Web framework adapters
│   ├── cache/            # Cache adapters
│   ├── messaging/        # Message queue adapters
│   └── deployment/       # Docker, K8s configs
├── tests/
│   ├── unit/             # Core logic tests
│   └── integration/      # Full system tests
└── main.py               # Composition Root
```

## Bước triển khai chi tiết

### Phase 1: Core Domain (Tuần 1)

#### 1.1 Tạo Domain Models
```python
# core/domain/user.py
@dataclass
class User:
    id: str
    email: str
    name: str
    
    def change_email(self, new_email: str) -> None:
        if not self._is_valid_email(new_email):
            raise ValueError("Invalid email")
        self.email = new_email
    
    def _is_valid_email(self, email: str) -> bool:
        return "@" in email  # Simplified validation
```

#### 1.2 Định nghĩa Interfaces (Ports)
```python
# core/interfaces/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..domain.user import User

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        pass
```

#### 1.3 Implement Use Cases
```python
# core/services/user_service.py
from ..domain.user import User
from ..interfaces.user_repository import UserRepository

class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo
    
    def register_user(self, email: str, name: str) -> User:
        # Business logic
        existing = self._user_repo.find_by_email(email)
        if existing:
            raise ValueError("Email already exists")
        
        user = User(id=self._generate_id(), email=email, name=name)
        self._user_repo.save(user)
        return user
    
    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
```

#### 1.4 Viết Unit Tests
```python
# tests/unit/test_user_service.py
import unittest
from unittest.mock import Mock
from core.services.user_service import UserService
from core.domain.user import User

class TestUserService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = Mock()
        self.user_service = UserService(self.mock_repo)
    
    def test_register_new_user(self):
        self.mock_repo.find_by_email.return_value = None
        
        user = self.user_service.register_user("test@example.com", "Test User")
        
        self.assertEqual(user.email, "test@example.com")
        self.mock_repo.save.assert_called_once()
```

### Phase 2: Infrastructure Adapters (Tuần 2)

#### 2.1 Database Adapter
```python
# infrastructure/database/postgres_user_repository.py
import psycopg2
from core.interfaces.user_repository import UserRepository
from core.domain.user import User

class PostgresUserRepository(UserRepository):
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    def save(self, user: User) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (id, email, name) VALUES (%s, %s, %s)",
            (user.id, user.email, user.name)
        )
        self.conn.commit()
    
    def find_by_email(self, email: str) -> Optional[User]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, email, name FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        if row:
            return User(id=row[0], email=row[1], name=row[2])
        return None
```

#### 2.2 Web Adapter
```python
# infrastructure/web/fastapi_adapter.py
from fastapi import FastAPI, HTTPException
from core.services.user_service import UserService

class FastAPIAdapter:
    def __init__(self, user_service: UserService):
        self.app = FastAPI()
        self.user_service = user_service
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/users")
        async def create_user(email: str, name: str):
            try:
                user = self.user_service.register_user(email, name)
                return {"id": user.id, "email": user.email, "name": user.name}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
```

### Phase 3: Composition Root (Tuần 3)

#### 3.1 Dependency Injection
```python
# main.py
import os
from core.services.user_service import UserService
from infrastructure.database.postgres_user_repository import PostgresUserRepository
from infrastructure.web.fastapi_adapter import FastAPIAdapter

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/mydb")

# Dependency Injection
def create_app():
    # Infrastructure
    user_repo = PostgresUserRepository(DATABASE_URL)
    
    # Core Services
    user_service = UserService(user_repo)
    
    # Web Adapter
    web_adapter = FastAPIAdapter(user_service)
    
    return web_adapter.app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Phase 4: Deployment (Tuần 4)

#### 4.1 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

#### 4.2 Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/mydb
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Checklist triển khai

### ✅ Phase 1: Core (Tuần 1)
- [ ] Tạo domain models với business rules
- [ ] Định nghĩa interfaces (ports)
- [ ] Implement use cases/services
- [ ] Viết unit tests cho core logic
- [ ] Đảm bảo core không depend external libraries

### ✅ Phase 2: Infrastructure (Tuần 2)
- [ ] Implement database adapters
- [ ] Implement web framework adapters
- [ ] Implement cache/messaging adapters
- [ ] Viết integration tests

### ✅ Phase 3: Integration (Tuần 3)
- [ ] Tạo composition root
- [ ] Setup dependency injection
- [ ] Configuration management
- [ ] Error handling

### ✅ Phase 4: Deployment (Tuần 4)
- [ ] Containerization (Docker)
- [ ] Orchestration (Docker Compose/K8s)
- [ ] CI/CD pipeline
- [ ] Monitoring & logging

## Patterns thường dùng

### Repository Pattern
```python
class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None: pass
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[User]: pass
```

### Factory Pattern
```python
class UserFactory:
    @staticmethod
    def create_user(email: str, name: str) -> User:
        return User(
            id=str(uuid.uuid4()),
            email=email.lower(),
            name=name.strip()
        )
```

### Command Pattern
```python
@dataclass
class CreateUserCommand:
    email: str
    name: str

class CreateUserHandler:
    def handle(self, command: CreateUserCommand) -> User:
        # Implementation
        pass
```

## Best Practices

### 1. **Dependency Direction**
- Core không depend vào Infrastructure
- Infrastructure depend vào Core
- Sử dụng Dependency Inversion

### 2. **Testing Strategy**
- Unit tests cho Core (fast, isolated)
- Integration tests cho Adapters
- E2E tests cho full system

### 3. **Error Handling**
- Domain exceptions trong Core
- Technical exceptions trong Infrastructure
- Convert exceptions ở boundaries

### 4. **Configuration**
- Environment variables
- Configuration objects
- Validation at startup

## Migration từ Monolith

### Bước 1: Identify Boundaries
- Tìm business domains
- Tách data models
- Identify dependencies

### Bước 2: Extract Core
- Move business logic vào Core
- Tạo interfaces cho external dependencies
- Viết tests

### Bước 3: Create Adapters
- Implement adapters từng bước
- Maintain backward compatibility
- Gradual migration

### Bước 4: Refactor
- Remove old code
- Optimize performance
- Documentation

## Ví dụ áp dụng cho các domain

### E-commerce
```
core/
├── domain/
│   ├── product.py
│   ├── order.py
│   └── customer.py
├── interfaces/
│   ├── product_repository.py
│   ├── order_repository.py
│   └── payment_gateway.py
└── services/
    ├── catalog_service.py
    ├── order_service.py
    └── payment_service.py
```

### Blog System
```
core/
├── domain/
│   ├── post.py
│   ├── author.py
│   └── comment.py
├── interfaces/
│   ├── post_repository.py
│   └── notification_service.py
└── services/
    ├── blog_service.py
    └── comment_service.py
```

## Tools & Libraries

### Python
- **Web**: FastAPI, Flask, Django
- **Database**: SQLAlchemy, Tortoise ORM
- **Testing**: pytest, unittest
- **DI**: dependency-injector, punq

### Node.js
- **Web**: Express, NestJS, Fastify
- **Database**: TypeORM, Prisma
- **Testing**: Jest, Mocha
- **DI**: InversifyJS, awilix

### Java
- **Web**: Spring Boot, Quarkus
- **Database**: JPA, MyBatis
- **Testing**: JUnit, Mockito
- **DI**: Spring, Guice

## Kết luận

Clean Architecture giúp:
- **Testability**: Easy unit testing
- **Flexibility**: Easy technology changes
- **Maintainability**: Clear separation of concerns
- **Scalability**: Independent deployment of layers

**Thời gian triển khai**: 4 tuần cho dự án mới, 8-12 tuần cho migration từ monolith.
