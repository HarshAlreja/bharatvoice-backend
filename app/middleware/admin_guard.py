"""
Decorator for all /api/admin/* routes. Requires a valid JWT belonging to an Admin
(not a client User) with role=super_admin (or support_admin for read-only areas).
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("actor_type") != "admin":
            return jsonify({"status": "error", "message": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def super_admin_required(fn):
    """Stricter check for destructive actions (delete business, purge tenant, etc)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("actor_type") != "admin" or claims.get("role") != "super_admin":
            return jsonify({"status": "error", "message": "Super admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
