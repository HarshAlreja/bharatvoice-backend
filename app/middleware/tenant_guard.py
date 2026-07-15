"""
Decorator for all /api/{client routes}. This is the actual multi-tenant security
boundary: it reads business_id from the JWT (NOT from the URL or a header the
client could tamper with) and injects it into the request so every query can be
scoped correctly. If a header X-Business-ID is also sent, it must match the JWT's
business_id or the request is rejected -- prevents a client editing the header to
peek at another tenant's data.
"""
from functools import wraps
from flask import jsonify, request, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def tenant_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("actor_type") != "client":
            return jsonify({"status": "error", "message": "Client access required"}), 403

        jwt_business_id = claims.get("business_id")
        if not jwt_business_id:
            return jsonify({"status": "error", "message": "No business associated with this account"}), 403

        header_business_id = request.headers.get("X-Business-ID")
        if header_business_id and str(header_business_id) != str(jwt_business_id):
            return jsonify({"status": "error", "message": "Business ID mismatch"}), 403

        g.business_id = jwt_business_id
        return fn(*args, **kwargs)
    return wrapper
