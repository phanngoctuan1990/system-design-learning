"""
Main Application - Composition Root
Wires together core and infrastructure components
"""
import os
import signal
import sys
from flask import Flask

# Core imports
from core.services.app_service import AppService
from core.services.auth_service import AuthService
from core.services.address_service import AddressService

# Infrastructure imports
from infrastructure.cache.redis_adapter import RedisAdapter
from infrastructure.cache.memory_adapter import MemoryAdapter
from infrastructure.database.mysql_adapter import MySQLAdapter
from infrastructure.web.flask_adapter import FlaskAdapter
from infrastructure.web.routes import register_routes
from infrastructure.web.routes.health import init_health_routes
from infrastructure.web.routes.api import init_api_routes
from infrastructure.web.routes.auth import init_auth_routes
from infrastructure.web.routes.address import init_address_routes

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
USE_REDIS = os.getenv('USE_REDIS', 'true').lower() == 'true'

# MySQL Configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'app_user')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'app_password')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'app_db')


# Dependency Injection
def create_cache_adapter():
    if USE_REDIS:
        try:
            cache = RedisAdapter(host=REDIS_HOST)
            cache.ping()  # Test connection
            return cache
        except Exception:
            print("Redis unavailable, falling back to memory cache")
    
    return MemoryAdapter()


def create_database_adapter():
    try:
        db = MySQLAdapter(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        db.ping()  # Test connection
        return db
    except Exception as e:
        print(f"MySQL connection failed: {e}")
        return None


def create_app():
    """Application factory - creates and configures Flask app"""
    app = Flask(__name__)
    
    # Initialize dependencies
    cache = create_cache_adapter()
    db = create_database_adapter()
    
    app_service = AppService(cache)
    web_adapter = FlaskAdapter()
    
    # Initialize middleware (must be before routes that use them)
    from infrastructure.web.middleware import init_auth_middleware
    init_auth_middleware(cache, web_adapter)
    
    # Inject dependencies into routes
    init_health_routes(app_service, web_adapter)
    init_api_routes(app_service, web_adapter)
    
    # Initialize auth routes if database is available
    if db:
        # Create services with cache for session management
        auth_service = AuthService(db, cache)
        address_service = AddressService(db)
        
        init_auth_routes(auth_service, web_adapter)
        init_address_routes(address_service, web_adapter)
    
    # Register all blueprints
    register_routes(app)
    
    return app


# Create app instance
flask_app = create_app()

# Graceful shutdown
def signal_handler(sig, frame):
    print(f"Received signal {sig}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=5000, debug=False)

