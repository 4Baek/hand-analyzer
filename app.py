import os
from flask import Flask, request, jsonify, render_template

from hand_utils import analyze_hand
from db_config import db, init_db, reset_db, Racket
from hand_service import recommend_rackets_from_metrics

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 나중에 DATABASE_URL 환경변수로 다른 DB 연결 가능
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "rackets.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# 앱 시작 시 DB 준비
with app.app_context():
    init_db()


# -------------------------
# 메인 페이지 / 관리자 페이지
# -------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/admin", methods=["GET"])
def admin_page():
    # DB 관리 전용 페이지
    return render_template("admin.html")


# -------------------------
# 손 이미지 분석
# -------------------------

@app.route("/scan-hand", methods=["POST"])
def scan_hand():
    if "file" not in request.files:
        return jsonify({"error": "이미지 파일이 필요합니다"}), 400

    file = request.files["file"]
    temp_path = os.path.join(BASE_DIR, "temp.jpg")
    file.save(temp_path)

    result = analyze_hand(temp_path)
    if result is None:
        return jsonify({"error": "손 인식 실패"}), 400

    java_url = 'http://localhost:8080/recommend'
    try:
        print("✅ Java로 전달할 JSON:", result)
        java_response = requests.post(java_url, json=[result], timeout=5)
        print("📨 Java 응답 코드:", java_response.status_code)
        print("📨 Java 응답 본문:", java_response.text)
        java_response.raise_for_status()
        return jsonify(java_response.json())
    except requests.exceptions.RequestException as e:
        print("[Java 연동 오류]", e)
        return jsonify({'error': 'Java 서버 통신 실패'}), 500


# -------------------------
# 라켓 추천 API
# -------------------------

@app.route("/recommend-rackets", methods=["POST"])
def recommend_rackets_api():
    data = request.get_json(silent=True) or {}
    rackets = recommend_rackets_from_metrics(data)
    return jsonify({"rackets": rackets})


# -------------------------
# DB 관리용 API
# -------------------------

@app.route("/admin/reset-db", methods=["POST"])
def reset_db_route():
    reset_db()
    return jsonify({"status": "ok", "message": "DB reset & seeded"})


@app.route("/admin/rackets", methods=["GET", "POST"])
def admin_rackets():
    if request.method == "GET":
        rackets = Racket.query.order_by(Racket.id).all()
        data = [r.to_dict() for r in rackets]
        return jsonify({"rackets": data})

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    brand = (data.get("brand") or "").strip()

    if not name or not brand:
        return jsonify({"error": "name, brand는 필수입니다."}), 400

    def to_int(value, default=None):
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    power = to_int(data.get("power"), 5)
    control = to_int(data.get("control"), 5)
    spin = to_int(data.get("spin"), 5)
    weight = to_int(data.get("weight"))

    tags_raw = data.get("tags")
    if isinstance(tags_raw, list):
        tags = ",".join(t.strip() for t in tags_raw if t)
    else:
        tags = (tags_raw or "").strip()

    new_racket = Racket(
        name=name,
        brand=brand,
        power=power,
        control=control,
        spin=spin,
        weight=weight,
        tags=tags,
    )

    db.session.add(new_racket)
    db.session.commit()

    return jsonify({"racket": new_racket.to_dict()}), 201


# ---- 새로 추가: 라켓 단건 삭제 ----
@app.route("/admin/rackets/<int:racket_id>", methods=["DELETE"])
def delete_racket(racket_id):
    racket = Racket.query.get(racket_id)
    if racket is None:
        return jsonify({"error": "해당 ID의 라켓이 없습니다."}), 404

    db.session.delete(racket)
    db.session.commit()
    return jsonify({"status": "ok", "message": f"삭제 완료 (id={racket_id})"})


if __name__ == "__main__":
    app.run(port=5000)
