# services/playstyle_service.py

def build_playstyle_profile(survey: dict) -> dict:
    """
    설문 데이터를 바탕으로 플레이 스타일 프로파일을 만든다.

    기대 입력 (recommend.js에서 보내는 구조 기준):
    {
        "level": "beginner|intermediate|advanced|expert",
        "pain": "none|sometimes|often",
        "swing": "slow|normal|fast",
        "styles": ["power", "control", "spin"],
        "stringTypePreference": "auto|poly|multi"
    }
    """
    survey = survey or {}

    level = survey.get("level") or None
    pain = survey.get("pain") or None
    swing = survey.get("swing") or None
    styles = survey.get("styles") or []
    string_pref = survey.get("stringTypePreference") or "auto"

    # 레벨 → 숫자 점수
    level_map = {
        "beginner": 1,
        "intermediate": 2,
        "advanced": 3,
        "expert": 4,
    }
    level_score = level_map.get(level, 2)

    # 기본 가중치
    power_weight = 1.0
    control_weight = 1.0
    spin_weight = 1.0
    comfort_weight = 1.0

    # 스타일 선택 반영
    if "power" in styles:
        power_weight += 0.7
    if "control" in styles:
        control_weight += 0.7
    if "spin" in styles:
        spin_weight += 0.7

    # 스윙 속도 반영
    if swing == "fast":
        power_weight += 0.3
    elif swing == "slow":
        control_weight += 0.3

    # 통증 여부 반영
    if pain == "often":
        comfort_weight += 1.0
        power_weight -= 0.2
        spin_weight -= 0.2
    elif pain == "sometimes":
        comfort_weight += 0.5

    # 무게 선호 (추측입니다)
    weight_pref = "medium"
    if level_score <= 2 or pain == "often":
        weight_pref = "light"
    elif level_score >= 3 and pain == "none":
        weight_pref = "heavy"

    # 문자열 플래그도 같이 보관
    style_power = "power" in styles
    style_control = "control" in styles
    style_spin = "spin" in styles

    return {
        "level": level,
        "levelScore": level_score,
        "swing": swing,
        "pain": pain,
        "styles": styles,
        "stylePower": style_power,
        "styleControl": style_control,
        "styleSpin": style_spin,
        "stringTypePreference": string_pref,
        "powerWeight": power_weight,
        "controlWeight": control_weight,
        "spinWeight": spin_weight,
        "comfortWeight": comfort_weight,
        "weightPreference": weight_pref,
    }
