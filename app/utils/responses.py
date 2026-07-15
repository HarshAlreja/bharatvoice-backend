"""Standard {status, message, data} response wrapper -- keep every endpoint consistent."""
from flask import jsonify


def success(data=None, message="OK", code=200):
    return jsonify({"status": "success", "message": message, "data": data}), code


def error(message="Something went wrong", code=400):
    return jsonify({"status": "error", "message": message}), code
