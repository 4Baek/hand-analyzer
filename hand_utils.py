import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands

def analyze_hand(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("[❗] 이미지 읽기 실패: ", image_path)
        return None

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
        result = hands.process(image_rgb)

        # result가 None이거나 구조가 예상과 다를 경우 처리
        if not hasattr(result, 'multi_hand_landmarks') or not result.multi_hand_landmarks:
            print("[⚠️] 손 인식 실패 (landmarks 없음)")
            return None

        landmarks = result.multi_hand_landmarks[0].landmark
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        thumb_tip = landmarks[4]
        pinky_tip = landmarks[20]

        hand_length = np.linalg.norm(
            np.array([wrist.x, wrist.y]) - np.array([middle_tip.x, middle_tip.y])
        )
        hand_width = np.linalg.norm(
            np.array([thumb_tip.x, thumb_tip.y]) - np.array([pinky_tip.x, pinky_tip.y])
        )

        return {
            "handLength": round(hand_length * 1000, 1),
            "handWidth": round(hand_width * 1000, 1),
            "fingerRatios": {
                "indexToMiddle": round(landmarks[8].y / landmarks[12].y, 2),
                "ringToMiddle": round(landmarks[16].y / landmarks[12].y, 2)
            }
        }
