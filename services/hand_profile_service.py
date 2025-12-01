# services/hand_profile_service.py

def build_hand_profile(metrics: dict) -> dict:
    """
    손 분석 결과(JSON)를 바탕으로 손 프로파일을 생성한다.

    입력 예시 (analyze_hand에서 내려오는 값):
    - handLength / handWidth : 상대 지수
    - handLengthMm / handWidthMm : mm 단위 추정값
    - handSizeCategory : 'SMALL' / 'MEDIUM' / 'LARGE'
    - fingerRatios : [검지/중지, 약지/중지]
    """
    if not metrics:
        return {"handExists": False}

    length_score = metrics.get("handLength")
    width_score = metrics.get("handWidth")

    length_mm = metrics.get("handLengthMm")
    width_mm = metrics.get("handWidthMm")
    size_category = metrics.get("handSizeCategory")
    finger_ratios = metrics.get("fingerRatios") or []

    # handLengthMm가 없고, handLength 지수만 있다면 대략 환산 (추측입니다)
    if length_mm is None and isinstance(length_score, (int, float)):
        length_mm = length_score / 4.0  # 위 analyze_hand와 동일 스케일
    if width_mm is None and isinstance(width_score, (int, float)):
        width_mm = width_score / 4.0

    # 손 크기 등급이 비어 있으면 길이 기반으로 다시 계산
    if size_category is None and isinstance(length_mm, (int, float)):
        if length_mm < 170:
            size_category = "SMALL"
        elif length_mm < 190:
            size_category = "MEDIUM"
        else:
            size_category = "LARGE"

    # 그립 사이즈 추정 (L1/L2/L3, 추측입니다)
    grip_size_label = None
    if isinstance(length_mm, (int, float)):
        if length_mm < 175:
            grip_size_label = "L1"
        elif length_mm < 190:
            grip_size_label = "L2"
        else:
            grip_size_label = "L3"

    # 손가락 비율 기반 손 타입 (추측입니다)
    hand_type = None
    if len(finger_ratios) >= 2:
        idx_ratio, ring_ratio = finger_ratios[0], finger_ratios[1]
        avg = (idx_ratio + ring_ratio) / 2.0
        if avg < 0.97:
            hand_type = "compact"  # 상대적으로 짧은 손가락
        elif avg > 1.03:
            hand_type = "long"     # 길쭉한 손가락
        else:
            hand_type = "average"

    return {
        "handExists": True,
        "handLengthScore": length_score,
        "handWidthScore": width_score,
        "handLengthMm": length_mm,
        "handWidthMm": width_mm,
        "handSizeCategory": size_category,              # 'SMALL' / 'MEDIUM' / 'LARGE'
        "sizeGroup": size_category.lower() if size_category else None,  # small/medium/large
        "gripSizeLabel": grip_size_label,               # L1/L2/L3
        "fingerRatios": finger_ratios,
        "handType": hand_type,
    }
