import cv2
import mediapipe as mp
import math


def _dist(px1, px2):
    return math.sqrt((px1[0] - px2[0]) ** 2 + (px1[1] - px2[1]) ** 2)


# 촬영거리 기반 보정 상수
# 손 길이: 약 18.5cm / 손 너비: 약 16.5cm 를 기준으로
# 30cm / 40cm / 50cm 샷을 동시에 맞추도록 튜닝한 값입니다. (추측입니다)
C_LEN_CM_PER_PX_PER_CM = 0.0006555   # length_cm = C_LEN * length_px * distance_cm
C_WID_CM_PER_PX_PER_CM = 0.0007884   # width_cm  = C_WID * width_px  * distance_cm


def _length_distance_correction(distance_cm: float) -> float:
    """
    촬영 거리별 추가 길이 보정 계수.

    - 30cm : 약 0.902  (205mm → 185mm 근처로 내리기 위해)
    - 40cm : 1.0      (보정 없음, 기준 거리)
    - 30~40cm 사이는 선형 보간
    - 그 외(40 이상, 30 이하 영역 바깥)는 양 끝값으로 클램핑
    """
    d = float(distance_cm)

    # 30cm 이하에서는 항상 최소 계수 사용
    if d <= 30.0:
        return 0.902

    # 40cm 이상에서는 보정 없이 1.0 사용
    if d >= 40.0:
        return 1.0

    # 30~40cm 사이 선형 보간
    # d=30 → 0.902, d=40 → 1.0
    t = (d - 30.0) / 10.0  # 0~1
    return 0.902 + t * (1.0 - 0.902)


def analyze_hand(image_path, capture_distance_cm=None, capture_device=None):
    """
    손 이미지에서 길이/너비/손가락 비율/손 크기 구분 등을 계산한다.

    반환 값 예시:
    {
        "handLength": 720.0,        # 길이 지수 (mm 기반 스코어)
        "handWidth": 660.0,         # 너비 지수 (mm 기반 스코어)
        "handLengthMm": 185.0,      # 손 길이 추정값 (mm)
        "handLengthCm": 18.5,       # 손 길이 추정값 (cm)
        "handWidthMm": 165.0,       # 손 너비 추정값 (mm)
        "handWidthCm": 16.5,        # 손 너비 추정값 (cm)
        "fingerRatios": [0.91, 0.96],
        "handSizeCategory": "LARGE",
        "captureDevice": "...",
        "captureDistanceCm": 40.0,
    }
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.5,
    )
    results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    if not results.multi_hand_landmarks:
        return None

    hand = results.multi_hand_landmarks[0]
    h, w, _ = img.shape

    def to_px(lm):
        return (lm.x * w, lm.y * h)

    # ---------------------------------
    # 1) 기본 랜드마크에서 픽셀 길이 계산
    # ---------------------------------
    # 손 길이: 손목(0) ~ 중지 MCP(9)
    p0 = to_px(hand.landmark[0])
    p9 = to_px(hand.landmark[9])
    # 손 너비: 검지 MCP(5) ~ 새끼 MCP(17)
    p5 = to_px(hand.landmark[5])
    p17 = to_px(hand.landmark[17])

    length_px = _dist(p0, p9)
    width_px = _dist(p5, p17)

    # 손가락 길이 (검지, 중지, 약지) → 비율용
    p5_mcp = to_px(hand.landmark[5])
    p8_tip = to_px(hand.landmark[8])
    index_len_px = _dist(p5_mcp, p8_tip)

    p9_mcp = to_px(hand.landmark[9])
    p12_tip = to_px(hand.landmark[12])
    middle_len_px = _dist(p9_mcp, p12_tip)

    p13_mcp = to_px(hand.landmark[13])
    p16_tip = to_px(hand.landmark[16])
    ring_len_px = _dist(p13_mcp, p16_tip)

    finger_ratios = []
    if middle_len_px > 0:
        finger_ratios.append(index_len_px / middle_len_px)
        finger_ratios.append(ring_len_px / middle_len_px)

    # ---------------------------------
    # 2) px → cm 변환
    #    - 촬영거리(cm)가 들어온 경우:
    #         길이(cm) = C_LEN * length_px * distance_cm * length_corr
    #         너비(cm) = C_WID * width_px  * distance_cm
    #    - 촬영거리가 없으면 예전 방식(대략적인 값)으로만 계산
    # ---------------------------------
    if capture_distance_cm is not None:
        d = float(capture_distance_cm)

        length_cm = C_LEN_CM_PER_PX_PER_CM * length_px * d
        width_cm = C_WID_CM_PER_PX_PER_CM * width_px * d

        # 30cm에서 길이가 과대 측정되는 문제를 보정하기 위한 추가 계수
        length_corr = _length_distance_correction(d)
        length_cm *= length_corr
    else:
        # 거리 정보가 없을 때는 단순 비례(예전 스케일)만 사용
        base_scale_cm_per_px = 0.026
        length_cm = length_px * base_scale_cm_per_px
        width_cm = width_px * base_scale_cm_per_px

    length_mm = length_cm * 10.0
    width_mm = width_cm * 10.0

    # ---------------------------------
    # 3) UI용 지수 및 손 크기 구분
    # ---------------------------------
    # 지수: mm * 4 → 보통 500~900 사이
    score_factor = 4.0
    length_score = length_mm * score_factor
    width_score = width_mm * score_factor

    # 손 크기 구분 (길이 기준)
    size_category = None
    if length_mm:
        if length_mm < 170:
            size_category = "SMALL"
        elif length_mm < 190:
            size_category = "MEDIUM"
        else:
            size_category = "LARGE"

    result = {
        # 상대 지수
        "handLength": round(length_score, 1),
        "handWidth": round(width_score, 1),
        # 절대값 추정
        "handLengthMm": round(length_mm, 1),
        "handLengthCm": round(length_cm, 2),
        "handWidthMm": round(width_mm, 1),
        "handWidthCm": round(width_cm, 2),
        # 손가락 비율
        "fingerRatios": [round(r, 3) for r in finger_ratios] if finger_ratios else [],
        # 손 크기 등급
        "handSizeCategory": size_category,
        # 촬영 정보
        "captureDevice": capture_device,
        "captureDistanceCm": float(capture_distance_cm) if capture_distance_cm is not None else None,
    }

    return result
