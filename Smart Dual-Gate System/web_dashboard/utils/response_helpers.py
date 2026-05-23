from flask import jsonify


def json_success(data=None, status=200):
    payload = {"success": True, "data": data}
    return jsonify(payload), status


def json_error(message, status=400):
    payload = {"success": False, "error": message}
    return jsonify(payload), status
