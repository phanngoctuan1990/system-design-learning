"""
Auth Middleware - Authentication decorators for protected routes
"""
from functools import wraps
from flask import request, g
import json

# Dependencies will be injected via init_auth_middleware
_cache = None
_web_adapter = None


def init_auth_middleware(cache, web_adapter):
    """
    Initialize middleware with dependencies.
    Must be called before using @login_required decorator.
    """
    global _cache, _web_adapter
    _cache = cache
    _web_adapter = web_adapter


def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Validates session cookie against Redis cache.
    Sets g.user_id, g.username, g.session_id if authenticated.
    
    Usage:
        from infrastructure.web.middleware import login_required
        
        @some_bp.route('/protected')
        @login_required
        def protected_route():
            user_id = g.user_id  # Available after auth check
            username = g.username
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get session_id from cookie
        session_id = request.cookies.get('session_id')
        
        if not session_id:
            return _web_adapter.create_response(
                {"success": False, "error": "Authentication required"},
                401
            )
        
        if not _cache:
            return _web_adapter.create_response(
                {"success": False, "error": "Session service unavailable"},
                503
            )
        
        # Validate session in cache (Redis)
        session_data = _cache.get(f"auth_session:{session_id}")
        
        if not session_data:
            return _web_adapter.create_response(
                {"success": False, "error": "Session expired or invalid"},
                401
            )
        
        # Parse session and set user info in Flask's g object
        try:
            session = json.loads(session_data)
            g.user_id = session.get('user_id')
            g.username = session.get('username')
            g.session_id = session_id
        except Exception:
            return _web_adapter.create_response(
                {"success": False, "error": "Invalid session data"},
                401
            )
        
        return f(*args, **kwargs)
    
    return decorated_function
