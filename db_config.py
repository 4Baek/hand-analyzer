from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Racket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    power = db.Column(db.Integer, nullable=True)
    control = db.Column(db.Integer, nullable=True)
    spin = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Integer, nullable=True)
    tags = db.Column(db.String(300), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "power": self.power,
            "control": self.control,
            "spin": self.spin,
            "weight": self.weight,
            "tags": self.tags,
        }


def _seed_rackets(db):
    sample_rackets = [
        Racket(name="Wilson Pro Staff V14", brand="Wilson", power=6, control=9, spin=6, weight=315),
        Racket(name="Babolat Pure Aero", brand="Babolat", power=8, control=6, spin=9, weight=300),
        Racket(name="Yonex Ezone", brand="Yonex", power=9, control=6, spin=7, weight=305),
    ]
    for r in sample_rackets:
        db.session.add(r)
    db.session.commit()


def init_db():
    db.create_all()
    if Racket.query.count() == 0:
        _seed_rackets(db)


def reset_db():
    db.drop_all()
    db.create_all()
    _seed_rackets(db)
