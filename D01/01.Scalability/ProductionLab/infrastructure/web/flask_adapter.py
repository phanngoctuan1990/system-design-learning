"""
Flask Adapter - Implementation of WebPort for Flask
"""
from typing import Dict, Any, Optional
from flask import request, make_response, jsonify
from core.interfaces.web_port import WebPort

class FlaskAdapter(WebPort):
    def __init__(self):
        self._current_response = None
    
    def get_request_data(self) -> Dict[str, Any]:
        return {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "json": request.get_json() if request.is_json else None
        }
    
    def get_session_id(self) -> Optional[str]:
        return request.cookies.get('session_id')
    
    def set_session_id(self, session_id: str) -> None:
        # Store for later use in create_response
        self._session_id = session_id
    
    def create_response(self, data: Dict[str, Any], status_code: int = 200) -> Any:
        response = make_response(jsonify(data), status_code)
        
        # Set session cookie if available
        if hasattr(self, '_session_id'):
            response.set_cookie('session_id', self._session_id, max_age=3600)
            delattr(self, '_session_id')
        
        return response
