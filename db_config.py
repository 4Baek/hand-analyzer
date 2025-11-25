# db_config.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Racket(db.Model):
    __tablename__ = "rackets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)

    power = db.Column(db.Integer, nullable=False, default=5)
    control = db.Column(db.Integer, nullable=False, default=5)
    spin = db.Column(db.Integer, nullable=False, default=5)

    weight = db.Column(db.Integer, nullable=True)  # g 단위
    tags = db.Column(db.String(200), nullable=True)  # "스핀,공격형" 이런 식

    def to_dict(self):
        """API 응답용 공통 변환 메서드"""
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "power": self.power,
            "control": self.control,
            "spin": self.spin,
            "weight": self.weight,
            "tags": (self.tags or "").split(",") if self.tags else [],
        }


def _seed_rackets():
    """rackets 테이블이 비어 있을 때 기본 라켓들을 넣어주는 함수."""
    from sqlalchemy import func

    count = db.session.query(func.count(Racket.id)).scalar()
    if count and count > 0:
        return

    samples = [
        Racket(
            name="Wilson RF01",
            brand="Wilson",
            power=7,
            control=10,
            spin=6,
            weight=340,
            tags="헤비,컨트롤,페더러",
        ),
        Racket(
            name="Babolat Pure Aero",
            brand="Babolat",
            power=9,
            control=6,
            spin=10,
            weight=300,
            tags="스핀,공격형,나달",
        ),
        Racket(
            name="Babolat Pure Drive",
            brand="Babolat",
            power=9,
            control=7,
            spin=7,
            weight=300,
            tags="파워,올라운드",
        ),
        Racket(
            name="Yonex Percept",
            brand="Yonex",
            power=7,
            control=9,
            spin=7,
            weight=305,
            tags="컨트롤,감각",
        ),
        Racket(
            name="Yonex Ezone",
            brand="Yonex",
            power=9,
            control=7,
            spin=6,
            weight=305,
            tags="파워,편안함",
        ),
        Racket(
            name="Wilson Pro Staff V14",
            brand="Wilson",
            power=7,
            control=10,
            spin=6,
            weight=315,
            tags="전통컨트롤,상급자",
        ),
        Racket(
            name="Wilson Blade V9",
            brand="Wilson",
            power=8,
            control=9,
            spin=8,
            weight=305,
            tags="컨트롤,스핀,투어",
        ),
        Racket(
            name="Head Gravity MP 2023",
            brand="Head",
            power=8,
            control=8,
            spin=7,
            weight=295,
            tags="큰스윗스폿,올라운드",
        ),
    ]

    db.session.add_all(samples)
    db.session.commit()


def init_db():
    """앱 컨텍스트 안에서 호출되는 전제."""
    db.create_all()
    _seed_rackets()


def reset_db():
    """개발용: 전체 드롭 후 재생성 + 샘플 데이터 재입력."""
    db.drop_all()
    db.create_all()
    _seed_rackets()
