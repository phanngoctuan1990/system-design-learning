"""
Health Routes - Health check and server info endpoints
"""
from flask import Blueprint

health_bp = Blueprint('health', __name__)

# Dependencies will be injected via init_health_routes
_app_service = None
_web_adapter = None


def init_health_routes(app_service, web_adapter):
    """Initialize routes with dependencies"""
    global _app_service, _web_adapter
    _app_service = app_service
    _web_adapter = web_adapter


@health_bp.route('/health')
def health():
    """Health check endpoint"""
    health_status = _app_service.check_health()
    status_code = 200 if health_status.status == "healthy" else 503
    return _web_adapter.create_response({
        "status": health_status.status,
        "message": health_status.message,
        "timestamp": health_status.timestamp
    }, status_code)


@health_bp.route('/info')
def info():
    """Server information endpoint"""
    return _web_adapter.create_response(_app_service.get_server_info())
