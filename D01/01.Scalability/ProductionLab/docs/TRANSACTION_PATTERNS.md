# Transaction Patterns in Hexagonal Architecture

## Tổng quan

Trong Hexagonal Architecture, việc xử lý transaction cần đảm bảo tính nhất quán dữ liệu mà không vi phạm nguyên tắc tách biệt giữa Core và Infrastructure.

## Pattern 1: Database Transaction (Single Database)

### Khi nào sử dụng
- Tất cả operations trong cùng một database
- ACID transactions được hỗ trợ
- Đơn giản và hiệu quả nhất

### Implementation

#### Core Layer
```python
# core/interfaces/transaction_manager.py
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator

class TransactionManager(ABC):
    @abstractmethod
    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Context manager for database transactions"""
        pass

# core/domain/user.py
@dataclass
class AuthUser:
    id: Optional[str] = None
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None

@dataclass
class UserProfile:
    id: Optional[str] = None
    auth_user_id: str = ""
    name: str = ""
    phone: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class User:
    auth_user: AuthUser
    profile: UserProfile

# core/interfaces/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    def save_auth_user(self, auth_user: AuthUser) -> AuthUser:
        pass
    
    @abstractmethod
    def save_user_profile(self, profile: UserProfile) -> UserProfile:
        pass
    
    @abstractmethod
    def find_auth_user_by_email(self, email: str) -> Optional[AuthUser]:
        pass

# core/services/user_service.py
class UserService:
    def __init__(self, user_repo: UserRepository, tx_manager: TransactionManager):
        self._user_repo = user_repo
        self._tx_manager = tx_manager
    
    def register_user(self, email: str, name: str, password: str) -> User:
        # Validate business rules
        existing = self._user_repo.find_auth_user_by_email(email)
        if existing:
            raise ValueError(f"User with email {email} already exists")
        
        with self._tx_manager.transaction():
            # Step 1: Create auth user
            auth_user = AuthUser(
                email=email,
                password_hash=self._hash_password(password),
                created_at=datetime.utcnow()
            )
            saved_auth = self._user_repo.save_auth_user(auth_user)
            
            # Step 2: Create user profile
            # Nếu step này fail, auth_user sẽ được rollback tự động
            profile = UserProfile(
                auth_user_id=saved_auth.id,
                name=name,
                created_at=datetime.utcnow()
            )
            saved_profile = self._user_repo.save_user_profile(profile)
            
            return User(auth_user=saved_auth, profile=saved_profile)
    
    def _hash_password(self, password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
```

#### Infrastructure Layer
```python
# infrastructure/database/postgres_transaction_manager.py
from sqlalchemy.orm import sessionmaker
from core.interfaces.transaction_manager import TransactionManager

class PostgresTransactionManager(TransactionManager):
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
    
    @contextmanager
    def transaction(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# infrastructure/database/postgres_user_repository.py
from sqlalchemy.orm import Session
from core.interfaces.user_repository import UserRepository
from core.domain.user import AuthUser, UserProfile

class PostgresUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def save_auth_user(self, auth_user: AuthUser) -> AuthUser:
        db_auth_user = AuthUserModel(
            email=auth_user.email,
            password_hash=auth_user.password_hash,
            created_at=auth_user.created_at
        )
        self._session.add(db_auth_user)
        self._session.flush()  # Get ID but don't commit yet
        
        return AuthUser(
            id=str(db_auth_user.id),
            email=db_auth_user.email,
            password_hash=db_auth_user.password_hash,
            created_at=db_auth_user.created_at
        )
    
    def save_user_profile(self, profile: UserProfile) -> UserProfile:
        db_profile = UserProfileModel(
            auth_user_id=int(profile.auth_user_id),
            name=profile.name,
            phone=profile.phone,
            created_at=profile.created_at
        )
        self._session.add(db_profile)
        self._session.flush()
        
        return UserProfile(
            id=str(db_profile.id),
            auth_user_id=profile.auth_user_id,
            name=db_profile.name,
            phone=db_profile.phone,
            created_at=db_profile.created_at
        )
    
    def find_auth_user_by_email(self, email: str) -> Optional[AuthUser]:
        db_user = self._session.query(AuthUserModel).filter_by(email=email).first()
        if db_user:
            return AuthUser(
                id=str(db_user.id),
                email=db_user.email,
                password_hash=db_user.password_hash,
                created_at=db_user.created_at
            )
        return None

# infrastructure/database/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuthUserModel(Base):
    __tablename__ = 'auth_users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)

class UserProfileModel(Base):
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    auth_user_id = Column(Integer, ForeignKey('auth_users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False)
```

## Pattern 2: Unit of Work Pattern

### Khi nào sử dụng
- Cần track nhiều repositories trong cùng transaction
- Complex business operations với nhiều entities
- Muốn lazy loading và batch operations

### Implementation

#### Core Layer
```python
# core/interfaces/unit_of_work.py
from abc import ABC, abstractmethod
from typing import Protocol

class AuthUserRepository(Protocol):
    def save(self, auth_user: AuthUser) -> AuthUser: ...
    def find_by_email(self, email: str) -> Optional[AuthUser]: ...

class UserProfileRepository(Protocol):
    def save(self, profile: UserProfile) -> UserProfile: ...
    def find_by_auth_user_id(self, auth_user_id: str) -> Optional[UserProfile]: ...

class UnitOfWork(ABC):
    @abstractmethod
    def __enter__(self):
        return self
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @abstractmethod
    def commit(self):
        pass
    
    @abstractmethod
    def rollback(self):
        pass
    
    @property
    @abstractmethod
    def auth_users(self) -> AuthUserRepository:
        pass
    
    @property
    @abstractmethod
    def user_profiles(self) -> UserProfileRepository:
        pass

# core/services/user_service.py
class UserService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
    
    def register_user(self, email: str, name: str, password: str) -> User:
        with self._uow:
            # Check if user exists
            existing = self._uow.auth_users.find_by_email(email)
            if existing:
                raise ValueError(f"User with email {email} already exists")
            
            # Create auth user
            auth_user = AuthUser(
                email=email,
                password_hash=self._hash_password(password),
                created_at=datetime.utcnow()
            )
            saved_auth = self._uow.auth_users.save(auth_user)
            
            # Create user profile
            profile = UserProfile(
                auth_user_id=saved_auth.id,
                name=name,
                created_at=datetime.utcnow()
            )
            saved_profile = self._uow.user_profiles.save(profile)
            
            # Commit happens automatically when exiting context
            return User(auth_user=saved_auth, profile=saved_profile)
```

#### Infrastructure Layer
```python
# infrastructure/database/postgres_unit_of_work.py
from sqlalchemy.orm import sessionmaker
from core.interfaces.unit_of_work import UnitOfWork

class PostgresUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._session = None
    
    def __enter__(self):
        self._session = self._session_factory()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self._session.close()
    
    def commit(self):
        self._session.commit()
    
    def rollback(self):
        self._session.rollback()
    
    @property
    def auth_users(self):
        return PostgresAuthUserRepository(self._session)
    
    @property
    def user_profiles(self):
        return PostgresUserProfileRepository(self._session)

class PostgresAuthUserRepository:
    def __init__(self, session):
        self._session = session
    
    def save(self, auth_user: AuthUser) -> AuthUser:
        # Implementation similar to previous example
        pass
    
    def find_by_email(self, email: str) -> Optional[AuthUser]:
        # Implementation similar to previous example
        pass
```

## Pattern 3: Saga Pattern (Distributed Transactions)

### Khi nào sử dụng
- Multiple databases/services
- Long-running processes
- Need compensation logic
- Microservices architecture

### Implementation

#### Core Layer
```python
# core/domain/saga.py
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class SagaStepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    name: str
    status: SagaStepStatus
    data: dict
    error: Optional[str] = None

class SagaState:
    def __init__(self, saga_id: str):
        self.saga_id = saga_id
        self.steps: List[SagaStep] = []
        self.current_step = 0
    
    def add_step(self, step: SagaStep):
        self.steps.append(step)
    
    def mark_step_completed(self, step_name: str, data: dict = None):
        step = self._find_step(step_name)
        if step:
            step.status = SagaStepStatus.COMPLETED
            if data:
                step.data.update(data)
    
    def mark_step_failed(self, step_name: str, error: str):
        step = self._find_step(step_name)
        if step:
            step.status = SagaStepStatus.FAILED
            step.error = error
    
    def _find_step(self, step_name: str) -> Optional[SagaStep]:
        return next((s for s in self.steps if s.name == step_name), None)

# core/services/user_registration_saga.py
class UserRegistrationSaga:
    def __init__(self, 
                 auth_service: AuthService, 
                 profile_service: ProfileService,
                 email_service: EmailService,
                 saga_store: SagaStore):
        self._auth_service = auth_service
        self._profile_service = profile_service
        self._email_service = email_service
        self._saga_store = saga_store
    
    async def execute(self, email: str, name: str, password: str) -> User:
        saga_id = str(uuid.uuid4())
        saga_state = SagaState(saga_id)
        
        # Define saga steps
        saga_state.add_step(SagaStep("create_auth_user", SagaStepStatus.PENDING, {}))
        saga_state.add_step(SagaStep("create_user_profile", SagaStepStatus.PENDING, {}))
        saga_state.add_step(SagaStep("send_welcome_email", SagaStepStatus.PENDING, {}))
        
        try:
            # Step 1: Create auth user
            auth_user = await self._create_auth_user(saga_state, email, password)
            
            # Step 2: Create user profile
            profile = await self._create_user_profile(saga_state, auth_user.id, name)
            
            # Step 3: Send welcome email
            await self._send_welcome_email(saga_state, email)
            
            await self._saga_store.save(saga_state)
            return User(auth_user=auth_user, profile=profile)
            
        except Exception as e:
            await self._compensate(saga_state)
            raise e
    
    async def _create_auth_user(self, saga_state: SagaState, email: str, password: str) -> AuthUser:
        try:
            auth_user = await self._auth_service.create_user(email, password)
            saga_state.mark_step_completed("create_auth_user", {"auth_user_id": auth_user.id})
            return auth_user
        except Exception as e:
            saga_state.mark_step_failed("create_auth_user", str(e))
            raise
    
    async def _create_user_profile(self, saga_state: SagaState, auth_user_id: str, name: str) -> UserProfile:
        try:
            profile = await self._profile_service.create_profile(auth_user_id, name)
            saga_state.mark_step_completed("create_user_profile", {"profile_id": profile.id})
            return profile
        except Exception as e:
            saga_state.mark_step_failed("create_user_profile", str(e))
            raise
    
    async def _send_welcome_email(self, saga_state: SagaState, email: str):
        try:
            await self._email_service.send_welcome_email(email)
            saga_state.mark_step_completed("send_welcome_email")
        except Exception as e:
            saga_state.mark_step_failed("send_welcome_email", str(e))
            raise
    
    async def _compensate(self, saga_state: SagaState):
        """Execute compensation in reverse order"""
        completed_steps = [s for s in saga_state.steps if s.status == SagaStepStatus.COMPLETED]
        
        for step in reversed(completed_steps):
            try:
                if step.name == "send_welcome_email":
                    # Email already sent, cannot compensate
                    pass
                elif step.name == "create_user_profile":
                    profile_id = step.data.get("profile_id")
                    await self._profile_service.delete_profile(profile_id)
                elif step.name == "create_auth_user":
                    auth_user_id = step.data.get("auth_user_id")
                    await self._auth_service.delete_user(auth_user_id)
                
                step.status = SagaStepStatus.COMPENSATED
                
            except Exception as e:
                logger.error(f"Compensation failed for step {step.name}: {e}")
        
        await self._saga_store.save(saga_state)
```

## Pattern 4: Event Sourcing + CQRS

### Khi nào sử dụng
- Need audit trail
- Complex business workflows
- High scalability requirements
- Eventual consistency acceptable

### Implementation

#### Core Layer
```python
# core/domain/events.py
@dataclass
class DomainEvent:
    event_id: str
    aggregate_id: str
    event_type: str
    data: dict
    timestamp: datetime
    version: int

@dataclass
class UserRegistrationStarted(DomainEvent):
    def __init__(self, user_id: str, email: str, name: str):
        super().__init__(
            event_id=str(uuid.uuid4()),
            aggregate_id=user_id,
            event_type="UserRegistrationStarted",
            data={"email": email, "name": name},
            timestamp=datetime.utcnow(),
            version=1
        )

@dataclass
class AuthUserCreated(DomainEvent):
    def __init__(self, user_id: str, auth_user_id: str):
        super().__init__(
            event_id=str(uuid.uuid4()),
            aggregate_id=user_id,
            event_type="AuthUserCreated",
            data={"auth_user_id": auth_user_id},
            timestamp=datetime.utcnow(),
            version=1
        )

# core/services/user_registration_process_manager.py
class UserRegistrationProcessManager:
    def __init__(self, 
                 event_store: EventStore,
                 command_bus: CommandBus,
                 auth_service: AuthService,
                 profile_service: ProfileService):
        self._event_store = event_store
        self._command_bus = command_bus
        self._auth_service = auth_service
        self._profile_service = profile_service
    
    async def start_registration(self, email: str, name: str, password: str) -> str:
        user_id = str(uuid.uuid4())
        
        # Publish domain event
        event = UserRegistrationStarted(user_id, email, name)
        await self._event_store.append(event)
        
        # Start the process
        await self._handle_registration_started(event)
        
        return user_id
    
    async def _handle_registration_started(self, event: UserRegistrationStarted):
        try:
            # Create auth user
            auth_user = await self._auth_service.create_user(
                event.data["email"], 
                "password"  # Should be passed separately
            )
            
            # Publish success event
            success_event = AuthUserCreated(event.aggregate_id, auth_user.id)
            await self._event_store.append(success_event)
            
            # Continue to next step
            await self._handle_auth_user_created(success_event)
            
        except Exception as e:
            # Publish failure event
            failure_event = AuthUserCreationFailed(event.aggregate_id, str(e))
            await self._event_store.append(failure_event)
    
    async def _handle_auth_user_created(self, event: AuthUserCreated):
        # Get original registration data
        registration_events = await self._event_store.get_events(event.aggregate_id)
        registration_started = next(e for e in registration_events if e.event_type == "UserRegistrationStarted")
        
        try:
            # Create user profile
            profile = await self._profile_service.create_profile(
                event.data["auth_user_id"],
                registration_started.data["name"]
            )
            
            # Publish success event
            success_event = UserProfileCreated(event.aggregate_id, profile.id)
            await self._event_store.append(success_event)
            
        except Exception as e:
            # Compensate: Delete auth user
            await self._auth_service.delete_user(event.data["auth_user_id"])
            
            # Publish failure event
            failure_event = UserProfileCreationFailed(event.aggregate_id, str(e))
            await self._event_store.append(failure_event)
```

## Composition Root Examples

### Database Transaction
```python
# main.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.database.postgres_transaction_manager import PostgresTransactionManager
from infrastructure.database.postgres_user_repository import PostgresUserRepository
from core.services.user_service import UserService

def create_app():
    # Database setup
    engine = create_engine("postgresql://user:pass@localhost/db")
    session_factory = sessionmaker(bind=engine)
    
    # Transaction manager
    tx_manager = PostgresTransactionManager(session_factory)
    
    # Repository (will be injected with session from tx_manager)
    def create_user_service():
        session = session_factory()
        user_repo = PostgresUserRepository(session)
        return UserService(user_repo, tx_manager)
    
    return create_user_service
```

### Unit of Work
```python
# main.py
def create_app():
    engine = create_engine("postgresql://user:pass@localhost/db")
    session_factory = sessionmaker(bind=engine)
    
    # Unit of Work
    uow = PostgresUnitOfWork(session_factory)
    
    # Service
    user_service = UserService(uow)
    
    return user_service
```

## Testing Strategies

### Mock Transaction Manager
```python
# tests/unit/test_user_service.py
class MockTransactionManager(TransactionManager):
    @contextmanager
    def transaction(self):
        yield  # No actual transaction, just pass through

class TestUserService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = Mock()
        self.mock_tx_manager = MockTransactionManager()
        self.user_service = UserService(self.mock_repo, self.mock_tx_manager)
    
    def test_register_user_success(self):
        # Setup mocks
        self.mock_repo.find_auth_user_by_email.return_value = None
        self.mock_repo.save_auth_user.return_value = AuthUser(id="1", email="test@example.com")
        self.mock_repo.save_user_profile.return_value = UserProfile(id="1", name="Test User")
        
        # Execute
        result = self.user_service.register_user("test@example.com", "Test User", "password")
        
        # Verify
        self.assertIsNotNone(result)
        self.mock_repo.save_auth_user.assert_called_once()
        self.mock_repo.save_user_profile.assert_called_once()
```

### Integration Test with Real Transaction
```python
# tests/integration/test_user_service_integration.py
class TestUserServiceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine)
    
    def setUp(self):
        self.tx_manager = PostgresTransactionManager(self.session_factory)
        session = self.session_factory()
        self.user_repo = PostgresUserRepository(session)
        self.user_service = UserService(self.user_repo, self.tx_manager)
    
    def test_register_user_rollback_on_profile_failure(self):
        # Mock profile creation to fail
        with patch.object(self.user_repo, 'save_user_profile', side_effect=Exception("Profile error")):
            with self.assertRaises(Exception):
                self.user_service.register_user("test@example.com", "Test User", "password")
        
        # Verify auth user was rolled back
        session = self.session_factory()
        auth_user = session.query(AuthUserModel).filter_by(email="test@example.com").first()
        self.assertIsNone(auth_user)
```

## Best Practices

### 1. **Choose the Right Pattern**
- **Single Database**: Database Transaction
- **Multiple Services**: Saga Pattern
- **Complex Workflows**: Event Sourcing
- **Simple CRUD**: Unit of Work

### 2. **Error Handling**
```python
class TransactionError(Exception):
    """Base exception for transaction-related errors"""
    pass

class CompensationError(TransactionError):
    """Raised when compensation fails"""
    pass

class SagaTimeoutError(TransactionError):
    """Raised when saga times out"""
    pass
```

### 3. **Monitoring & Observability**
```python
# Add transaction metrics
transaction_duration = Histogram('transaction_duration_seconds', 'Transaction duration')
transaction_failures = Counter('transaction_failures_total', 'Transaction failures')

@contextmanager
def monitored_transaction(tx_manager):
    start_time = time.time()
    try:
        with tx_manager.transaction():
            yield
        transaction_duration.observe(time.time() - start_time)
    except Exception as e:
        transaction_failures.inc()
        raise
```

### 4. **Configuration**
```python
@dataclass
class TransactionConfig:
    timeout_seconds: int = 30
    retry_attempts: int = 3
    compensation_timeout: int = 60
    
    @classmethod
    def from_env(cls):
        return cls(
            timeout_seconds=int(os.getenv('TRANSACTION_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('TRANSACTION_RETRIES', '3')),
            compensation_timeout=int(os.getenv('COMPENSATION_TIMEOUT', '60'))
        )
```

## Kết luận

Việc lựa chọn transaction pattern phụ thuộc vào:

- **Complexity**: Database Transaction < Unit of Work < Saga < Event Sourcing
- **Consistency**: Strong (DB Transaction) → Eventual (Event Sourcing)
- **Scalability**: DB Transaction < Event Sourcing
- **Maintainability**: Unit of Work > Database Transaction > Saga > Event Sourcing

**Khuyến nghị**: Bắt đầu với Database Transaction, migrate sang pattern phức tạp hơn khi cần thiết.
