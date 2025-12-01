# services/recommend_service.py

from services.hand_profile_service import build_hand_profile
from services.playstyle_service import build_playstyle_profile
from services.racket_matching_service import match_rackets


def recommend_rackets_from_metrics(payload: dict) -> dict:
    """
    hand_api.py 에서 호출하는 최종 추천 함수.
    손 분석 결과 + 설문 데이터를 기반으로 전체 로직을 실행.
    """
    hand_metrics = payload.get("handMetrics")
    survey = payload.get("survey") or {}

    hand_profile = build_hand_profile(hand_metrics)
    style_profile = build_playstyle_profile(survey)

    match = match_rackets(hand_profile, style_profile)

    return {
        "handProfile": hand_profile,
        "styleProfile": style_profile,
        "recommended": match,
    }
