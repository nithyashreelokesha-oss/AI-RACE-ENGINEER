from .overtake import clamp


def calculate_retention_probability(race, deployment_mode):
    """
    Estimates the probability of retaining the position
    after completing an overtake.
    """

    battery_score = race["battery"] / 100

    # Opponent threat
    opponent_threat = race["threat_level"]

    # Tyre condition
    tyre_score = race["tyre_advantage"]

    # Deployment mode affects how much energy remains
    mode_bonus = {
        "PUSH": 0.15,
        "BALANCED": 0.10,
        "HARVEST": 0.05,
        "CONSERVE": -0.10
    }

    score = (
        battery_score * 0.35 +
        (1 - opponent_threat) * 0.25 +
        tyre_score * 0.20 +
        0.15 +
        mode_bonus[deployment_mode]
    )

    return round(clamp(score), 3)