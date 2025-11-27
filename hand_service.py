# hand_service.py
from typing import Dict, List, Any, Optional

from db_config import Racket


def _size_is_big(hand_length: Optional[float], hand_width: Optional[float]) -> bool:
    """기존 로직을 유지하기 위한 헬퍼: 평균이 800 이상이면 큰 손으로 간주."""
    if hand_length is None or hand_width is None:
        return False
    try:
        return (float(hand_length) + float(hand_width)) / 2.0 > 800.0
    except (TypeError, ValueError):
        return False


def _classify_hand_size(
    hand_length: Optional[float],
    hand_width: Optional[float],
) -> Optional[str]:
    """
    손 크기를 SMALL / MEDIUM / LARGE 로 대략 분류.
    hand_utils.analyze_hand 결과(대략 500~900대 값)를 기준으로 단순 구간화.
    """
    if hand_length is None or hand_width is None:
        return None

    avg = (float(hand_length) + float(hand_width)) / 2.0

    # 700 이상: 큰 손, 550 이하: 작은 손 정도로 사용 (추측입니다)
    if avg <= 550:
        return "SMALL"
    if avg >= 750:
        return "LARGE"
    return "MEDIUM"


def _normalize_survey(raw: Dict) -> Dict:
    """프론트엔드에서 넘어온 survey 객체를 정규화."""
    if not isinstance(raw, dict):
        return {}

    styles = raw.get("styles") or []
    if isinstance(styles, str):
        # 혹시 콤마 구분 문자열로 올 경우
        styles = [s.strip() for s in styles.split(",") if s.strip()]

    return {
        "level": raw.get("level") or None,  # beginner / intermediate / advanced / expert
        "pain": raw.get("pain") or None,  # none / sometimes / often
        "swing": raw.get("swing") or None,  # slow / normal / fast
        "styles": styles,
        "string_type_preference": raw.get("stringTypePreference") or "auto",
    }


def _calc_racket_score(
    racket: Racket,
    hand_size: Optional[str],
    survey: Dict,
    finger_ratios: Optional[List[float]],
) -> float:
    """
    라켓 하나에 대한 적합도 점수를 계산.
    - power/control/spin 점수 + 설문 + 약간의 태그 보정.
    """
    # 1) 스타일에 따른 P/C/S 가중치
    styles: List[str] = survey.get("styles") or []
    w_power = 1.0
    w_control = 1.0
    w_spin = 1.0

    if "power" in styles:
        w_power += 0.7
    if "control" in styles:
        w_control += 0.7
    if "spin" in styles:
        w_spin += 0.7

    w_sum = w_power + w_control + w_spin
    w_power /= w_sum
    w_control /= w_sum
    w_spin /= w_sum

    p = float(getattr(racket, "power", 5) or 5)
    c = float(getattr(racket, "control", 5) or 5)
    s = float(getattr(racket, "spin", 5) or 5)

    base_score = w_power * p + w_control * c + w_spin * s

    # 2) 손 크기 / 무게에 따른 보정
    extra = 0.0
    weight_val = getattr(racket, "weight", None)
    try:
        weight_val = float(weight_val) if weight_val is not None else None
    except (TypeError, ValueError):
        weight_val = None

    swing = survey.get("swing")
    pain = survey.get("pain")

    # 손이 작은데 무겁고, 스윙 느리고, 통증 있는 경우에는 감점 (추측입니다)
    if hand_size == "SMALL" and weight_val is not None:
        if weight_val >= 7:  # 상대적으로 무거운 편이라고 가정 (추측입니다)
            extra -= 0.4
    if swing == "slow" and weight_val is not None and weight_val >= 7:
        extra -= 0.3
    if pain in ("sometimes", "often") and weight_val is not None and weight_val >= 7:
        extra -= 0.5

    # 손이 크고 스윙이 빠르면 무거운 라켓 선호 보너스
    if hand_size == "LARGE" and swing == "fast" and weight_val is not None and weight_val >= 7:
        extra += 0.5

    # 3) 태그 기반 보정
    tags = getattr(racket, "tags", "") or ""
    if "스핀" in tags and "spin" in styles:
        extra += 0.5
    if "파워" in tags and "power" in styles:
        extra += 0.4
    if "컨트롤" in tags and "control" in styles:
        extra += 0.4

    # 손가락 비율을 이용한 스핀 성향 보정 (기존 로직 느낌 유지)
    if isinstance(finger_ratios, list) and len(finger_ratios) >= 2:
        index_ratio, ring_ratio = finger_ratios[0], finger_ratios[1]
        try:
            if index_ratio < ring_ratio and "스핀" in tags:
                extra += 0.5
        except Exception:
            pass

    return round(base_score + extra, 2)


def _recommend_string(
    hand_length: Optional[float],
    hand_width: Optional[float],
    survey: Dict,
) -> Dict[str, Any]:
    """
    손 크기 + 설문을 활용해 스트링 타입 / 텐션 추천.
    수치는 일반적인 테니스 스트링 가이드를 참고한 단순 규칙 기반이며, 개인차가 큰 영역이라 추측입니다.
    """
    base_tension_lbs = 48.0

    swing = survey.get("swing")
    pain = survey.get("pain")
    level = survey.get("level")
    preferred_type = survey.get("string_type_preference") or "auto"

    # 1) 스윙 속도 보정
    if swing == "slow":
        base_tension_lbs -= 4
    elif swing == "fast":
        base_tension_lbs += 4

    # 2) 통증 보정
    if pain == "sometimes":
        base_tension_lbs -= 2
    elif pain == "often":
        base_tension_lbs -= 4

    # 3) 레벨 보정
    if level in ("beginner",):
        base_tension_lbs -= 2
    elif level in ("advanced", "expert"):
        base_tension_lbs += 2

    # 4) 손 크기 보정
    hand_size = _classify_hand_size(hand_length, hand_width)
    if hand_size == "SMALL":
        base_tension_lbs -= 1
    elif hand_size == "LARGE":
        base_tension_lbs += 1

    # 안전 범위 클램프 (보통 40~56lbs 정도 많이 사용)
    if base_tension_lbs < 40:
        base_tension_lbs = 40
    if base_tension_lbs > 56:
        base_tension_lbs = 56

    # 문자열 타입 결정
    if preferred_type == "auto":
        # 자동 모드: 통증/스윙/레벨 기반으로 폴리 vs 멀티 선택 (추측입니다)
        if pain in ("sometimes", "often"):
            string_type = "multi"
        elif swing == "fast" and level in ("intermediate", "advanced", "expert"):
            string_type = "poly"
        else:
            string_type = "multi"
    else:
        string_type = preferred_type

    if string_type == "poly":
        string_label = "폴리 스트링"
    elif string_type == "multi":
        string_label = "멀티필라멘트 스트링"
    else:
        string_label = "기본 합성 스트링"

    tension_main_lbs = round(base_tension_lbs)
    tension_cross_lbs = tension_main_lbs  # 처음 버전은 메인/크로스 동일
    tension_main_kg = round(tension_main_lbs / 2.20462, 1)
    tension_cross_kg = tension_main_kg

    reason_parts: List[str] = []

    if swing == "slow":
        reason_parts.append("스윙이 비교적 느린 편이라 파워를 돕기 위해 텐션을 낮게 설정했습니다.")
    elif swing == "fast":
        reason_parts.append("스윙이 빠른 편이라 컨트롤을 돕기 위해 텐션을 다소 높게 설정했습니다.")

    if pain in ("sometimes", "often"):
        reason_parts.append(
            "팔·손목 통증을 줄이기 위해 텐션을 전체적으로 낮추고, 충격이 적은 스트링 타입을 우선했습니다."
        )

    if hand_size == "SMALL":
        reason_parts.append("손 크기가 작은 편이라 부담을 줄이는 방향으로 텐션을 조금 낮췄습니다.")
    elif hand_size == "LARGE":
        reason_parts.append("손 크기가 큰 편이라 약간 높은 텐션도 무리가 없다고 판단했습니다.")

    if not reason_parts:
        reason_parts.append("일반적인 중간값 기준에서 설문 답변을 반영해 텐션을 조정한 결과입니다. (추측입니다)")

    reason_text = " ".join(reason_parts)
    if "추측입니다" not in reason_text:
        reason_text += " (일반적인 가이드를 기반으로 한 추측입니다)"

    return {
        "tensionMainLbs": tension_main_lbs,
        "tensionCrossLbs": tension_cross_lbs,
        "tensionMainKg": tension_main_kg,
        "tensionCrossKg": tension_cross_kg,
        "stringType": string_type,
        "stringLabel": string_label,
        "reason": reason_text,
    }


def recommend_rackets_from_metrics(metrics: Dict) -> Dict[str, Any]:
    """
    손 길이/너비/손가락 비율 + 설문(survey)을 이용해서
    - 라켓 추천 목록
    - 스트링 / 텐션 추천
    을 함께 반환하는 함수.

    /recommend-rackets 라우트에서는 이 함수만 호출하면 됨.
    """
    if not isinstance(metrics, dict):
        metrics = {}

    hand_length = metrics.get("handLength")
    hand_width = metrics.get("handWidth")
    finger_ratios = metrics.get("fingerRatios") or []

    raw_survey = metrics.get("survey") or {}
    survey = _normalize_survey(raw_survey)

    hand_size = _classify_hand_size(hand_length, hand_width)

    # 1) 라켓 적합도 계산
    results: List[Dict[str, Any]] = []

    for r in Racket.query.all():
        score = _calc_racket_score(
            racket=r,
            hand_size=hand_size,
            survey=survey,
            finger_ratios=finger_ratios,
        )
        data = r.to_dict()
        data["score"] = score
        results.append(data)

    results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    top_rackets = results[:5]

    # 2) 스트링 추천 계산
    string_info = _recommend_string(hand_length, hand_width, survey)

    return {
        "rackets": top_rackets,
        "string": string_info,
        "handProfile": {
            "handSize": hand_size,
        },
    }
