def calculate_confidence(race):

    # Own-car information is considered highly reliable
    own_car_confidence = 0.94

    # Opponent state is estimated from observable information
    opponent_confidence = 0.65

    # Data quality
    data_quality = 0.90

    overall = (
        own_car_confidence * 0.45
        + opponent_confidence * 0.35
        + data_quality * 0.20
    )

    return {
        "own_car": own_car_confidence,
        "opponent": opponent_confidence,
        "overall": overall
    }