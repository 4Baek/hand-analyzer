# services/recommend_service.py

from services.hand_profile_service import build_hand_profile
from services.playstyle_service import build_playstyle_profile
from services.racket_matching_service import match_rackets


def recommend_rackets_from_metrics(payload: dict) -> dict:
    """
    /recommend-rackets 엔드포인트에서 사용하는 최종 추천 함수.

    프런트에서 오는 payload 형태를 두 가지 모두 지원:
    1) { handMetrics: {...}, survey: {...} }
    2) { handLength: ..., handWidth: ..., ..., survey: {...} }  (현재 recommend.js 구조)
    """
    payload = payload or {}

    survey = payload.get("survey") or {}

    # 1) handMetrics 키가 있으면 그걸 우선 사용
    hand_metrics = payload.get("handMetrics")
    if not isinstance(hand_metrics, dict):
        # 2) 없으면 survey를 제외한 나머지 상위 키들을 메트릭스로 간주
        hand_metrics = {
            k: v for k, v in payload.items()
            if k != "survey"
        }

    hand_profile = build_hand_profile(hand_metrics)
    style_profile = build_playstyle_profile(survey)

    match = match_rackets(hand_profile, style_profile)

    # 프런트 recommend.js는 data.rackets / data.string을 기대하므로
    # recommended 안에 넣지 말고 최상위로 풀어서 반환
    return {
        "handProfile": hand_profile,
        "styleProfile": style_profile,
        "rackets": match.get("rackets", []),
        "string": match.get("string"),
    }
