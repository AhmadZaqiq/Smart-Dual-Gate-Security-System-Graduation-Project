from flask import Blueprint, request, session

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import stream_service
from web_dashboard.utils.response_helpers import json_error, json_success

streams_api_bp = Blueprint("api_streams", __name__, url_prefix="/api/streams")


@streams_api_bp.route("/status")
@login_required
def streams_status():
    return json_success(stream_service.get_streams_status())


@streams_api_bp.route("/face/start", methods=["POST"])
@login_required
def start_face():
    ok, message = stream_service.start_face_stream()
    if not ok:
        return json_error(message, 400)
    return json_success({"message": message, "streams": stream_service.get_streams_status()})


@streams_api_bp.route("/face/stop", methods=["POST"])
@login_required
def stop_face():
    ok, message = stream_service.stop_face_stream()
    return json_success({"message": message, "streams": stream_service.get_streams_status()})


@streams_api_bp.route("/inner/start", methods=["POST"])
@login_required
def start_inner():
    ok, message = stream_service.start_inner_stream()
    if not ok:
        return json_error(message, 400)
    return json_success({"message": message, "streams": stream_service.get_streams_status()})


@streams_api_bp.route("/inner/stop", methods=["POST"])
@login_required
def stop_inner():
    ok, message = stream_service.stop_inner_stream()
    if not ok:
        return json_error(message, 400)
    return json_success({"message": message, "streams": stream_service.get_streams_status()})
