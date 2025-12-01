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

    reason_text = " ".join(reasons) if reasons else "설문과 손 프로파일을 종합해 기본 값에 가깝게 설정했습니다. "

    return {
        "tensionMainKg": tension_main_kg,
        "tensionMainLbs": tension_main_lbs,
        "stringType": effective_type,
        "stringLabel": label,
        "reason": reason_text,
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
    한 개 라켓에 대해 손/플레이스타일/스펙을 근거로 추천 이유 문장을 만든다. 
    """
    size_cat = hand_profile.get("handSizeCategory") or hand_profile.get("sizeGroup")
    pain = style_profile.get("pain")
    styles = style_profile.get("styles") or []
    level = style_profile.get("level")
    weight_pref = style_profile.get("weightPreference")

    parts = []

    # 1) 손 크기 + 무게 선호
    if isinstance(unstrung_weight, (int, float)):
        if size_cat in ("SMALL", "small"):
            if unstrung_weight <= 290:
                parts.append("작은 손 기준에서도 부담이 덜한 비교적 가벼운 무게라 스윙하기 편한 편입니다. ")
            else:
                parts.append("무게는 약간 있는 편이지만 작은 손에서도 안정적인 타구감을 줄 수 있는 스펙입니다. ")
        elif size_cat in ("LARGE", "large"):
            if unstrung_weight >= 295:
                parts.append("손이 큰 편이어서 약간 묵직한 무게가 헤드 안정성을 높여주는 구성이어서 추천했습니다. ")
            else:
                parts.append("손 크기에 비해 가벼운 편이라 빠른 스윙과 민첩한 플레이에 유리하다고 판단했습니다. ")

        if weight_pref == "light" and unstrung_weight <= 290:
            parts.append("설문에서 가벼운 라켓을 선호해 이 무게대 라켓을 우선 배치했습니다. ")
        if weight_pref == "heavy" and unstrung_weight >= 300:
            parts.append("묵직한 라켓을 선호하는 응답을 반영해 무게감 있는 스펙을 선택했습니다. ")

    # 2) 통증 + 강성/스윙웨이트
    if pain == "often":
        if isinstance(stiffness_ra, (int, float)) and stiffness_ra <= 64:
            parts.append("프레임 강성이 낮은 편이라 임팩트 시 팔·손목에 전달되는 충격을 줄여줍니다. ")
        if isinstance(swingweight, (int, float)) and swingweight <= 330:
            parts.append("스윙웨이트가 과하지 않아 장시간 플레이에서도 팔에 부담이 덜한 편입니다. ")
    elif pain == "none":
        if isinstance(stiffness_ra, (int, float)) and stiffness_ra >= 66:
            parts.append("탄성 있는 프레임 특성으로 강하게 휘둘렀을 때 파워를 내기 좋은 구성이어서 선택했습니다. ")

    # 3) 플레이 스타일 + 헤드사이즈/점수/패턴
    if "control" in styles:
        if isinstance(head_size, (int, float)) and head_size <= 100:
            parts.append("헤드 사이즈가 비교적 작아 컨트롤 위주의 플레이에 유리한 구조입니다. ")
        if control_score >= power_score:
            parts.append("내부 평가에서 컨트롤 점수가 높게 나와 라인 공략에 강점을 보이는 라켓입니다. ")

    if "power" in styles:
        if isinstance(head_size, (int, float)) and head_size >= 100:
            parts.append("조금 더 넉넉한 헤드 사이즈로 스윗스팟이 넓어 힘을 실어 치기 쉬운 편입니다. ")
        if power_score >= control_score:
            parts.append("파워 계열 점수가 높아 깊게 밀어 넣는 스트로크에 강점을 보입니다. ")

    if "spin" in styles:
        if string_pattern and ("16x19" in string_pattern or "16x18" in string_pattern):
            parts.append("16x19 계열 스트링 패턴으로 스핀량을 확보하기 좋은 구조입니다. ")
        elif string_pattern:
            parts.append("스트링 패턴 특성을 기준으로 스핀 성능이 준수하게 평가된 라켓입니다. ")
        if spin_score >= power_score and spin_score >= control_score:
            parts.append("내부 평가에서 스핀 관련 점수가 상대적으로 높게 나왔습니다. ")

    # 4) 레벨 + 헤드사이즈
    if level in ("beginner", "intermediate"):
        if isinstance(head_size, (int, float)) and head_size >= 100:
            parts.append("헤드가 넓은 편이라 미스 히트에도 관대한 편으로, 초·중급 레벨에서 안정감을 주기 좋습니다. ")
    elif level in ("advanced", "expert"):
        if isinstance(head_size, (int, float)) and head_size <= 100:
            parts.append("상급자 기준으로 스윗스팟이 집중된 헤드 사이즈라 정교한 컨트롤 플레이에 적합합니다. ")

    # 5) 기본 근거
    if not parts:
        parts.append("손 크기, 통증 여부, 플레이 스타일과 라켓 스펙을 종합했을 때 내부 점수 상위권에 위치해 추천 목록에 포함되었습니다. ")

    # 너무 길어지지 않도록 앞쪽 설명 위주로 3~4개만 사용
    return " ".join(parts[:4])


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
        unstrung_weight = _get_attr(
            r, "unstrung_weight_g", _get_attr(r, "weight", None)
        )
        swingweight = _get_attr(r, "swingweight", None)
        stiffness_ra = _get_attr(r, "stiffness_ra", None)
        balance_type = _get_attr(r, "balance_type", None)  # 'HL', 'EB', 'HH'
        string_pattern = _get_attr(r, "string_pattern", None)

        # 기본 스코어 (내부 절대 점수)
        score = (
            power_score * power_w
            + control_score * control_w
            + spin_score * spin_w
            + comfort_score * comfort_w
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

        # 추천 이유 생성 
        reason_text = _build_racket_reason(
            hand_profile,
            style_profile,
            head_size=head_size,
            unstrung_weight=unstrung_weight,
            swingweight=swingweight,
            stiffness_ra=stiffness_ra,
            string_pattern=string_pattern,
            power_score=power_score,
            control_score=control_score,
            spin_score=spin_score,
        )

        # 여기 단계의 score는 "내부 절대 점수"
        candidates.append(
            {
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
                "score": float(score),  # rawScore 후보
                "reason": reason_text,
                "url":r.url,
            }
        )

    if not candidates:
        string_rec = _compute_string_recommendation(hand_profile, style_profile)
        return {
            "rackets": [],
            "string": string_rec,
        }

    # 점수순 정렬 후 상위 5개 선택 (여기까지는 절대 점수 기준)
    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:5]

    # === 정규화: 1등을 100점으로 맞추고 나머지는 비율로 환산 ===
    max_score = candidates[0]["score"] if candidates and candidates[0]["score"] else 0.0

    if max_score > 0:
        for c in candidates:
            raw = float(c["score"])
            normalized = round(raw / max_score * 100.0, 1)
            c["rawScore"] = raw            # 내부 절대 점수 보존
            c["score"] = normalized        # UI에서 사용할 정규화 점수
            c["normalizedScore"] = normalized  # 명시적인 필드도 함께 제공
    else:
        # 모든 점수가 0 이하인 비정상 케이스 방어
        for c in candidates:
            raw = float(c["score"])
            c["rawScore"] = raw
            c["score"] = 0.0
            c["normalizedScore"] = 0.0

    string_rec = _compute_string_recommendation(hand_profile, style_profile)

    return {
        "rackets": candidates,
        "string": string_rec,
    }
