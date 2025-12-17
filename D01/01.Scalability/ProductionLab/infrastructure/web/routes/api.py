"""
API Routes - Main application endpoints
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Dependencies will be injected via init_api_routes
_app_service = None
_web_adapter = None


def init_api_routes(app_service, web_adapter):
    """Initialize routes with dependencies"""
    global _app_service, _web_adapter
    _app_service = app_service
    _web_adapter = web_adapter


@api_bp.route('/')
def index():
    """Main endpoint - handles requests with session tracking"""
    result = _app_service.handle_request(_web_adapter)
    return _web_adapter.create_response(result)
