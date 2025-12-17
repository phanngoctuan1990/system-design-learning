# Clean Architecture Templates

## Template cho các loại dự án

### 1. REST API Template

#### Domain Model
```python
# core/domain/entity.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Entity:
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def mark_updated(self):
        self.updated_at = datetime.utcnow()
```

#### Repository Interface
```python
# core/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class Repository(ABC):
    @abstractmethod
    def save(self, entity: Any) -> Any:
        pass
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def find_all(self, filters: Dict = None) -> List[Any]:
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        pass
```

#### Service Template
```python
# core/services/base_service.py
from typing import TypeVar, Generic, Optional, List, Dict
from ..interfaces.repository import Repository

T = TypeVar('T')

class BaseService(Generic[T]):
    def __init__(self, repository: Repository):
        self._repository = repository
    
    def create(self, data: Dict) -> T:
        entity = self._create_entity(data)
        return self._repository.save(entity)
    
    def get_by_id(self, id: str) -> Optional[T]:
        return self._repository.find_by_id(id)
    
    def get_all(self, filters: Dict = None) -> List[T]:
        return self._repository.find_all(filters)
    
    def update(self, id: str, data: Dict) -> Optional[T]:
        entity = self._repository.find_by_id(id)
        if entity:
            self._update_entity(entity, data)
            return self._repository.save(entity)
        return None
    
    def delete(self, id: str) -> bool:
        return self._repository.delete(id)
    
    def _create_entity(self, data: Dict) -> T:
        raise NotImplementedError
    
    def _update_entity(self, entity: T, data: Dict) -> None:
        raise NotImplementedError
```

### 2. CRUD Application Template

#### Project Structure
```
project/
├── core/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── base_entity.py
│   │   └── {entity_name}.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   └── {entity_name}_repository.py
│   └── services/
│       ├── __init__.py
│       ├── base_service.py
│       └── {entity_name}_service.py
├── infrastructure/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   └── {entity_name}_repository.py
│   ├── web/
│   │   ├── __init__.py
│   │   ├── base_controller.py
│   │   └── {entity_name}_controller.py
│   └── deployment/
│       ├── Dockerfile
│       └── docker-compose.yml
├── tests/
├── main.py
└── requirements.txt
```

#### FastAPI Controller Template
```python
# infrastructure/web/base_controller.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

class BaseController:
    def __init__(self, service, router_prefix: str):
        self.service = service
        self.router = APIRouter(prefix=router_prefix)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.post("/", response_model=Dict)
        async def create(self, data: BaseModel):
            try:
                result = self.service.create(data.dict())
                return self._to_dict(result)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.router.get("/{id}", response_model=Dict)
        async def get_by_id(self, id: str):
            result = self.service.get_by_id(id)
            if not result:
                raise HTTPException(status_code=404, detail="Not found")
            return self._to_dict(result)
        
        @self.router.get("/", response_model=List[Dict])
        async def get_all(self):
            results = self.service.get_all()
            return [self._to_dict(r) for r in results]
        
        @self.router.put("/{id}", response_model=Dict)
        async def update(self, id: str, data: BaseModel):
            result = self.service.update(id, data.dict())
            if not result:
                raise HTTPException(status_code=404, detail="Not found")
            return self._to_dict(result)
        
        @self.router.delete("/{id}")
        async def delete(self, id: str):
            success = self.service.delete(id)
            if not success:
                raise HTTPException(status_code=404, detail="Not found")
            return {"message": "Deleted successfully"}
    
    def _to_dict(self, entity) -> Dict:
        if hasattr(entity, '__dict__'):
            return entity.__dict__
        return entity
```

### 3. Microservice Template

#### Service Discovery Interface
```python
# core/interfaces/service_discovery.py
from abc import ABC, abstractmethod
from typing import List, Optional

@dataclass
class ServiceInstance:
    name: str
    host: str
    port: int
    health_check_url: str

class ServiceDiscovery(ABC):
    @abstractmethod
    def register(self, instance: ServiceInstance) -> None:
        pass
    
    @abstractmethod
    def discover(self, service_name: str) -> List[ServiceInstance]:
        pass
    
    @abstractmethod
    def health_check(self, instance: ServiceInstance) -> bool:
        pass
```

#### Message Queue Interface
```python
# core/interfaces/message_queue.py
from abc import ABC, abstractmethod
from typing import Callable, Any

class MessageQueue(ABC):
    @abstractmethod
    def publish(self, topic: str, message: Any) -> None:
        pass
    
    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        pass
    
    @abstractmethod
    def unsubscribe(self, topic: str) -> None:
        pass
```

### 4. Event-Driven Template

#### Domain Events
```python
# core/domain/events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

@dataclass
class DomainEvent:
    event_type: str
    aggregate_id: str
    data: Dict[str, Any]
    occurred_at: datetime
    version: int = 1

class EventStore:
    def __init__(self):
        self._events = []
    
    def append(self, event: DomainEvent) -> None:
        self._events.append(event)
    
    def get_events(self, aggregate_id: str) -> List[DomainEvent]:
        return [e for e in self._events if e.aggregate_id == aggregate_id]
```

#### Event Handler
```python
# core/services/event_handler.py
from typing import Dict, Callable, List
from ..domain.events import DomainEvent

class EventHandler:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def register(self, event_type: str, handler: Callable[[DomainEvent], None]):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def handle(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error, don't fail other handlers
                print(f"Handler failed: {e}")
```

### 5. Testing Templates

#### Unit Test Template
```python
# tests/unit/test_service_template.py
import unittest
from unittest.mock import Mock, patch
from core.services.{service_name} import {ServiceName}

class Test{ServiceName}(unittest.TestCase):
    def setUp(self):
        self.mock_repository = Mock()
        self.service = {ServiceName}(self.mock_repository)
    
    def test_create_success(self):
        # Arrange
        data = {"name": "test"}
        expected_entity = Mock()
        self.mock_repository.save.return_value = expected_entity
        
        # Act
        result = self.service.create(data)
        
        # Assert
        self.assertEqual(result, expected_entity)
        self.mock_repository.save.assert_called_once()
    
    def test_create_validation_error(self):
        # Arrange
        invalid_data = {}
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.service.create(invalid_data)
    
    def tearDown(self):
        pass
```

#### Integration Test Template
```python
# tests/integration/test_repository_template.py
import unittest
from infrastructure.database.{repository_name} import {RepositoryName}
from core.domain.{entity_name} import {EntityName}

class Test{RepositoryName}Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup test database
        cls.db_connection = create_test_db_connection()
        cls.repository = {RepositoryName}(cls.db_connection)
    
    def setUp(self):
        # Clean database before each test
        self.clean_database()
    
    def test_save_and_find(self):
        # Arrange
        entity = {EntityName}(name="test")
        
        # Act
        saved_entity = self.repository.save(entity)
        found_entity = self.repository.find_by_id(saved_entity.id)
        
        # Assert
        self.assertIsNotNone(found_entity)
        self.assertEqual(found_entity.name, "test")
    
    def clean_database(self):
        # Implementation to clean test database
        pass
    
    @classmethod
    def tearDownClass(cls):
        # Cleanup test database
        cls.db_connection.close()
```

### 6. Configuration Templates

#### Environment Configuration
```python
# config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass
class AppConfig:
    debug: bool
    host: str
    port: int
    database: DatabaseConfig
    redis_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '8000')),
            database=DatabaseConfig(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
                name=os.getenv('DB_NAME', 'mydb'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'password')
            ),
            redis_url=os.getenv('REDIS_URL')
        )
```

### 7. Makefile Template

```makefile
# Makefile
.PHONY: install test lint format run docker-build docker-run clean

# Development
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	python -m pytest tests/ -v --cov=core --cov=infrastructure

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

lint:
	flake8 core/ infrastructure/ tests/
	mypy core/ infrastructure/

format:
	black core/ infrastructure/ tests/
	isort core/ infrastructure/ tests/

run:
	python main.py

# Docker
docker-build:
	docker build -t myapp .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Database
db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	docker system prune -f
```

### 8. Requirements Template

```txt
# requirements.txt
# Web Framework
fastapi==0.104.1
uvicorn==0.24.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Cache
redis==5.0.1

# Validation
pydantic==2.5.0

# HTTP Client
httpx==0.25.2

# Configuration
python-dotenv==1.0.0

# Logging
structlog==23.2.0
```

```txt
# requirements-dev.txt
# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1

# Code Quality
black==23.11.0
flake8==6.1.0
isort==5.12.0
mypy==1.7.1

# Development
pre-commit==3.6.0
```

Các templates này cung cấp foundation để bắt đầu nhanh với Clean Architecture cho bất kỳ dự án nào!
