from flask import Blueprint, render_template

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config

live_bp = Blueprint("live", __name__, url_prefix="/live")


@live_bp.route("/")
@login_required
def index():
    return render_template(
        "live/index.html",
        stream_url=Config.YOLO_STREAM_BASE_URL,
    )
