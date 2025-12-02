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

    # 기본 값
    base_string_type = "poly"  # 기본값
    base_tension_kg = 23.0

    # 레벨에 따라 기본 텐션 조정
    if level_score <= 1:
        base_tension_kg = 21.0
    elif level_score == 2:
        base_tension_kg = 22.0
    elif level_score == 3:
        base_tension_kg = 23.0
    else:
        base_tension_kg = 24.0

    # 통증이 많으면 텐션 다운 + 부드러운 스트링 쪽으로
    if pain == "often":
        base_tension_kg -= 1.5
        base_string_type = "multi"
    elif pain == "sometimes":
        base_tension_kg -= 0.5

    # 플레이 스타일 반영
    if "power" in styles:
        base_tension_kg += 0.5
    if "control" in styles:
        base_tension_kg += 0.5
    if "spin" in styles:
        # 스핀 위주이면 약간 낮추는 방향도 가능하지만, 여기서는 유지
        pass

    # 사용자 선호 타입이 있으면 우선
    if pref in ("poly", "multi"):
        base_string_type = pref

    # 합리적인 범위 클램핑
    if base_tension_kg < 18.0:
        base_tension_kg = 18.0
    if base_tension_kg > 27.0:
        base_tension_kg = 27.0

    tension_lbs = int(round(base_tension_kg * 2.205))

    if base_string_type == "poly":
        label = "폴리 스트링 추천"
        reason = (
            "스핀과 컨트롤을 중시하는 플레이에 적합한 폴리 스트링을 기준으로 텐션을 산출했습니다. "
            "팔에 무리가 가지 않도록 레벨과 통증 여부를 함께 고려했습니다."
        )
    else:
        label = "멀티필라멘트 스트링 추천"
        reason = (
            "팔·손목 부담을 줄이고 타구감을 부드럽게 하기 위해 멀티필라멘트 계열 스트링을 기준으로 산출했습니다. "
            "통증 여부와 레벨을 반영해 텐션을 조정했습니다."
        )

    return {
        "stringType": base_string_type,
        "stringLabel": label,
        "tensionMainKg": round(base_tension_kg, 1),
        "tensionMainLbs": tension_lbs,
        "reason": reason,
    }


def _build_racket_reason(
    hand_profile: dict,
    style_profile: dict,
    *,
    head_size,
    unstrung_weight,
    swingweight,
    stiffness_ra,
    string_pattern,
    power_score,
    control_score,
    spin_score,
) -> str:
    """
    한 개 라켓에 대해 손/플레이스타일/스펙을 설명하는 추천 사유 문구 생성.
    - '(추측입니다)' 같은 표현은 사용하지 않는다.
    """
    size_cat = hand_profile.get("handSizeCategory")
    styles = style_profile.get("styles") or []
    level_score = style_profile.get("levelScore", 2)
    pain = style_profile.get("pain")

    reasons = []

    # 손 크기
    if size_cat == "SMALL":
        reasons.append("손 크기가 비교적 작은 편이라 상대적으로 부담이 적은 스펙의 라켓을 우선 고려했습니다.")
    elif size_cat == "LARGE":
        reasons.append("손 크기가 큰 편이라 무게와 스윙웨이트를 조금 더 받아줄 수 있는 라켓을 우선 고려했습니다.")
    else:
        reasons.append("손 크기가 평균 범위에 가까워 범용적인 스펙의 라켓을 중심으로 추천했습니다.")

    # 무게/스윙웨이트
    if isinstance(unstrung_weight, (int, float)):
        if unstrung_weight <= 285:
            reasons.append("언스트렁 기준 285g 이하의 비교적 가벼운 무게로, 스윙이 편하고 피로도가 덜합니다.")
        elif unstrung_weight >= 305:
            reasons.append("언스트렁 기준 305g 이상의 무게로, 볼을 눌러 치는 파워에 유리합니다.")
        else:
            reasons.append("언스트렁 기준 290~300g대의 중간 무게로, 파워와 컨트롤의 균형을 노릴 수 있습니다.")

    if isinstance(swingweight, (int, float)):
        if swingweight <= 315:
            reasons.append("스윙웨이트가 낮은 편이라 라켓 헤드가 가볍게 따라와 빠른 스윙에 적합합니다.")
        elif swingweight >= 325:
            reasons.append("스윙웨이트가 높은 편이라 임팩트 시 안정감과 볼의 관통력이 좋습니다.")

    # 헤드 사이즈
    if isinstance(head_size, (int, float)):
        if head_size >= 100:
            reasons.append("헤드 사이즈 100sq.in 이상으로 스윗스폿이 넓어 미스샷에 관대합니다.")
        elif head_size <= 98:
            reasons.append("헤드 사이즈 98sq.in 이하로, 정교한 컨트롤과 방향성을 중시하는 스타일에 어울립니다.")

    # 프레임 강성
    if isinstance(stiffness_ra, (int, float)):
        if stiffness_ra >= 67:
            reasons.append("프레임 강성이 높은 편이라 반발력이 좋고 파워를 내기 수월합니다.")
        elif stiffness_ra <= 63:
            reasons.append("프레임 강성이 낮은 편이라 타구감이 부드럽고 팔 부담이 적은 편입니다.")

    # 스트링 패턴
    if string_pattern:
        if "16x19" in string_pattern.replace(" ", ""):
            reasons.append("16x19 패턴으로 스핀을 걸기 쉽고 볼을 띄우기 좋습니다.")
        elif "18x20" in string_pattern.replace(" ", ""):
            reasons.append("18x20 패턴으로 탄도가 낮고, 납작하게 밀어치는 컨트롤 위주 플레이에 적합합니다.")

    # 플레이 스타일 반영
    if "power" in styles and power_score is not None:
        reasons.append(
            f"파워 성향({power_score}/10)을 살리기에 적합한 프레임 특성을 가진 라켓입니다."
        )
    if "control" in styles and control_score is not None:
        reasons.append(
            f"컨트롤 성향({control_score}/10)에 맞춰 방향성과 안정성을 중시하는 세팅입니다."
        )
    if "spin" in styles and spin_score is not None:
        reasons.append(
            f"스핀 성향({spin_score}/10)을 고려하여 회전을 걸기 쉬운 스펙과 패턴을 가진 라켓입니다."
        )

    # 레벨과 통증 여부
    if pain in ("sometimes", "often"):
        reasons.append("팔·손목 통증 이력을 고려해 너무 무겁거나 과도하게 단단한 조합은 피했습니다.")
    if level_score <= 2:
        reasons.append("입문·초급 레벨에서도 다루기 쉽게 설계된 스펙을 우선 반영했습니다.")
    elif level_score >= 3:
        reasons.append("중급 이상 레벨에서 볼을 눌러 칠 수 있도록 약간 더 무게와 안정성을 주는 조합을 반영했습니다.")

    return " ".join(reasons)


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

    # 손 크기
    size_cat = hand_profile.get("handSizeCategory")
    size_group = hand_profile.get("sizeGroup")

    candidates = []

    # ★ is_active=True 인 라켓만 추천 대상에 포함
    for r in Racket.query.filter_by(is_active=True).all():
        # 점수 계열(추후 DB 확장 시 활용)
        power_score = _get_attr(r, "power_score", _get_attr(r, "power", 5))
        control_score = _get_attr(r, "control_score", _get_attr(r, "control", 5))
        spin_score = _get_attr(r, "spin_score", _get_attr(r, "spin", 5))
        comfort_score = _get_attr(r, "comfort_score", 5)

        # 스펙 계열
        head_size = _get_attr(r, "head_size_sq_in", None)
        unstrung_weight = _get_attr(
            r, "unstrung_weight_g", _get_attr(r, "weight", None)
        )
        swingweight = _get_attr(r, "swingweight", None)
        stiffness_ra = _get_attr(r, "stiffness_ra", None)
        balance_type = _get_attr(r, "balance_type", None)  # 'HL', 'EB', 'HH'
        string_pattern = _get_attr(r, "string_pattern", None)

        # 무게/손 크기/통증에 따른 가중치 조정
        weight_score = 0.0
        if isinstance(unstrung_weight, (int, float)):
            target_weight = 295
            min_weight = 270
            max_weight = 315

            # 레벨 반영
            if level_score <= 1:
                target_weight = 285
                max_weight = 300
            elif level_score >= 3:
                target_weight = 300
                min_weight = 280

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
                    weight_score = 1.0
                else:
                    diff = abs(unstrung_weight - target_weight)
                    weight_score = max(0.0, 1.0 - diff / 30.0)

        # 밸런스/스윙웨이트 기반 안정성 점수
        stability_score = 0.0
        if isinstance(swingweight, (int, float)):
            if swingweight >= 325:
                stability_score += 0.5
            elif swingweight <= 310:
                stability_score -= 0.3

        if balance_type == "HL":
            stability_score += 0.2
        elif balance_type == "HH":
            stability_score -= 0.2

        # 통증 여부에 따른 comfort 보정
        comfort_adj = 0.0
        if pain == "often":
            comfort_adj += 1.0
        elif pain == "sometimes":
            comfort_adj += 0.5

        final_comfort = (comfort_score or 5) + comfort_adj

        # 스타일 가중치 적용
        base_score = (
            power_score * power_w
            + control_score * control_w
            + spin_score * spin_w
            + final_comfort * comfort_w
        )

        # 무게/안정성 반영
        base_score += weight_score * 1.5 + stability_score

        # 손 크기 그룹/레벨에 따라 약간 보정 (예: SMALL + 무거운 라켓이면 감점 등)
        if size_cat == "SMALL" and isinstance(unstrung_weight, (int, float)):
            if unstrung_weight >= 305:
                base_score -= 1.0
        if size_cat == "LARGE" and isinstance(unstrung_weight, (int, float)):
            if unstrung_weight <= 280:
                base_score -= 0.5

        candidates.append(
            {
                "racket": r,
                "score": float(base_score),
                "powerScore": power_score,
                "controlScore": control_score,
                "spinScore": spin_score,
                "comfortScore": final_comfort,
                "headSize": head_size,
                "unstrungWeight": unstrung_weight,
                "swingweight": swingweight,
                "stiffnessRa": stiffness_ra,
                "stringPattern": string_pattern,
            }
        )

    # 점수 기준 정렬
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # 상위 N개만 노출
    top_n = 8
    result_rackets = []
    if candidates:
        max_score = candidates[0]["score"] or 1.0
    else:
        max_score = 1.0

    for rank, c in enumerate(candidates[:top_n], start=1):
        r = c["racket"]
        score = c["score"]
        normalized = (score / max_score) * 100.0 if max_score > 0 else 0.0

        reason = _build_racket_reason(
            hand_profile,
            style_profile,
            head_size=c["headSize"],
            unstrung_weight=c["unstrungWeight"],
            swingweight=c["swingweight"],
            stiffness_ra=c["stiffnessRa"],
            string_pattern=c["stringPattern"],
            power_score=c["powerScore"],
            control_score=c["controlScore"],
            spin_score=c["spinScore"],
        )

        result_rackets.append(
            {
                "id": r.id,
                "name": r.name,
                "brand": r.brand,
                "score": round(normalized, 1),
                "power": c["powerScore"],
                "control": c["controlScore"],
                "spin": c["spinScore"],
                "comfort": c["comfortScore"],
                "head_size_sq_in": c["headSize"],
                "unstrung_weight_g": c["unstrungWeight"],
                "swingweight": c["swingweight"],
                "stiffness_ra": c["stiffnessRa"],
                "string_pattern": c["stringPattern"],
                "tags": r.tags,
                "url": r.url,
                "reason": reason,
            }
        )

    # 스트링 추천
    string_rec = _compute_string_recommendation(hand_profile, style_profile)

    return {
        "rackets": result_rackets,
        "string": string_rec,
    }
