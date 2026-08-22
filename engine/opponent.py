def estimate_opponent_state(race):

    pace = race["pace_advantage"]
    gap_trend = race["gap_behind"]

    # Faster closing pace may indicate opponent is deploying energy
    if gap_trend < 0.5 and pace < 0:

        state = "HIGH DEPLOYMENT"

    elif gap_trend > 1.5 and pace > 0.1:

        state = "LOW DEPLOYMENT"

    else:

        state = "BALANCED"

    confidence = 0.60

    return {
        "state": state,
        "confidence": confidence
    }