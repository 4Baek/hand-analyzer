"""
services 패키지

비즈니스 로직 모음.

- hand_profile_service.py    : 손 분석 결과 → 손 프로필 생성
- playstyle_service.py       : 설문 결과 → 플레이 스타일 프로필 생성
- racket_matching_service.py : 손 프로필 + 스타일 → 라켓/스트링 매칭
- recommend_service.py       : 위 서비스들을 조합한 최종 추천 진입점
"""

# 필요하다면 여기서 주요 함수들을 재노출할 수 있습니다.
# from .recommend_service import recommend_rackets_from_metrics
# __all__ = ["recommend_rackets_from_metrics"]
