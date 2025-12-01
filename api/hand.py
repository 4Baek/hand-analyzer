import os
from flask import Blueprint, request, jsonify

from utils.hand_utils import analyze_hand
from services.recommend_service import recommend_rackets_from_metrics

hand_bp = Blueprint("hand_api", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@hand_bp.route("/scan-hand", methods=["POST"])
def scan_hand():
    if "file" not in request.files:
        return jsonify({"error": "이미지 파일이 필요합니다"}), 400

    file = request.files["file"]
    temp_path = os.path.join(BASE_DIR, "temp.jpg")
    file.save(temp_path)

    capture_distance = request.form.get("captureDistance")
    capture_device = request.form.get("captureDevice")

    try:
        capture_distance_cm = float(capture_distance) if capture_distance else None
    except:
        capture_distance_cm = None

    result = analyze_hand(
        temp_path,
        capture_distance_cm=capture_distance_cm,
        capture_device=capture_device,
    )

    if result is None:
        return jsonify({"error": "손 인식 실패"}), 400

    return jsonify(result)


@hand_bp.route("/recommend-rackets", methods=["POST"])
def recommend_rackets_api():
    data = request.get_json(silent=True) or {}
    result = recommend_rackets_from_metrics(data)
    return jsonify(result)
