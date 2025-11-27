import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands


def analyze_hand(image_path, capture_distance_cm=None, capture_device=None):
    """
    이미지를 읽어서 손 길이/너비/손가락 비율을 계산.
    - handLength / handWidth: MediaPipe 좌표 기반 상대 크기 점수
    - handLengthMm / handWidthMm: 성인 평균 손 크기를 기준으로 한 추정값 (추측입니다)
    - capture_distance_cm가 있으면 30cm 기준으로 간단히 보정 (추측입니다)
    인식 실패 시 None 반환.
    """
    image = cv2.imread(image_path)
    if image is None:
        return None

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
        result = hands.process(image_rgb)

        if not result.multi_hand_landmarks:
            return None

        landmarks = result.multi_hand_landmarks[0].landmark

        # 주요 포인트
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        thumb_tip = landmarks[4]
        pinky_tip = landmarks[20]

        # 정규화 좌표 기준 거리 (0~1 사이)
        hand_length_norm = np.linalg.norm(
            np.array([wrist.x, wrist.y]) - np.array([middle_tip.x, middle_tip.y])
        )
        hand_width_norm = np.linalg.norm(
            np.array([thumb_tip.x, thumb_tip.y]) - np.array([pinky_tip.x, pinky_tip.y])
        )

        # 기존 점수 스케일 유지 (대략 500~900대, 추측입니다)
        hand_length_score = hand_length_norm * 1000.0
        hand_width_score = hand_width_norm * 1000.0

        # 손가락 비율 예시: 검지/중지, 약지/중지
        index_to_middle = landmarks[8].y / landmarks[12].y
        ring_to_middle = landmarks[16].y / landmarks[12].y

        # -----------------------------
        # 손 길이/너비 (mm / cm) 추정
        # -----------------------------
        # 기준 가정 (추측입니다):
        #  - handLengthScore 650 ≒ 손 길이 185mm
        #  - handWidthScore  650 ≒ 손 너비  85mm
        #  - 촬영 거리 기준 30cm
        base_length_mm = hand_length_score * (185.0 / 650.0)
        base_width_mm = hand_width_score * (85.0 / 650.0)

        # 촬영 거리 보정 (거리 ∝ 실제 길이, 단순 비례 보정 – 추측입니다)
        scale = 1.0
        if capture_distance_cm and capture_distance_cm > 0:
            # 30cm를 기준으로, 더 멀면 길이↑, 더 가까우면 길이↓
            scale = capture_distance_cm / 30.0

        length_mm = base_length_mm * scale
        width_mm = base_width_mm * scale

        hand_length_mm = round(length_mm, 1)
        hand_width_mm = round(width_mm, 1)
        hand_length_cm = round(hand_length_mm / 10.0, 1)
        hand_width_cm = round(hand_width_mm / 10.0, 1)

        # 손 크기 구분 (SMALL / MEDIUM / LARGE)
        avg_score = (hand_length_score + hand_width_score) / 2.0
        if avg_score <= 550:
            hand_size_category = "SMALL"
        elif avg_score >= 750:
            hand_size_category = "LARGE"
        else:
            hand_size_category = "MEDIUM"

        return {
            # 상대 점수
            "handLength": round(hand_length_score, 2),
            "handWidth": round(hand_width_score, 2),
            "fingerRatios": [
                round(index_to_middle, 2),
                round(ring_to_middle, 2),
            ],
            # mm / cm 추정값
            "handLengthMm": hand_length_mm,
            "handLengthCm": hand_length_cm,
            "handWidthMm": hand_width_mm,
            "handWidthCm": hand_width_cm,
            "handSizeCategory": hand_size_category,
            # 참고용 메타
            "captureDistance": capture_distance_cm,
        }
