def attack_scenario():

    return {
        "lap": 42,
        "total_laps": 57,
        "position": 6,

        "battery": 72,

        "gap_ahead": 0.4,
        "gap_behind": 1.5,

        "tyre_condition": "GOOD",
        "tyre_advantage": 0.90,

        "pace_advantage": 0.35,

        "overtake_opportunity": 0.92,
        "future_opportunity": 0.50,

        "threat_level": 0.20
    }


def energy_critical_scenario():

    return {
        "lap": 42,
        "total_laps": 57,
        "position": 6,

        "battery": 22,

        "gap_ahead": 1.0,
        "gap_behind": 1.2,

        "tyre_condition": "GOOD",
        "tyre_advantage": 0.80,

        "pace_advantage": 0.10,

        "overtake_opportunity": 0.80,
        "future_opportunity": 0.60,

        "threat_level": 0.30
    }


def defensive_scenario():

    return {
        "lap": 42,
        "total_laps": 57,
        "position": 6,

        "battery": 50,

        "gap_ahead": 1.5,
        "gap_behind": 0.25,

        "tyre_condition": "MEDIUM",
        "tyre_advantage": 0.60,

        "pace_advantage": -0.10,

        "overtake_opportunity": 0.30,
        "future_opportunity": 0.50,

        "threat_level": 0.90
    }


def future_opportunity_scenario():

    return {
        "lap": 42,
        "total_laps": 57,
        "position": 6,

        "battery": 55,

        "gap_ahead": 1.0,
        "gap_behind": 1.5,

        "tyre_condition": "GOOD",
        "tyre_advantage": 0.85,

        "pace_advantage": 0.15,

        "overtake_opportunity": 0.35,
        "future_opportunity": 0.95,

        "threat_level": 0.20
    }