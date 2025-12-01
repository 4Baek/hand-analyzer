import os
from flask import Flask
from db_config import db, init_db

from views.main import main_bp
from api.hand import hand_bp
from api.admin import admin_bp


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app() -> Flask:
    app = Flask(__name__)

    # DB 설정
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "rackets.db"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # DB 초기화
    db.init_app(app)
    with app.app_context():
        init_db()

    # 블루프린트 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(hand_bp)
    app.register_blueprint(admin_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
