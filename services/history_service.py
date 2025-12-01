# services/history_service.py

import json
from typing import Optional, List, Dict
from db_config import db, HandMetrics, SurveyResponse, RecommendationLog


# ----------------------------------------------------------------------
# 1) 손 분석 결과 저장
# ----------------------------------------------------------------------
def save_hand_metrics_from_result(
    analysis_result: dict,
) -> HandMetrics:
    """
    hand_utils.analyze_hand() 결과 dict를 받아 hand_metrics 테이블에 저장한다.

    analysis_result 예시:
    {
        "handLength": 720.0,
        "handWidth": 620.0,
        "handLengthMm": 180.0,
        "handWidthMm": 155.0,
        "handSizeCategory": "MEDIUM",
        "fingerRatios": [0.98, 1.02],
        "captureDevice": "iphone",
        "captureDistanceCm": 35.0,
        ...
    }
    """
    if not analysis_result:
        raise ValueError("analysis_result is empty")

    hand_length_mm = analysis_result.get("handLengthMm")
    hand_width_mm = analysis_result.get("handWidthMm")
    hand_length_score = analysis_result.get("handLength")
    hand_width_score = analysis_result.get("handWidth")
    size_category = analysis_result.get("handSizeCategory") or "MEDIUM"

    finger_ratios = analysis_result.get("fingerRatios") or []
    capture_device = analysis_result.get("captureDevice")
    capture_distance_cm = analysis_result.get("captureDistanceCm")

    hm = HandMetrics(
        hand_length_mm=hand_length_mm,
        hand_width_mm=hand_width_mm,
        hand_length_score=hand_length_score,
        hand_width_score=hand_width_score,
        hand_size_category=size_category,
        finger_ratios_json=json.dumps(finger_ratios, ensure_ascii=False),
        capture_device=capture_device,
        capture_distance_cm=capture_distance_cm,
        raw_result_json=json.dumps(analysis_result, ensure_ascii=False),
    )
    db.session.add(hm)
    db.session.commit()
    return hm


# ----------------------------------------------------------------------
# 2) 설문 응답 저장
# ----------------------------------------------------------------------
def save_survey_response_from_payload(
    survey_payload: dict,
) -> SurveyResponse:
    """
    recommend.js에서 올리는 설문 payload를 받아 survey_responses에 저장.

    기대 payload (playstyle_service 참고):
    {
        "level": "beginner|intermediate|advanced|expert",
        "pain": "none|sometimes|often",
        "swing": "slow|normal|fast",
        "styles": ["power", "control", "spin"],
        "stringTypePreference": "auto|poly|multi",
        ...
    }
    """
    survey_payload = survey_payload or {}

    styles = survey_payload.get("styles") or []

    sr = SurveyResponse(
        level=survey_payload.get("level"),
        pain=survey_payload.get("pain"),
        swing=survey_payload.get("swing"),
        string_type_preference=survey_payload.get("stringTypePreference"),
        styles_json=json.dumps(styles, ensure_ascii=False),
        extra_payload_json=json.dumps(survey_payload, ensure_ascii=False),
    )
    db.session.add(sr)
    db.session.commit()
    return sr


# ----------------------------------------------------------------------
# 3) 추천 로그 저장
# ----------------------------------------------------------------------
def log_recommendations(
    *,
    hand_metrics: Optional[HandMetrics],
    survey_response: Optional[SurveyResponse],
    hand_profile: dict,
    style_profile: dict,
    racket_candidates: List[Dict],
    string_rec: Dict,
    algorithm_version: str = "v1",
) -> List[RecommendationLog]:
    """
    match_rackets 결과를 recommendation_logs에 저장.

    racket_candidates 예시 (racket_matching_service 반환 구조):
    [
        {
            "id": 1,
            "name": "...",
            "brand": "...",
            "score": 92.5,
            ...
        },
        ...
    ]

    string_rec 예시 (_compute_string_recommendation 반환 구조):
    {
        "tensionMainKg": 23.0,
        "tensionMainLbs": 51,
        "stringType": "poly",
        "stringLabel": "폴리 계열 스트링",
        "reason": "...",
    }
    """
    logs: List[RecommendationLog] = []

    hand_profile_json = json.dumps(hand_profile, ensure_ascii=False)
    style_profile_json = json.dumps(style_profile, ensure_ascii=False)

    string_type = string_rec.get("stringType")
    string_label = string_rec.get("stringLabel")
    tension_kg = string_rec.get("tensionMainKg")
    tension_lbs = string_rec.get("tensionMainLbs")
    reason = string_rec.get("reason")

    for idx, racket in enumerate(racket_candidates, start=1):
        racket_id = racket.get("id")

        # 정규화 이전의 내부 점수(rawScore)가 있으면 그 값을 우선 저장,
        # 없으면 기존 score(정규화 or 절대값)를 그대로 사용.
        raw_score = racket.get("rawScore")
        score = raw_score if raw_score is not None else racket.get("score")

        log = RecommendationLog(
            hand_metrics_id=hand_metrics.id if hand_metrics else None,
            survey_response_id=survey_response.id if survey_response else None,
            racket_id=racket_id,
            recommended_string_type=string_type,
            recommended_string_label=string_label,
            recommended_tension_main_kg=tension_kg,
            recommended_tension_main_lbs=tension_lbs,
            recommendation_score=score,
            rank_in_result=idx,
            algorithm_version=algorithm_version,
            rationale=reason,
            hand_profile_json=hand_profile_json,
            style_profile_json=style_profile_json,
        )
        db.session.add(log)
        logs.append(log)

    db.session.commit()
    return logs
