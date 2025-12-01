def build_playstyle_profile(survey: dict) -> dict:
    level = survey.get("level")
    swing = survey.get("swing")
    preference = survey.get("preference")

    power_factor = 5
    control_factor = 5

    if swing == "fast":
        power_factor += 2
    elif swing == "slow":
        control_factor += 2

    if preference == "power":
        power_factor += 3
    elif preference == "control":
        control_factor += 3

    return {
        "level": level,
        "swing": swing,
        "preference": preference,
        "powerFactor": power_factor,
        "controlFactor": control_factor,
    }
