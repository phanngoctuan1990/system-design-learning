# Migration Guide: From Monolith to Clean Architecture

## Tổng quan Migration Strategy

### Strangler Fig Pattern
Dần dần thay thế monolith bằng microservices mới, giữ hệ thống cũ chạy song song.

### Big Bang vs Incremental
- **Big Bang**: Rewrite toàn bộ (rủi ro cao)
- **Incremental**: Migrate từng phần (khuyến nghị)

## Phase 1: Assessment & Planning (Tuần 1-2)

### 1.1 Phân tích Monolith hiện tại

#### Inventory Code Base
```bash
# Phân tích dependencies
find . -name "*.py" | xargs grep -l "import" | head -20

# Đếm lines of code
find . -name "*.py" | xargs wc -l | sort -n

# Tìm circular dependencies
python -m pydeps --show-deps myapp/
```

#### Identify Business Domains
```python
# Tạo domain map
domains = {
    "user_management": ["user.py", "auth.py", "profile.py"],
    "product_catalog": ["product.py", "category.py", "inventory.py"],
    "order_processing": ["order.py", "payment.py", "shipping.py"],
    "reporting": ["analytics.py", "reports.py"]
}
```

#### Database Analysis
```sql
-- Phân tích table relationships
SELECT 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY';
```

### 1.2 Migration Plan

#### Priority Matrix
```
High Business Value + Low Complexity = Phase 1
High Business Value + High Complexity = Phase 2  
Low Business Value + Low Complexity = Phase 3
Low Business Value + High Complexity = Consider keeping
```

#### Timeline Template
```
Phase 1 (Month 1-2): User Management
Phase 2 (Month 3-4): Product Catalog  
Phase 3 (Month 5-6): Order Processing
Phase 4 (Month 7-8): Reporting & Analytics
```

## Phase 2: Setup Infrastructure (Tuần 3-4)

### 2.1 Tạo New Project Structure
```bash
mkdir new-architecture
cd new-architecture

# Tạo cấu trúc Clean Architecture
mkdir -p {core/{domain,interfaces,services},infrastructure/{database,web,cache},tests/{unit,integration}}

# Copy business logic từ monolith
cp ../monolith/models/user.py core/domain/
cp ../monolith/services/user_service.py core/services/
```

### 2.2 Database Migration Strategy

#### Shared Database (Phase 1)
```python
# Cả monolith và microservice dùng chung DB
# infrastructure/database/shared_db_repository.py
class SharedUserRepository(UserRepository):
    def __init__(self, connection_string: str):
        # Connect to existing monolith database
        self.engine = create_engine(connection_string)
```

#### Database per Service (Phase 2)
```python
# Tách database riêng cho từng service
# infrastructure/database/user_db_repository.py
class UserRepository(UserRepository):
    def __init__(self, connection_string: str):
        # Connect to dedicated user database
        self.engine = create_engine(connection_string)
```

### 2.3 API Gateway Setup
```yaml
# infrastructure/deployment/api-gateway.yml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: api-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: routing
spec:
  http:
  - match:
    - uri:
        prefix: /api/users
    route:
    - destination:
        host: user-service
  - match:
    - uri:
        prefix: /api
    route:
    - destination:
        host: monolith-service  # Fallback to monolith
```

## Phase 3: Incremental Migration (Tuần 5-12)

### 3.1 Extract First Domain (User Management)

#### Step 1: Create Core Domain
```python
# core/domain/user.py - Extract từ monolith
@dataclass
class User:
    id: str
    email: str
    name: str
    created_at: datetime
    
    # Business rules từ monolith
    def change_email(self, new_email: str):
        if not self._is_valid_email(new_email):
            raise ValueError("Invalid email format")
        self.email = new_email
    
    def _is_valid_email(self, email: str) -> bool:
        # Copy validation logic từ monolith
        return "@" in email and "." in email.split("@")[1]
```

#### Step 2: Create Interfaces
```python
# core/interfaces/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        pass
```

#### Step 3: Implement Service
```python
# core/services/user_service.py - Migrate business logic
class UserService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        self._user_repo = user_repo
        self._email_service = email_service
    
    def register_user(self, email: str, name: str) -> User:
        # Copy business logic từ monolith
        existing = self._user_repo.find_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"User with email {email} already exists")
        
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            created_at=datetime.utcnow()
        )
        
        saved_user = self._user_repo.save(user)
        
        # Send welcome email (business rule từ monolith)
        self._email_service.send_welcome_email(saved_user)
        
        return saved_user
```

### 3.2 Parallel Run Strategy

#### Dual Write Pattern
```python
# Ghi vào cả monolith và microservice
class DualWriteUserRepository(UserRepository):
    def __init__(self, monolith_repo: MonolithUserRepo, new_repo: NewUserRepo):
        self.monolith_repo = monolith_repo
        self.new_repo = new_repo
    
    def save(self, user: User) -> User:
        # Write to monolith first (source of truth)
        monolith_user = self.monolith_repo.save(user)
        
        try:
            # Write to new service
            self.new_repo.save(user)
        except Exception as e:
            # Log error but don't fail
            logger.error(f"Failed to write to new service: {e}")
        
        return monolith_user
```

#### Feature Toggle
```python
# config.py
@dataclass
class FeatureFlags:
    use_new_user_service: bool = False
    use_new_product_service: bool = False
    
    @classmethod
    def from_env(cls):
        return cls(
            use_new_user_service=os.getenv('USE_NEW_USER_SERVICE', 'false').lower() == 'true',
            use_new_product_service=os.getenv('USE_NEW_PRODUCT_SERVICE', 'false').lower() == 'true'
        )

# main.py
def create_user_service():
    flags = FeatureFlags.from_env()
    
    if flags.use_new_user_service:
        return NewUserService()
    else:
        return MonolithUserService()
```

### 3.3 Data Migration

#### Batch Migration Script
```python
# scripts/migrate_users.py
import asyncio
from typing import List
from monolith.models import MonolithUser
from core.domain.user import User
from infrastructure.database.user_repository import UserRepository

class UserMigrator:
    def __init__(self, monolith_db, new_db):
        self.monolith_db = monolith_db
        self.new_repo = UserRepository(new_db)
    
    async def migrate_batch(self, batch_size: int = 1000):
        offset = 0
        
        while True:
            # Get batch from monolith
            monolith_users = self.monolith_db.query(MonolithUser)\
                .offset(offset)\
                .limit(batch_size)\
                .all()
            
            if not monolith_users:
                break
            
            # Convert to new domain model
            new_users = [self._convert_user(mu) for mu in monolith_users]
            
            # Batch insert to new service
            await self._batch_insert(new_users)
            
            offset += batch_size
            print(f"Migrated {offset} users")
    
    def _convert_user(self, monolith_user: MonolithUser) -> User:
        return User(
            id=str(monolith_user.id),
            email=monolith_user.email,
            name=monolith_user.full_name,
            created_at=monolith_user.created_date
        )
    
    async def _batch_insert(self, users: List[User]):
        for user in users:
            try:
                self.new_repo.save(user)
            except Exception as e:
                print(f"Failed to migrate user {user.id}: {e}")

# Run migration
if __name__ == "__main__":
    migrator = UserMigrator(monolith_db, new_db)
    asyncio.run(migrator.migrate_batch())
```

### 3.4 Testing Strategy

#### Shadow Testing
```python
# Test new service với production traffic
class ShadowTestUserService:
    def __init__(self, primary_service, shadow_service):
        self.primary = primary_service
        self.shadow = shadow_service
    
    def register_user(self, email: str, name: str) -> User:
        # Primary service (production)
        result = self.primary.register_user(email, name)
        
        # Shadow service (testing)
        asyncio.create_task(self._shadow_test(email, name, result))
        
        return result
    
    async def _shadow_test(self, email: str, name: str, expected_result: User):
        try:
            shadow_result = self.shadow.register_user(email, name)
            
            # Compare results
            if shadow_result.email != expected_result.email:
                logger.warning("Shadow test mismatch: email")
            
        except Exception as e:
            logger.error(f"Shadow test failed: {e}")
```

## Phase 4: Cutover & Cleanup (Tuần 13-16)

### 4.1 Traffic Switching

#### Canary Deployment
```yaml
# k8s/canary-deployment.yml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: user-service
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 10    # 10% traffic to new service
      - pause: {duration: 1h}
      - setWeight: 50    # 50% traffic
      - pause: {duration: 30m}
      - setWeight: 100   # 100% traffic
  selector:
    matchLabels:
      app: user-service
  template:
    spec:
      containers:
      - name: user-service
        image: user-service:v2.0
```

#### Blue-Green Deployment
```bash
# Switch traffic từ monolith sang microservice
kubectl patch service user-service -p '{"spec":{"selector":{"version":"v2"}}}'

# Rollback nếu có vấn đề
kubectl patch service user-service -p '{"spec":{"selector":{"version":"v1"}}}'
```

### 4.2 Monitoring & Alerting

#### Health Checks
```python
# infrastructure/web/health_controller.py
class HealthController:
    def __init__(self, user_service: UserService, db_health: DatabaseHealth):
        self.user_service = user_service
        self.db_health = db_health
    
    async def health_check(self):
        checks = {
            "database": await self.db_health.check(),
            "user_service": await self._check_user_service(),
            "external_apis": await self._check_external_apis()
        }
        
        all_healthy = all(checks.values())
        status_code = 200 if all_healthy else 503
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }, status_code
```

#### Metrics Collection
```python
# infrastructure/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
user_registrations = Counter('user_registrations_total', 'Total user registrations')
user_login_duration = Histogram('user_login_duration_seconds', 'User login duration')
active_users = Gauge('active_users', 'Number of active users')

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Record metrics
            duration = time.time() - start_time
            user_login_duration.observe(duration)
        
        await self.app(scope, receive, send)
```

### 4.3 Cleanup Monolith

#### Remove Dead Code
```python
# scripts/cleanup_monolith.py
import ast
import os

class DeadCodeFinder(ast.NodeVisitor):
    def __init__(self):
        self.functions = set()
        self.called_functions = set()
    
    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        self.generic_visit(node)

def find_dead_code(directory):
    finder = DeadCodeFinder()
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    tree = ast.parse(f.read())
                    finder.visit(tree)
    
    dead_functions = finder.functions - finder.called_functions
    return dead_functions
```

## Common Pitfalls & Solutions

### 1. **Data Consistency Issues**
```python
# Solution: Saga Pattern
class UserRegistrationSaga:
    def __init__(self, user_service, email_service, audit_service):
        self.user_service = user_service
        self.email_service = email_service
        self.audit_service = audit_service
    
    async def execute(self, user_data):
        try:
            # Step 1: Create user
            user = await self.user_service.create_user(user_data)
            
            # Step 2: Send welcome email
            await self.email_service.send_welcome_email(user)
            
            # Step 3: Log audit event
            await self.audit_service.log_user_created(user)
            
        except Exception as e:
            # Compensating actions
            await self._compensate(user_data, e)
    
    async def _compensate(self, user_data, error):
        # Rollback operations
        if hasattr(self, 'created_user'):
            await self.user_service.delete_user(self.created_user.id)
```

### 2. **Performance Degradation**
```python
# Solution: Caching & Async Processing
class CachedUserService:
    def __init__(self, user_service, cache):
        self.user_service = user_service
        self.cache = cache
    
    async def get_user(self, user_id: str) -> User:
        # Try cache first
        cached_user = await self.cache.get(f"user:{user_id}")
        if cached_user:
            return User.from_dict(cached_user)
        
        # Fallback to service
        user = await self.user_service.get_user(user_id)
        
        # Cache result
        await self.cache.set(f"user:{user_id}", user.to_dict(), ttl=3600)
        
        return user
```

### 3. **Integration Complexity**
```python
# Solution: Anti-Corruption Layer
class MonolithUserAdapter:
    def __init__(self, monolith_client):
        self.monolith_client = monolith_client
    
    def get_user(self, user_id: str) -> User:
        # Call monolith API
        monolith_response = self.monolith_client.get_user(user_id)
        
        # Transform to domain model
        return self._transform_user(monolith_response)
    
    def _transform_user(self, monolith_user) -> User:
        return User(
            id=str(monolith_user['user_id']),
            email=monolith_user['email_address'],
            name=f"{monolith_user['first_name']} {monolith_user['last_name']}",
            created_at=datetime.fromisoformat(monolith_user['creation_date'])
        )
```

## Success Metrics

### Technical Metrics
- **Deployment Frequency**: Tăng từ monthly → weekly
- **Lead Time**: Giảm từ weeks → days  
- **MTTR**: Giảm từ hours → minutes
- **Change Failure Rate**: < 15%

### Business Metrics
- **Feature Delivery Speed**: Tăng 2-3x
- **System Availability**: > 99.9%
- **Performance**: Response time < 200ms
- **Cost**: Giảm infrastructure cost 20-30%

Migration thành công khi đạt được cả technical và business objectives!
