"""Registered as an app.before_request/after_request pair in app/__init__.py (optional
wiring) -- logs every request to api_request_logs for the admin analytics page."""
import time
from flask import request, g
from app.extensions import db
from app.models.api_request_log import ApiRequestLog


def start_timer():
    g._request_start_time = time.time()


def log_request(response):
    try:
        elapsed_ms = int((time.time() - g._request_start_time) * 1000)
        business_id = getattr(g, "business_id", None)
        log = ApiRequestLog(
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            business_id=business_id,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return response
