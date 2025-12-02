from flask import Blueprint, request, jsonify
from db_config import (
    db,
    reset_db,
    Racket,
    HandMetrics,
    SurveyResponse,
    RecommendationLog,
)

admin_bp = Blueprint("admin_api", __name__)


# ------------------------------------------------------------
# 공통 유틸
# ------------------------------------------------------------


def _to_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_tags(tags):
    """
    tags가 문자열이면 그대로, 리스트면 쉼표로 이어서 저장.
    """
    if tags is None:
        return None
    if isinstance(tags, list):
        parts = [str(t).strip() for t in tags if str(t).strip()]
        return ",".join(parts) if parts else None
    s = str(tags).strip()
    return s or None


def _apply_racket_fields_from_dict(racket: Racket, data: dict, is_create: bool = False):
    """
    Racket 인스턴스에 dict에서 온 필드를 적용.
    - is_create=True이면 기본값(is_active=True 등)도 설정.
    """
    if "name" in data:
        name = (data.get("name") or "").strip()
        if name:
            racket.name = name
    if "brand" in data:
        brand = (data.get("brand") or "").strip()
        if brand:
            racket.brand = brand

    # 기본 점수 필드 (기존 UI 호환)
    if "power" in data:
        racket.power = _to_int(data.get("power"))
    if "control" in data:
        racket.control = _to_int(data.get("control"))
    if "spin" in data:
        racket.spin = _to_int(data.get("spin"))
    if "weight" in data:
        racket.weight = _to_int(data.get("weight"))

    # 태그
    if "tags" in data:
        racket.tags = _normalize_tags(data.get("tags"))

    # 예약 URL
    if "url" in data:
        url = (data.get("url") or "").strip()
        racket.url = url or None

    # 스펙 필드들
    if "headSizeSqIn" in data or "head_size_sq_in" in data:
        racket.head_size_sq_in = _to_int(
            data.get("headSizeSqIn") or data.get("head_size_sq_in")
        )

    if (
        "unstrungWeightG" in data
        or "unstrung_weight_g" in data
        or ("weight" in data and is_create)
    ):
        # weight만 들어온 경우도 언스트렁 무게로 같이 보정
        uw = data.get("unstrungWeightG") or data.get("unstrung_weight_g")
        if uw is None and "weight" in data:
            uw = data.get("weight")
        racket.unstrung_weight_g = _to_int(uw)

    if "swingweight" in data:
        racket.swingweight = _to_int(data.get("swingweight"))

    if "stiffnessRa" in data or "stiffness_ra" in data:
        racket.stiffness_ra = _to_int(
            data.get("stiffnessRa") or data.get("stiffness_ra")
        )

    if "stringPattern" in data or "string_pattern" in data:
        sp = (data.get("stringPattern") or data.get("string_pattern") or "").strip()
        racket.string_pattern = sp or None

    if "lengthMm" in data or "length_mm" in data:
        racket.length_mm = _to_int(data.get("lengthMm") or data.get("length_mm"))

    if "balanceType" in data or "balance_type" in data:
        bt = (data.get("balanceType") or data.get("balance_type") or "").strip()
        racket.balance_type = bt or None

    if "beamWidthMm" in data or "beam_width_mm" in data:
        racket.beam_width_mm = _to_int(
            data.get("beamWidthMm") or data.get("beam_width_mm")
        )

    # 점수 확장 필드
    if "powerScore" in data:
        racket.power_score = _to_int(data.get("powerScore"))
    if "controlScore" in data:
        racket.control_score = _to_int(data.get("controlScore"))
    if "spinScore" in data:
        racket.spin_score = _to_int(data.get("spinScore"))
    if "comfortScore" in data:
        racket.comfort_score = _to_int(data.get("comfortScore"))
    if "maneuverScore" in data:
        racket.maneuver_score = _to_int(data.get("maneuverScore"))

    # 타깃 레벨
    if "levelMin" in data:
        racket.level_min = _to_int(data.get("levelMin"))
    if "levelMax" in data:
        racket.level_max = _to_int(data.get("levelMax"))

    # 활성 여부
    if "isActive" in data:
        racket.is_active = bool(data.get("isActive"))
    elif is_create:
        # 생성 시 별도 값이 없으면 True
        racket.is_active = True


# ------------------------------------------------------------
# DB 초기화
# ------------------------------------------------------------


@admin_bp.route("/admin/reset-db", methods=["POST"])
def reset_db_route():
    reset_db()
    return jsonify({"status": "ok", "message": "DB reset complete"})


# ------------------------------------------------------------
# 라켓 Admin API
# ------------------------------------------------------------


@admin_bp.route("/admin/rackets", methods=["GET", "POST"])
def admin_rackets():
    """
    GET  /admin/rackets   : 모든 라켓 조회 (활성/비활성 모두)
    POST /admin/rackets   : 라켓 신규 등록
    """
    if request.method == "GET":
        rackets = Racket.query.order_by(Racket.id.asc()).all()
        return jsonify({"rackets": [r.to_dict() for r in rackets]})

    # POST - 생성
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    brand = (data.get("brand") or "").strip()

    if not name or not brand:
        return (
            jsonify({"error": "name/brand 필드는 반드시 필요합니다."}),
            400,
        )

    racket = Racket(name=name, brand=brand)
    _apply_racket_fields_from_dict(racket, data, is_create=True)

    db.session.add(racket)
    db.session.commit()

    return jsonify({"racket": racket.to_dict()}), 201


@admin_bp.route("/admin/rackets/<int:racket_id>", methods=["GET", "PUT", "DELETE"])
def admin_racket_detail(racket_id):
    """
    GET    /admin/rackets/<id> : 단건 조회
    PUT    /admin/rackets/<id> : 단건 수정 (부분 수정 허용)
    DELETE /admin/rackets/<id> : 단건 삭제
    """
    racket = Racket.query.get(racket_id)
    if racket is None:
        return jsonify({"error": "not found"}), 404

    if request.method == "GET":
        return jsonify({"racket": racket.to_dict()})

    if request.method == "DELETE":
        db.session.delete(racket)
        db.session.commit()
        return jsonify({"status": "ok"})

    # PUT - 수정
    data = request.get_json(silent=True) or {}
    _apply_racket_fields_from_dict(racket, data, is_create=False)
    db.session.commit()
    return jsonify({"racket": racket.to_dict()})


# ------------------------------------------------------------
# HandMetrics / SurveyResponse / RecommendationLog 조회용 API
# ------------------------------------------------------------


@admin_bp.route("/admin/hand-metrics", methods=["GET"])
def admin_hand_metrics():
    """
    최근 손 분석 결과 조회 (기본 50건, 최대 200건)
    """
    limit = _to_int(request.args.get("limit")) or 50
    limit = max(1, min(limit, 200))

    rows = (
        HandMetrics.query.order_by(HandMetrics.id.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"items": [r.to_dict() for r in rows]})


@admin_bp.route("/admin/surveys", methods=["GET"])
def admin_surveys():
    """
    최근 설문 응답 조회 (기본 50건, 최대 200건)
    """
    limit = _to_int(request.args.get("limit")) or 50
    limit = max(1, min(limit, 200))

    rows = (
        SurveyResponse.query.order_by(SurveyResponse.id.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"items": [r.to_dict() for r in rows]})


@admin_bp.route("/admin/recommendations", methods=["GET"])
def admin_recommendations():
    """
    최근 추천 로그 조회 (기본 50건, 최대 200건)
    - hand_metrics_id / survey_response_id / racket_id / 점수 / 스트링 정보 등 포함
    """
    limit = _to_int(request.args.get("limit")) or 50
    limit = max(1, min(limit, 200))

    rows = (
        RecommendationLog.query.order_by(RecommendationLog.id.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"items": [r.to_dict() for r in rows]})
