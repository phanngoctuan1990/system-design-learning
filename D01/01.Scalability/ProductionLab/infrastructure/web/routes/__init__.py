"""
Routes Module - Aggregates all route blueprints
"""
from flask import Flask

from .health import health_bp
from .api import api_bp
from .auth import auth_bp
from .address import address_bp


def register_routes(app: Flask) -> None:
    """Register all blueprints with the Flask app"""
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(address_bp)

