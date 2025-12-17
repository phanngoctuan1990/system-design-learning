"""
Auth Routes - User registration, login, and profile endpoints
"""
from flask import Blueprint, request, g

# Import middleware
from infrastructure.web.middleware import login_required

auth_bp = Blueprint('auth', __name__)

# Dependencies will be injected via init_auth_routes
_auth_service = None
_web_adapter = None


def init_auth_routes(auth_service, web_adapter):
    """Initialize routes with dependencies"""
    global _auth_service, _web_adapter
    _auth_service = auth_service
    _web_adapter = web_adapter



@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json() or {}
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return _web_adapter.create_response(
            {"success": False, "error": "Username and password are required"},
            400
        )
    
    result = _auth_service.register(
        username=username,
        password=password,
        full_name=data.get('full_name'),
        email=data.get('email'),
        address_id=data.get('address_id'),
        address_detail=data.get('address_detail')
    )
    
    status_code = 201 if result['success'] else 400
    return _web_adapter.create_response(result, status_code)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and set session cookie"""
    data = request.get_json() or {}
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return _web_adapter.create_response(
            {"success": False, "error": "Username and password are required"},
            400
        )
    
    result = _auth_service.login(username, password)
    
    if result['success']:
        response = _web_adapter.create_response(result, 200)
        response.set_cookie(
            'session_id', 
            result['session_id'],
            max_age=3600,
            httponly=True,
            samesite='Lax'
        )
        return response
    
    return _web_adapter.create_response(result, 401)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user and clear session cookie"""
    session_id = request.cookies.get('session_id')
    
    if session_id:
        result = _auth_service.logout(session_id)
    else:
        result = {"success": True, "message": "No active session"}
    
    response = _web_adapter.create_response(result, 200)
    response.delete_cookie('session_id')
    return response


@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get current user's profile.
    Requires authentication (session cookie).
    g.user_id is set by @login_required decorator.
    """
    profile = _auth_service.get_profile(g.user_id)
    
    if not profile:
        return _web_adapter.create_response(
            {"success": False, "error": "User not found"},
            404
        )
    
    return _web_adapter.create_response({
        "success": True,
        "profile": profile
    })


