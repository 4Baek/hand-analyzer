import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands


def analyze_hand(image_path: str):
  """
  이미지를 읽어서 손 길이/너비/손가락 비율을 계산.
  인식 실패 시 None 반환.
  """
  image = cv2.imread(image_path)
  if image is None:
      return None

  image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

  with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
      result = hands.process(image_rgb)

      # MediaPipe Hands: multi_hand_landmarks 사용
      if not result.multi_hand_landmarks:
          return None

      landmarks = result.multi_hand_landmarks[0].landmark

      wrist = landmarks[0]
      middle_tip = landmarks[12]
      thumb_tip = landmarks[4]
      pinky_tip = landmarks[20]

      # 손 길이 (손목 ~ 중지 끝) / 손 너비 (엄지 ~ 새끼)
      hand_length = np.linalg.norm(
          np.array([wrist.x, wrist.y]) - np.array([middle_tip.x, middle_tip.y])
      )
      hand_width = np.linalg.norm(
          np.array([thumb_tip.x, thumb_tip.y]) - np.array([pinky_tip.x, pinky_tip.y])
      )

      # 손가락 비율 예시: 검지/중지, 약지/중지
      index_to_middle = landmarks[8].y / landmarks[12].y
      ring_to_middle = landmarks[16].y / landmarks[12].y

      return {
          "handLength": round(hand_length * 1000, 2),
          "handWidth": round(hand_width * 1000, 2),
          "fingerRatios": [
              round(index_to_middle, 2),
              round(ring_to_middle, 2),
          ],
      }
