from flask import Blueprint, request, jsonify
from db_config import db, reset_db, Racket

admin_bp = Blueprint("admin_api", __name__)


@admin_bp.route("/admin/reset-db", methods=["POST"])
def reset_db_route():
    reset_db()
    return jsonify({"status": "ok", "message": "DB reset complete"})


@admin_bp.route("/admin/rackets", methods=["GET", "POST"])
def admin_rackets():
    if request.method == "GET":
        rackets = Racket.query.order_by(Racket.id).all()
        return jsonify({"rackets": [r.to_dict() for r in rackets]})

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    brand = (data.get("brand") or "").strip()
    if not name or not brand:
        return jsonify({"error": "name, brand 필수"}), 400

    def to_int(value, default=None):
        try:
            return int(value)
        except:
            return default

    new_racket = Racket(
        name=name,
        brand=brand,
        power=to_int(data.get("power"), 5),
        control=to_int(data.get("control"), 5),
        spin=to_int(data.get("spin"), 5),
        weight=to_int(data.get("weight")),
        tags=",".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else (data.get("tags") or "")
    )

    db.session.add(new_racket)
    db.session.commit()

    return jsonify({"racket": new_racket.to_dict()}), 201


@admin_bp.route("/admin/rackets/<int:racket_id>", methods=["DELETE"])
def delete_racket(racket_id):
    racket = Racket.query.get(racket_id)
    if racket is None:
        return jsonify({"error": "not found"}), 404

    db.session.delete(racket)
    db.session.commit()
    return jsonify({"status": "ok"})
