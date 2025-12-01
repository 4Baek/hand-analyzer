# db_config.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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

    # ------------------------------------------------------------------
    # JSON 변환 (admin UI, /recommend-rackets 응답용)
    # ------------------------------------------------------------------
    def to_dict(self):
        """
        admin_db.js, recommend.js에서 공통으로 쓰는 JSON 형태.
        기존 필드(power/control/spin/weight/tags)는 유지하고,
        headSize/swingweight/stiffnessRa 같은 확장 필드도 함께 내려준다.
        """
        # 점수 계열 fallback 처리
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
        # 윌슨 RF01 (프로스태프 RF ver. 추정)
        Racket(
            name="Wilson Pro Staff RF97",
            brand="Wilson",
            head_size_sq_in=97,
            length_mm=686,
            unstrung_weight_g=340,
            weight=340,
            balance_type="HL",
            swingweight=335,
            stiffness_ra=68,
            string_pattern="16x19",
            beam_width_mm="21.5",
            power=7,
            control=9,
            spin=6,
            power_score=7,
            control_score=9,
            spin_score=6,
            comfort_score=5,
            maneuver_score=4,
            level_min=3,
            level_max=4,
            tags="헤비,컨트롤,공격형",
            is_active=True,
        ),
        # 바볼랏 Pure Aero
        Racket(
            name="Babolat Pure Aero",
            brand="Babolat",
            head_size_sq_in=100,
            length_mm=685,
            unstrung_weight_g=300,
            weight=300,
            balance_type="HL",
            swingweight=324,
            stiffness_ra=67,
            string_pattern="16x19",
            beam_width_mm="23-26-23",
            power=8,
            control=6,
            spin=9,
            power_score=8,
            control_score=6,
            spin_score=9,
            comfort_score=6,
            maneuver_score=7,
            level_min=2,
            level_max=4,
            tags="스핀,공격형,투어",
            is_active=True,
        ),
        # 바볼랏 Pure Drive
        Racket(
            name="Babolat Pure Drive",
            brand="Babolat",
            head_size_sq_in=100,
            length_mm=685,
            unstrung_weight_g=300,
            weight=300,
            balance_type="HL",
            swingweight=320,
            stiffness_ra=71,
            string_pattern="16x19",
            beam_width_mm="23-26-23",
            power=9,
            control=6,
            spin=7,
            power_score=9,
            control_score=6,
            spin_score=7,
            comfort_score=5,
            maneuver_score=7,
            level_min=2,
            level_max=4,
            tags="파워,올라운드",
            is_active=True,
        ),
        # 요넥스 Percept 97 (컨트롤형)
        Racket(
            name="Yonex Percept 97",
            brand="Yonex",
            head_size_sq_in=97,
            length_mm=685,
            unstrung_weight_g=310,
            weight=310,
            balance_type="HL",
            swingweight=320,
            stiffness_ra=62,
            string_pattern="16x19",
            beam_width_mm="21",
            power=6,
            control=9,
            spin=6,
            power_score=6,
            control_score=9,
            spin_score=6,
            comfort_score=7,
            maneuver_score=6,
            level_min=3,
            level_max=4,
            tags="컨트롤,부드러운타구감",
            is_active=True,
        ),
        # 요넥스 Ezone 100
        Racket(
            name="Yonex Ezone 100",
            brand="Yonex",
            head_size_sq_in=100,
            length_mm=685,
            unstrung_weight_g=300,
            weight=300,
            balance_type="HL",
            swingweight=318,
            stiffness_ra=68,
            string_pattern="16x19",
            beam_width_mm="23.5-26-22",
            power=8,
            control=7,
            spin=7,
            power_score=8,
            control_score=7,
            spin_score=7,
            comfort_score=6,
            maneuver_score=7,
            level_min=2,
            level_max=4,
            tags="공격형,올라운드",
            is_active=True,
        ),
        # Wilson Blade 98 v9
        Racket(
            name="Wilson Blade 98 v9",
            brand="Wilson",
            head_size_sq_in=98,
            length_mm=685,
            unstrung_weight_g=305,
            weight=305,
            balance_type="HL",
            swingweight=320,
            stiffness_ra=64,
            string_pattern="16x19",
            beam_width_mm="21",
            power=7,
            control=8,
            spin=7,
            power_score=7,
            control_score=8,
            spin_score=7,
            comfort_score=7,
            maneuver_score=7,
            level_min=2,
            level_max=4,
            tags="투어,밸런스",
            is_active=True,
        ),
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
