# services/racket_matching_service.py

from db_config import Racket


def _get_attr(obj, name, default=None):
    value = getattr(obj, name, None)
    return value if value is not None else default


def _compute_string_recommendation(hand_profile: dict, style_profile: dict) -> dict:
    """
    스트링 타입 / 텐션 추천 (추측 기반 로직).
    """
    level_score = style_profile.get("levelScore", 2)
    pain = style_profile.get("pain")
    styles = style_profile.get("styles") or []
    pref = style_profile.get("stringTypePreference") or "auto"

    # 기본 텐션 (kg)
    base_tension = 23.0

    # 레벨/스타일에 따른 보정
    if "control" in styles and level_score >= 3:
        base_tension += 1.0
    if "power" in styles and "control" not in styles:
        base_tension -= 0.5

    # 통증에 따른 보정
    if pain == "often":
        base_tension -= 1.5
    elif pain == "sometimes":
        base_tension -= 0.5

    # 스트링 타입 선호
    effective_type = pref
    if pref == "auto":
        if pain == "often":
            effective_type = "multi"
        elif "spin" in styles and pain != "often":
            effective_type = "poly"
        else:
            effective_type = "multi"

    # 타입별 미세 조정
    if effective_type == "poly":
        base_tension += 0.5
    elif effective_type == "multi":
        base_tension -= 0.5

    tension_main_kg = round(base_tension, 1)
    tension_main_lbs = round(tension_main_kg * 2.20462)

    label = None
    if effective_type == "poly":
        label = "폴리 계열 스트링"
    elif effective_type == "multi":
        label = "멀티필라멘트 계열 스트링"
    else:
        label = "기본 합성 스트링"

    # 설명
    reasons = []
    if pain == "often":
        reasons.append("팔·손목 통증이 있어 비교적 낮은 텐션과 부드러운 스트링을 우선했습니다.")
    if "control" in styles:
        reasons.append("컨트롤 지향 스타일을 반영해 너무 낮지 않은 텐션을 유지했습니다.")
    if "power" in styles and "control" not in styles:
        reasons.append("파워 위주 스타일을 반영해 텐션을 약간 낮게 설정했습니다.")
    if effective_type == "poly":
        reasons.append("스핀/내구성을 고려해 폴리 계열을 추천했습니다.")
    if effective_type == "multi":
        reasons.append("팔의 편안함을 고려해 멀티 계열을 추천했습니다.")

    reason_text = " ".join(reasons) if reasons else "설문과 손 프로파일을 종합해 기본 값에 가깝게 설정했습니다. (추측입니다)"

    return {
        "tensionMainKg": tension_main_kg,
        "tensionMainLbs": tension_main_lbs,
        "stringType": effective_type,
        "stringLabel": label,
        "reason": reason_text,
    }


def match_rackets(hand_profile: dict, style_profile: dict):
    """
    손 프로파일 + 플레이스타일 프로파일을 기반으로 라켓/스트링을 추천한다.

    - 라켓 스코어: power/control/spin/comfort + 무게/스윙웨이트/헤드사이즈/프레임강성까지 반영
    - 스트링: _compute_string_recommendation에서 별도 산출
    """
    power_w = style_profile.get("powerWeight", 1.0)
    control_w = style_profile.get("controlWeight", 1.0)
    spin_w = style_profile.get("spinWeight", 1.0)
    comfort_w = style_profile.get("comfortWeight", 1.0)

    level_score = style_profile.get("levelScore", 2)
    pain = style_profile.get("pain")
    weight_pref = style_profile.get("weightPreference", "medium")
    styles = style_profile.get("styles") or []

    size_cat = hand_profile.get("handSizeCategory") or hand_profile.get("sizeGroup")

    candidates = []

    for r in Racket.query.all():
        # 점수 계열(추후 DB 확장 시 활용)
        power_score = _get_attr(r, "power_score", _get_attr(r, "power", 5))
        control_score = _get_attr(r, "control_score", _get_attr(r, "control", 5))
        spin_score = _get_attr(r, "spin_score", _get_attr(r, "spin", 5))
        comfort_score = _get_attr(r, "comfort_score", 5)

        # 스펙 계열
        head_size = _get_attr(r, "head_size_sq_in", None)
        unstrung_weight = _get_attr(r, "unstrung_weight_g", _get_attr(r, "weight", None))
        swingweight = _get_attr(r, "swingweight", None)
        stiffness_ra = _get_attr(r, "stiffness_ra", None)
        balance_type = _get_attr(r, "balance_type", None)  # 'HL', 'EB', 'HH'
        string_pattern = _get_attr(r, "string_pattern", None)

        # 기본 스코어
        score = (
            power_score * power_w +
            control_score * control_w +
            spin_score * spin_w +
            comfort_score * comfort_w
        )

        # === 무게 보정 (손 크기 + 선호 + 통증, 추측 로직) ===
        # 기본 타깃
        target_weight = 295
        min_weight = 270
        max_weight = 315

        if weight_pref == "light":
            target_weight = 285
            min_weight = 260
            max_weight = 300
        elif weight_pref == "heavy":
            target_weight = 305
            min_weight = 285
            max_weight = 325

        # 손 크기 반영
        if size_cat in ("SMALL", "small"):
            target_weight -= 5
            max_weight -= 5
        elif size_cat in ("LARGE", "large"):
            target_weight += 5
            min_weight += 5

        # 통증 있으면 다시 가볍게
        if pain == "often":
            target_weight -= 5
            max_weight -= 5

        if isinstance(unstrung_weight, (int, float)):
            if min_weight <= unstrung_weight <= max_weight:
                score += 15
            else:
                diff = abs(unstrung_weight - target_weight)
                if diff <= 10:
                    score += 8
                elif diff >= 25:
                    score -= 8

        # === 헤드사이즈 & 스타일 보정 ===
        if isinstance(head_size, (int, float)):
            if "control" in styles and head_size <= 100:
                score += 6
            if "power" in styles and head_size >= 100:
                score += 6

        # === 스윙웨이트 & 레벨/통증 보정 ===
        if isinstance(swingweight, (int, float)):
            if level_score <= 2 and swingweight > 325:
                score -= 10
            if pain == "often" and swingweight > 330:
                score -= 8

        # === 프레임 강성 & 통증 보정 ===
        if isinstance(stiffness_ra, (int, float)):
            if pain == "often" and stiffness_ra >= 67:
                score -= 10
            elif pain == "none" and stiffness_ra >= 67 and "power" in styles:
                score += 5
            if pain == "often" and stiffness_ra <= 63:
                score += 8

        # === 밸런스 타입 보정 (HL 선호) ===
        if balance_type == "HL":
            score += 3

        # === 스핀 스타일 & 스트링 패턴 ===
        if "spin" in styles and string_pattern:
            if "16x19" in string_pattern or "16x18" in string_pattern:
                score += 4

        candidates.append({
            "id": r.id,
            "name": r.name,
            "brand": r.brand,
            "weight": unstrung_weight,
            "headSize": head_size,
            "swingweight": swingweight,
            "stiffnessRa": stiffness_ra,
            "balanceType": balance_type,
            "stringPattern": string_pattern,
            "powerScore": power_score,
            "controlScore": control_score,
            "spinScore": spin_score,
            "comfortScore": comfort_score,
            "score": float(score),
        })

    # 점수순 상위 5개
    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:5]

    string_rec = _compute_string_recommendation(hand_profile, style_profile)

    return {
        "rackets": candidates,
        "string": string_rec,
    }
