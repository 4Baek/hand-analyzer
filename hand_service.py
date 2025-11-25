# hand_service.py
from typing import Dict, List

from db_config import Racket


def _size_is_big(hand_length, hand_width) -> bool:
    if hand_length is None or hand_width is None:
        return False
    return (hand_length + hand_width) / 2.0 > 800


def recommend_rackets_from_metrics(metrics: Dict) -> List[Dict]:
    """
    손 길이/너비/손가락 비율을 이용해서 Racket 테이블에서 라켓을 고르고 점수를 계산.
    Flask 라우트에서는 이 함수만 호출하면 됨.
    """
    hand_length = metrics.get("handLength")
    hand_width = metrics.get("handWidth")
    finger_ratios = metrics.get("fingerRatios") or []

    query = Racket.query

    # 손 크기 기준 1차 필터
    size = None
    if hand_length is not None and hand_width is not None:
        size = (hand_length + hand_width) / 2.0

        if size < 600:
            query = query.filter(Racket.power >= 8)
        elif size > 800:
            query = query.filter(Racket.control >= 8)

    index_ratio = finger_ratios[0] if len(finger_ratios) > 0 else 1.0
    ring_ratio = finger_ratios[1] if len(finger_ratios) > 1 else 1.0

    rackets = query.all()

    results: List[Dict] = []
    for r in rackets:
        base_score = (r.power + r.control + r.spin) / 3.0
        extra = 0.0
        tags = r.tags or ""

        if index_ratio < ring_ratio and "스핀" in tags:
            extra += 0.5

        if size is not None and _size_is_big(hand_length, hand_width) and "헤비" in tags:
            extra += 0.5

        data = r.to_dict()
        data["score"] = round(base_score + extra, 1)

        results.append(data)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]
