from db_config import Racket

def match_rackets(hand_profile: dict, style_profile: dict):
    power_factor = style_profile.get("powerFactor", 5)
    control_factor = style_profile.get("controlFactor", 5)

    candidates = []
    for r in Racket.query.all():
        score = (
            (r.power or 5) * power_factor +
            (r.control or 5) * control_factor
        )

        if hand_profile.get("sizeGroup") == "small" and (r.weight or 300) < 290:
            score += 30
        if hand_profile.get("sizeGroup") == "large" and (r.weight or 300) > 305:
            score += 30

        candidates.append({
            "id": r.id,
            "name": r.name,
            "brand": r.brand,
            "weight": r.weight,
            "score": score,
        })

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:5]

    return {
        "rackets": candidates,
        "string": {
            "recommendedTension": 48 if style_profile.get("preference") != "control" else 52
        }
    }
