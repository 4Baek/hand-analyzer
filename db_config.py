# db_config.py
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()


class HandMetrics(db.Model):
    """
    손 분석 결과 테이블 (hand_metrics)

    - hand_utils.analyze_hand() 결과를 그대로/부분적으로 저장한다.
    """
    __tablename__ = "hand_metrics"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    hand_length_mm = db.Column(db.Numeric(6, 2), nullable=False)
    hand_width_mm = db.Column(db.Numeric(6, 2), nullable=False)
    hand_length_score = db.Column(db.Numeric(7, 1), nullable=False)
    hand_width_score = db.Column(db.Numeric(7, 1), nullable=False)

    hand_size_category = db.Column(db.String(32), nullable=False)  # SMALL/MEDIUM/LARGE
    finger_ratios_json = db.Column(db.Text, nullable=False)

    capture_device = db.Column(db.String(32), nullable=True)
    capture_distance_cm = db.Column(db.Numeric(5, 2), nullable=True)

    raw_result_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    # 역방향: RecommendationLog.hand_metrics
    recommendation_logs = db.relationship(
        "RecommendationLog",
        back_populates="hand_metrics",
        lazy="dynamic",
    )

    def get_finger_ratios(self):
        try:
            return json.loads(self.finger_ratios_json)
        except Exception:
            return []

    def get_raw_result(self):
        try:
            return json.loads(self.raw_result_json) if self.raw_result_json else None
        except Exception:
            return None

    def to_dict(self):
        return {
            "id": self.id,
            "handLengthMm": float(self.hand_length_mm),
            "handWidthMm": float(self.hand_width_mm),
            "handLength": float(self.hand_length_score),
            "handWidth": float(self.hand_width_score),
            "handSizeCategory": self.hand_size_category,
            "fingerRatios": self.get_finger_ratios(),
            "captureDevice": self.capture_device,
            "captureDistanceCm": float(self.capture_distance_cm)
            if self.capture_distance_cm is not None
            else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class SurveyResponse(db.Model):
    """
    라켓 추천 설문 응답 테이블 (survey_responses)

    - playstyle_service.build_playstyle_profile()가 소비하는 최소 필드(level, pain, swing, styles, stringTypePreference)를 저장
    - 확장용 컬럼도 일부 포함
    """
    __tablename__ = "survey_responses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    level = db.Column(db.String(32), nullable=True)
    pain = db.Column(db.String(32), nullable=True)
    swing = db.Column(db.String(32), nullable=True)
    string_type_preference = db.Column(db.String(32), nullable=True)

    styles_json = db.Column(db.Text, nullable=True)

    preferred_weight_min_g = db.Column(db.SmallInteger, nullable=True)
    preferred_weight_max_g = db.Column(db.SmallInteger, nullable=True)
    preferred_head_size_min_sq_in = db.Column(db.SmallInteger, nullable=True)
    preferred_head_size_max_sq_in = db.Column(db.SmallInteger, nullable=True)
    preference_power = db.Column(db.SmallInteger, nullable=True)
    preference_control = db.Column(db.SmallInteger, nullable=True)
    preference_spin = db.Column(db.SmallInteger, nullable=True)

    extra_payload_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    recommendation_logs = db.relationship(
        "RecommendationLog",
        back_populates="survey_response",
        lazy="dynamic",
    )

    def get_styles(self):
        try:
            return json.loads(self.styles_json) if self.styles_json else []
        except Exception:
            return []

    def get_extra_payload(self):
        try:
            return json.loads(self.extra_payload_json) if self.extra_payload_json else None
        except Exception:
            return None

    def to_dict(self):
        return {
            "id": self.id,
            "level": self.level,
            "pain": self.pain,
            "swing": self.swing,
            "styles": self.get_styles(),
            "stringTypePreference": self.string_type_preference,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class RecommendationLog(db.Model):
    """
    실제 추천 결과 로그 테이블 (recommendation_logs)

    - 어떤 손/설문 조합으로 어떤 라켓과 스트링/텐션을 추천했는지 기록
    """
    __tablename__ = "recommendation_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    hand_metrics_id = db.Column(
        db.Integer,
        db.ForeignKey("hand_metrics.id"),
        nullable=True,
    )
    survey_response_id = db.Column(
        db.Integer,
        db.ForeignKey("survey_responses.id"),
        nullable=True,
    )
    racket_id = db.Column(
        db.Integer,
        db.ForeignKey("rackets.id"),
        nullable=False,
    )

    recommended_string_type = db.Column(db.String(32), nullable=True)
    recommended_string_label = db.Column(db.String(100), nullable=True)
    recommended_tension_main_kg = db.Column(db.Numeric(4, 2), nullable=True)
    recommended_tension_main_lbs = db.Column(db.Numeric(5, 1), nullable=True)

    recommendation_score = db.Column(db.Numeric(6, 2), nullable=True)
    rank_in_result = db.Column(db.SmallInteger, nullable=True)

    algorithm_version = db.Column(db.String(32), nullable=True)
    rationale = db.Column(db.Text, nullable=True)

    hand_profile_json = db.Column(db.Text, nullable=True)
    style_profile_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    hand_metrics = db.relationship("HandMetrics", back_populates="recommendation_logs")
    survey_response = db.relationship("SurveyResponse", back_populates="recommendation_logs")
    racket = db.relationship("Racket")

    def get_hand_profile(self):
        try:
            return json.loads(self.hand_profile_json) if self.hand_profile_json else None
        except Exception:
            return None

    def get_style_profile(self):
        try:
            return json.loads(self.style_profile_json) if self.style_profile_json else None
        except Exception:
            return None

    def to_dict(self):
        return {
            "id": self.id,
            "handMetricsId": self.hand_metrics_id,
            "surveyResponseId": self.survey_response_id,
            "racketId": self.racket_id,
            "recommendedStringType": self.recommended_string_type,
            "recommendedStringLabel": self.recommended_string_label,
            "recommendedTensionMainKg": float(self.recommended_tension_main_kg)
            if self.recommended_tension_main_kg is not None
            else None,
            "recommendedTensionMainLbs": float(self.recommended_tension_main_lbs)
            if self.recommended_tension_main_lbs is not None
            else None,
            "recommendationScore": float(self.recommendation_score)
            if self.recommendation_score is not None
            else None,
            "rankInResult": self.rank_in_result,
            "algorithmVersion": self.algorithm_version,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class Racket(db.Model):
    """
    테니스 라켓 스펙 + 점수 테이블

    - 기존 UI와의 호환을 위해 power/control/spin/weight/tags 컬럼은 유지
    - 추천 알고리즘 고도화를 위해 swingweight, head_size, stiffness_ra 등 확장
    """
    __tablename__ = "rackets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 기본 정보
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)

    # --- 스펙 관련 (추천 알고리즘에서 사용하는 확장 컬럼들) ---
    # 헤드 사이즈 (sq.in)
    head_size_sq_in = db.Column(db.Integer, nullable=True)
    # 라켓 길이 (mm) - 보통 685mm = 27inch
    length_mm = db.Column(db.Integer, nullable=True)
    # 언스트렁 무게 (g)
    unstrung_weight_g = db.Column(db.Integer, nullable=True)

    # 밸런스 타입: HL(Head Light), EB(Even Balance), HH(Head Heavy)
    balance_type = db.Column(db.String(10), nullable=True)

    # 스윙웨이트 (단위: 관성값, 보통 280~340 근처)
    swingweight = db.Column(db.Integer, nullable=True)

    # 프레임 강성 (RA, 보통 58~72)
    stiffness_ra = db.Column(db.Integer, nullable=True)

    # 스트링 패턴 (예: 16x19, 18x20)
    string_pattern = db.Column(db.String(10), nullable=True)

    # 빔 두께 (예: "23-26-23")
    beam_width_mm = db.Column(db.String(30), nullable=True)

    # --- 점수 계열 (1~10) ---
    # 기존 컬럼 (UI, 호환용)
    power = db.Column(db.Integer, nullable=False, default=5)
    control = db.Column(db.Integer, nullable=False, default=5)
    spin = db.Column(db.Integer, nullable=False, default=5)
    weight = db.Column(db.Integer, nullable=True)  # 기존 UI에서 쓰던 weight (g)

    # 추천엔진용 상세 점수 (없으면 위 값으로 fallback)
    power_score = db.Column(db.Integer, nullable=True)
    control_score = db.Column(db.Integer, nullable=True)
    spin_score = db.Column(db.Integer, nullable=True)
    comfort_score = db.Column(db.Integer, nullable=True)
    maneuver_score = db.Column(db.Integer, nullable=True)

    # 타깃 레벨 (1=입문, 2=초급, 3=중급, 4=상급)
    level_min = db.Column(db.Integer, nullable=True)
    level_max = db.Column(db.Integer, nullable=True)

    # 태그 및 활성 여부
    tags = db.Column(db.String(300), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    url = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        """
        admin_db.js, recommend.js에서 공통으로 쓰는 JSON 형태.
        기존 필드(power/control/spin/weight/tags)는 유지하고,
        headSize/swingweight/stiffnessRa 같은 확장 필드도 함께 내려준다.
        """
        power_score = self.power_score if self.power_score is not None else self.power
        control_score = (
            self.control_score if self.control_score is not None else self.control
        )
        spin_score = self.spin_score if self.spin_score is not None else self.spin

        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            # 기존 UI 필드
            "power": self.power,
            "control": self.control,
            "spin": self.spin,
            "weight": self.weight or self.unstrung_weight_g,
            "tags": self.tags,
            # 확장 스펙 필드
            "headSize": self.head_size_sq_in,
            "lengthMm": self.length_mm,
            "unstrungWeight": self.unstrung_weight_g,
            "balanceType": self.balance_type,
            "swingweight": self.swingweight,
            "stiffnessRa": self.stiffness_ra,
            "stringPattern": self.string_pattern,
            "beamWidthMm": self.beam_width_mm,
            # 확장 점수 필드
            "powerScore": power_score,
            "controlScore": control_score,
            "spinScore": spin_score,
            "comfortScore": self.comfort_score,
            "maneuverScore": self.maneuver_score,
            "levelMin": self.level_min,
            "levelMax": self.level_max,
            "isActive": self.is_active,
            "url": self.url,
        }


# ----------------------------------------------------------------------
# 샘플 라켓 데이터 (MariaDB든 SQLite든 처음 DB 만들 때 seed)
# ----------------------------------------------------------------------
def _seed_rackets():
    """
    라켓 테이블이 비어 있을 때만 샘플 데이터를 채운다.
    실제 상용 스펙과는 다를 수 있으며, 추천 알고리즘 테스트용 추정값입니다.
    """
    if Racket.query.count() > 0:
        return

    samples = [
        # ... (기존 샘플 라켓들 그대로 유지, 생략 가능)
    ]

    db.session.add_all(samples)
    db.session.commit()


def init_db():
    """
    앱 시작 시 한 번 호출:
    - 테이블 없으면 생성
    - 라켓 테이블이 비어 있으면 샘플 데이터 seed
    """
    db.create_all()
    _seed_rackets()


def reset_db():
    """
    개발용:
    - 모든 테이블 드롭 후 재생성
    - 샘플 라켓 데이터 다시 입력
    """
    db.drop_all()
    db.create_all()
    _seed_rackets()
