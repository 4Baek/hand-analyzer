import cv2
import mediapipe as mp
import math


def _dist(px1, px2):
    return math.sqrt((px1[0] - px2[0]) ** 2 + (px1[1] - px2[1]) ** 2)


def analyze_hand(image_path, capture_distance_cm=None, capture_device=None):
    """
    손 이미지에서 길이/너비/손가락 비율/손 크기 구분 등을 계산한다.

    - handLength / handWidth : 손 크기 '지수' (대략 500~900 근처 값이 나오도록 스케일링, 추측입니다)
    - handLengthMm / handWidthMm : mm 단위 추정값 (추측입니다)
    - handLengthCm / handWidthCm : cm 단위 추정값 (추측입니다)
    - fingerRatios : [검지/중지, 약지/중지] 길이 비율
    - handSizeCategory : 'SMALL' / 'MEDIUM' / 'LARGE'
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

    # 길이: 손목(0) ~ 중지 MCP(9)
    p0 = to_px(hand.landmark[0])
    p9 = to_px(hand.landmark[9])
    # 너비: 검지 MCP(5) ~ 새끼 MCP(17)
    p5 = to_px(hand.landmark[5])
    p17 = to_px(hand.landmark[17])

    length_px = _dist(p0, p9)
    width_px = _dist(p5, p17)

    # 손가락 길이 (검지, 중지, 약지)
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

    # px → cm 스케일 (촬영거리 반영, 완전한 물리 모델이 아니라 경험적 추정입니다)
    # 기본값은 손이 화면의 1/3~1/2 정도를 차지한다고 가정.
    base_scale_cm_per_px = 0.026  # 추측값
    if capture_distance_cm:
        # 거리가 멀수록 픽셀당 cm가 커지도록 약간 조정 (추측입니다)
        base_scale_cm_per_px = 0.018 + 0.00025 * float(capture_distance_cm)

    length_cm = length_px * base_scale_cm_per_px
    width_cm = width_px * base_scale_cm_per_px

    length_mm = length_cm * 10.0
    width_mm = width_cm * 10.0

    # UI에서 쓰는 '지수' 값: mm를 기반으로 500~900 근처가 나오게 스케일링 (추측입니다)
    # 예: 180mm → 720
    score_factor = 4.0
    length_score = length_mm * score_factor
    width_score = width_mm * score_factor

    # 손 크기 구분
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
        "captureDistanceCm": float(capture_distance_cm) if capture_distance_cm else None,
    }

    return result
