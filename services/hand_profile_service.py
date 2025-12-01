def build_hand_profile(metrics: dict) -> dict:
    if metrics is None:
        return {"handExists": False}

    hand_length = metrics.get("handLength")
    hand_width = metrics.get("handWidth")

    if hand_length is not None:
        if hand_length < 16:
            size_group = "small"
        elif hand_length < 18:
            size_group = "medium"
        else:
            size_group = "large"
    else:
        size_group = None

    return {
        "handExists": True,
        "handLength": hand_length,
        "handWidth": hand_width,
        "sizeGroup": size_group,
    }
