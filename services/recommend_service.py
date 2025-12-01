# services/recommend_service.py

import json
from typing import Dict, Any

from services.hand_profile_service import build_hand_profile
from services.playstyle_service import build_playstyle_profile
from services.racket_matching_service import match_rackets
from services.history_service import (
    save_survey_response_from_payload,
    log_recommendations,
)
from db_config import HandMetrics, SurveyResponse, db


def _load_hand_metrics_by_id(hand_metrics_id):
    if not hand_metrics_id:
        return None, None

    hm = HandMetrics.query.get(hand_metrics_id)
    if not hm:
        return None, None

    metrics_dict = hm.to_dict()
    return hm, metrics_dict


def _load_survey_response_by_id(survey_response_id):
    if not survey_response_id:
        return None, None

    sr = SurveyResponse.query.get(survey_response_id)
    if not sr:
        return None, None

    survey_dict = sr.to_dict()
    return sr, survey_dict


def recommend_rackets_from_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    /recommend-rackets 엔드포인트에서 사용하는 최종 추천 함수.

    지원 payload 예시:

    1) 기존 구조 (프론트에서 직접 메트릭/설문 전송)
       {
         "handLength": ...,
         "handWidth": ...,
         "handLengthMm": ...,
         "handWidthMm": ...,
         "handSizeCategory": "...",
         "fingerRatios": [...],
         "survey": { ... playstyle payload ... }
       }

    2) DB 기반 구조
       {
         "handMetricsId": 123,         # 옵션
         "surveyResponseId": 456,      # 옵션
         "survey": { ... }             # 옵션 (없으면 surveyResponseId 기반)
       }

    - handMetricsId/surveyResponseId가 있으면 DB에서 우선 로드
    - survey payload가 함께 오면, DB 설문 대신 그걸 기반으로 profile 생성
      (단, 별도로 저장하고 싶으면 별도의 API에서 save_survey_response_from_payload 사용)
    """
    payload = payload or {}

    # ---- 1) 손 메트릭 취합 (DB 우선, 없으면 payload 상단 키들) ----
    hand_metrics_id = payload.get("handMetricsId")
    hand_obj = None
    hand_metrics_dict = None

    if hand_metrics_id:
        hand_obj, hand_metrics_dict = _load_hand_metrics_by_id(hand_metrics_id)

    if hand_metrics_dict is None:
        # 1-1) handMetrics 키가 있으면 그걸 사용
        hand_metrics = payload.get("handMetrics")
        if isinstance(hand_metrics, dict):
            hand_metrics_dict = hand_metrics
        else:
            # 1-2) 없으면 survey를 제외한 나머지 상위 키들을 메트릭스로 간주
            hand_metrics_dict = {
                k: v for k, v in payload.items()
                if k not in ("survey", "handMetricsId", "surveyResponseId")
            }

    # ---- 2) 설문 취합 (DB 설문 vs payload survey) ----
    survey_response_id = payload.get("surveyResponseId")
    survey_obj = None
    survey_dict = None

    if survey_response_id:
        survey_obj, survey_dict = _load_survey_response_by_id(survey_response_id)

    if payload.get("survey") is not None:
        # payload 안의 survey가 있으면, DB에서 가져온 값보다 우선한다.
        survey_dict = payload.get("survey") or {}

    survey_dict = survey_dict or {}

    # ---- 3) profile 생성 ----
    hand_profile = build_hand_profile(hand_metrics_dict)
    style_profile = build_playstyle_profile(survey_dict)

    # ---- 4) 라켓/스트링 매칭 ----
    match = match_rackets(hand_profile, style_profile)
    rackets = match.get("rackets", [])
    string_rec = match.get("string") or {}

    # ---- 5) 추천 로그 기록 ----
    #    - 설문 payload만 있고 SurveyResponse row는 없을 수 있으므로
    #      여기서 새 row로 저장할지 여부는 정책에 따라 선택.
    #      여기서는 "surveyResponseId가 없고, survey payload가 있으면 새로 저장"으로 가정.
    if survey_obj is None and survey_dict:
        survey_obj = save_survey_response_from_payload(survey_dict)

    # hand_obj가 아직 없고, hand_metrics_dict가 있고, 그게 analyze_hand 결과라면
    # 여기서 저장할 수도 있지만, 보통은 /scan-hand에서 저장하고 id만 써도 충분해서
    # 이 부분은 선택적으로 남겨둔다. 필요하면 정책에 따라 활성화.
    # 예시:
    # if hand_obj is None and hand_metrics_dict and hand_metrics_dict.get("handLengthMm"):
    #     from services.history_service import save_hand_metrics_from_result
    #     hand_obj = save_hand_metrics_from_result(hand_metrics_dict)

    log_recommendations(
        hand_metrics=hand_obj,
        survey_response=survey_obj,
        hand_profile=hand_profile,
        style_profile=style_profile,
        racket_candidates=rackets,
        string_rec=string_rec,
        algorithm_version="v1",
    )

    # 프론트 recommend.js는 data.rackets / data.string을 기대하므로
    # recommended 안에 넣지 말고 최상위로 풀어서 반환
    return {
        "handProfile": hand_profile,
        "styleProfile": style_profile,
        "rackets": rackets,
        "string": string_rec,
    }
