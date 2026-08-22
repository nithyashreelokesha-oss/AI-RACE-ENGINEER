from .overtake import (
    calculate_overtake_probability
)

from .retention import (
    calculate_retention_probability
)

from .rules import (
    attack_is_allowed
)


# ============================================================
# DEFAULT WEIGHTS
# ============================================================

DEFAULT_WEIGHTS = {

    "overtake": 1.0,

    "retention": 1.0,

    "current_opportunity": 1.0,

    "future_opportunity": 1.0,

    "energy": 1.0,

    "tyres": 1.0,

    "threat": 1.0
}


# ============================================================
# CLAMP
# ============================================================

def clamp(
    value,
    minimum=0.0,
    maximum=10.0
):

    return max(
        minimum,
        min(
            value,
            maximum
        )
    )


# ============================================================
# ATTACK SCORE
# ============================================================

def calculate_attack_score(
    race,
    deployment_mode,
    weights=None
):

    if weights is None:

        weights = DEFAULT_WEIGHTS

    overtake = calculate_overtake_probability(
        race
    )

    retention = calculate_retention_probability(
        race,
        deployment_mode
    )

    battery = race[
        "battery"
    ] / 100.0

    tyres = race[
        "tyre_advantage"
    ]

    opportunity = race[
        "overtake_opportunity"
    ]

    # --------------------------------------------------------
    # Weighted factors
    # --------------------------------------------------------

    overtake_value = (
        overtake
        * 3.0
        * weights["overtake"]
    )

    retention_value = (
        retention
        * 2.5
        * weights["retention"]
    )

    opportunity_value = (
        opportunity
        * 2.0
        * weights["current_opportunity"]
    )

    energy_value = (
        battery
        * 1.5
        * weights["energy"]
    )

    tyre_value = (
        tyres
        * 1.0
        * weights["tyres"]
    )

    score = (

        overtake_value

        + retention_value

        + opportunity_value

        + energy_value

        + tyre_value

    )

    # --------------------------------------------------------
    # Energy risk
    # --------------------------------------------------------

    if battery < 0.30:

        score -= (
            2.0
            * weights["energy"]
        )

    elif battery < 0.45:

        score -= (
            1.0
            * weights["energy"]
        )

    # --------------------------------------------------------
    # Tyre risk
    # --------------------------------------------------------

    if tyres < 0.40:

        score -= (
            1.0
            * weights["tyres"]
        )

    return round(
        clamp(score),
        2
    )


# ============================================================
# STAY SCORE
# ============================================================

def calculate_stay_score(
    race,
    weights=None
):

    if weights is None:

        weights = DEFAULT_WEIGHTS

    battery = race[
        "battery"
    ] / 100.0

    future = race[
        "future_opportunity"
    ]

    current = race[
        "overtake_opportunity"
    ]

    threat = race[
        "threat_level"
    ]

    energy_value = (
        battery
        * 3.0
        * weights["energy"]
    )

    future_value = (
        future
        * 3.0
        * weights["future_opportunity"]
    )

    patience_value = (
        (1.0 - current)
        * 2.0
        * weights["current_opportunity"]
    )

    safety_value = (
        (1.0 - threat)
        * 2.0
        * weights["threat"]
    )

    score = (

        energy_value

        + future_value

        + patience_value

        + safety_value

    )

    return round(
        clamp(score),
        2
    )


# ============================================================
# DEFEND SCORE
# ============================================================

def calculate_defend_score(
    race,
    deployment_mode,
    weights=None
):

    if weights is None:

        weights = DEFAULT_WEIGHTS

    retention = calculate_retention_probability(
        race,
        deployment_mode
    )

    battery = race[
        "battery"
    ] / 100.0

    threat = race[
        "threat_level"
    ]

    tyres = race[
        "tyre_advantage"
    ]

    threat_value = (
        threat
        * 4.0
        * weights["threat"]
    )

    retention_value = (
        retention
        * 2.5
        * weights["retention"]
    )

    energy_value = (
        battery
        * 1.5
        * weights["energy"]
    )

    tyre_value = (
        tyres
        * 1.0
        * weights["tyres"]
    )

    score = (

        threat_value

        + retention_value

        + energy_value

        + tyre_value

    )

    if battery < 0.25:

        score -= (
            2.0
            * weights["energy"]
        )

    return round(
        clamp(score),
        2
    )


# ============================================================
# MAIN STRATEGY
# ============================================================

def evaluate_strategy(
    race,
    deployment_mode,
    weights=None
):

    if weights is None:

        weights = DEFAULT_WEIGHTS

    attack = calculate_attack_score(
        race,
        deployment_mode,
        weights
    )

    stay = calculate_stay_score(
        race,
        weights
    )

    defend = calculate_defend_score(
        race,
        deployment_mode,
        weights
    )

    # --------------------------------------------------------
    # Rule gate
    # --------------------------------------------------------

    from .energy import calculate_deployment

    deployment = calculate_deployment(
        race,
        deployment_mode
    )

    if not attack_is_allowed(
        race,
        deployment
    ):

        attack = 0.0

    scores = {

        "ATTACK":
            attack,

        "STAY":
            stay,

        "DEFEND":
            defend
    }

    recommendation = max(
        scores,
        key=scores.get
    )

    return scores, recommendation