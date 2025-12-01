import os
from flask import Blueprint, request, jsonify

from utils.hand_utils import analyze_hand
from services.recommend_service import recommend_rackets_from_metrics
from services.history_service import save_hand_metrics_from_result  # ✅ 추가

hand_bp = Blueprint("hand_api", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@hand_bp.route("/scan-hand", methods=["POST"])
def scan_hand():
    # 파일 체크
    if "file" not in request.files:
        return jsonify({"error": "이미지 파일이 필요합니다"}), 400

    file = request.files["file"]

    # 임시 저장 경로 (필요하면 uuid 등으로 바꿔도 됨)
    temp_path = os.path.join(BASE_DIR, "temp.jpg")
    file.save(temp_path)

    # 촬영 정보
    capture_distance = request.form.get("captureDistance")
    capture_device = request.form.get("captureDevice")

    try:
        capture_distance_cm = float(capture_distance) if capture_distance else None
    except Exception:
        capture_distance_cm = None

    # 손 분석 실행
    result = analyze_hand(
        temp_path,
        capture_distance_cm=capture_distance_cm,
        capture_device=capture_device,
    )

    if result is None:
        return jsonify({"error": "손 인식 실패"}), 400

    # ✅ DB에 hand_metrics 저장
    hand_metrics_row = save_hand_metrics_from_result(result)

    # ✅ 프론트에서 다시 쓸 수 있도록 id 포함
    result["handMetricsId"] = hand_metrics_row.id

    return jsonify(result)


@hand_bp.route("/recommend-rackets", methods=["POST"])
def recommend_rackets_api():
    # JSON 바디만 받는 구조 유지
    data = request.get_json(silent=True) or {}
    result = recommend_rackets_from_metrics(data)
    return jsonify(result)
