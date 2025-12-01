import cv2
import mediapipe as mp


def analyze_hand(image_path, capture_distance_cm=None, capture_device=None):
    """
    손의 길이/너비/비율 등을 계산하는 함수.
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
        return int(lm.x * w), int(lm.y * h)

    p0 = to_px(hand.landmark[0])
    p9 = to_px(hand.landmark[9])
    p5 = to_px(hand.landmark[5])
    p17 = to_px(hand.landmark[17])

    hand_length_px = ((p9[0] - p0[0]) ** 2 + (p9[1] - p0[1]) ** 2) ** 0.5
    hand_width_px = ((p17[0] - p5[0]) ** 2 + (p17[1] - p5[1]) ** 2) ** 0.5

    scale_factor = 0.026  # 대략적 기본값
    if capture_distance_cm:
        scale_factor = 0.015 + (0.0002 * capture_distance_cm)

    return {
        "handLength": round(hand_length_px * scale_factor, 2),
        "handWidth": round(hand_width_px * scale_factor, 2),
        "captureDevice": capture_device,
    }
