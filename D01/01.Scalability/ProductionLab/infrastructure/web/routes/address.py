"""
Address Routes - Address lookup endpoints for cascading dropdowns
"""
from flask import Blueprint, request

address_bp = Blueprint('address', __name__, url_prefix='/addresses')

# Dependencies will be injected via init_address_routes
_address_service = None
_web_adapter = None


def init_address_routes(address_service, web_adapter):
    """Initialize routes with dependencies"""
    global _address_service, _web_adapter
    _address_service = address_service
    _web_adapter = web_adapter


@address_bp.route('/countries', methods=['GET'])
def get_countries():
    """Get list of all countries"""
    countries = _address_service.get_countries()
    return _web_adapter.create_response({"countries": countries})


@address_bp.route('/provinces', methods=['GET'])
def get_provinces():
    """Get provinces for a country"""
    country = request.args.get('country')
    
    if not country:
        return _web_adapter.create_response(
            {"error": "country parameter is required"}, 400
        )
    
    provinces = _address_service.get_provinces(country)
    return _web_adapter.create_response({"provinces": provinces})


@address_bp.route('/districts', methods=['GET'])
def get_districts():
    """Get districts for a country + province"""
    country = request.args.get('country')
    province = request.args.get('province')
    
    if not country or not province:
        return _web_adapter.create_response(
            {"error": "country and province parameters are required"}, 400
        )
    
    districts = _address_service.get_districts(country, province)
    return _web_adapter.create_response({"districts": districts})
