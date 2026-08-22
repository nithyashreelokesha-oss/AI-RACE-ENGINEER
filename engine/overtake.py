import os
import joblib
import pandas as pd


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
    "ml",
    "overtake_model.pkl"
)


# ============================================================
# ML STATE
# ============================================================

ML_MODEL = None
ML_AVAILABLE = False
ML_ERROR = None


# ============================================================
# LOAD MODEL
# ============================================================

try:

    if not os.path.exists(MODEL_PATH):

        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    ML_MODEL = joblib.load(
        MODEL_PATH
    )

    ML_AVAILABLE = True
    ML_ERROR = None

except Exception as error:

    ML_MODEL = None
    ML_AVAILABLE = False
    ML_ERROR = str(error)


# ============================================================
# ML STATUS
# ============================================================

def get_ml_status():

    return {
        "available": ML_AVAILABLE,
        "model_loaded": ML_MODEL is not None,
        "model_path": MODEL_PATH,
        "error": ML_ERROR
    }


# ============================================================
# CLAMP
# ============================================================

def clamp(
    value,
    minimum=0.0,
    maximum=1.0
):

    return max(
        minimum,
        min(
            float(value),
            maximum
        )
    )


# ============================================================
# RULE FACTOR
# ============================================================

def calculate_rule_factor(race):

    track_limit_risk = clamp(
        race.get(
            "track_limit_risk",
            0.0
        )
    )

    race_condition = race.get(
        "race_condition",
        "NORMAL"
    )

    condition_factor = {

        "NORMAL": 1.00,

        "WET": 0.88,

        "VSC": 0.35,

        "SAFETY CAR": 0.10

    }.get(
        race_condition,
        1.00
    )

    track_factor = (
        1.0
        - 0.35 * track_limit_risk
    )

    return clamp(
        condition_factor
        * track_factor
    )


# ============================================================
# HEURISTIC MODEL
# ============================================================

def calculate_heuristic_probability(race):

    gap = float(
        race.get(
            "gap_ahead",
            2.0
        )
    )

    # --------------------------------------------------------
    # GAP
    # --------------------------------------------------------

    if gap <= 0.30:

        gap_score = 1.00

    elif gap <= 0.60:

        gap_score = 0.85

    elif gap <= 1.00:

        gap_score = 0.65

    elif gap <= 1.50:

        gap_score = 0.40

    else:

        gap_score = 0.15


    # --------------------------------------------------------
    # PACE
    # --------------------------------------------------------

    pace_score = clamp(
        (
            race.get(
                "pace_advantage",
                0.5
            )
            + 0.5
        )
        / 1.0
    )


    # --------------------------------------------------------
    # TYRES
    # --------------------------------------------------------

    tyre_score = clamp(
        race.get(
            "tyre_advantage",
            0.5
        )
    )


    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    energy_score = clamp(
        race.get(
            "battery",
            100.0
        )
        / 100.0
    )


    # --------------------------------------------------------
    # OPPORTUNITY
    # --------------------------------------------------------

    opportunity_score = clamp(
        race.get(
            "overtake_opportunity",
            0.5
        )
    )


    # --------------------------------------------------------
    # RULES
    # --------------------------------------------------------

    rule_factor = calculate_rule_factor(
        race
    )


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = (

        gap_score * 0.23

        + pace_score * 0.18

        + tyre_score * 0.14

        + energy_score * 0.14

        + opportunity_score * 0.21

        + rule_factor * 0.10
    )

    return clamp(
        score
    )


# ============================================================
# BUILD ML FEATURES
# ============================================================

def build_ml_features(race):

    return {

        "lap":
            race.get(
                "lap",
                1
            ),

        "sector":
            race.get(
                "sector",
                1
            ),

        "position":
            race.get(
                "position",
                6
            ),

        "battery":
            race.get(
                "battery",
                100.0
            ),

        "gap_ahead":
            race.get(
                "gap_ahead",
                1.0
            ),

        "gap_behind":
            race.get(
                "gap_behind",
                1.0
            ),

        "tyre_advantage":
            race.get(
                "tyre_advantage",
                0.5
            ),

        "pace_advantage":
            race.get(
                "pace_advantage",
                0.5
            ),

        "overtake_opportunity":
            race.get(
                "overtake_opportunity",
                0.5
            ),

        "future_opportunity":
            race.get(
                "future_opportunity",
                0.5
            ),

        "threat_level":
            race.get(
                "threat_level",
                0.5
            ),

        "sector_type":
            race.get(
                "sector_type",
                "HIGH_SPEED"
            ),

        "sector_energy_demand":
            race.get(
                "sector_energy_demand",
                1.0
            ),

        "sector_overtaking_base":
            race.get(
                "sector_overtaking_base",
                0.5
            ),

        "sector_braking_importance":
            race.get(
                "sector_braking_importance",
                0.5
            ),

        "sector_traction_importance":
            race.get(
                "sector_traction_importance",
                0.5
            ),

        "deployment_mode":
            race.get(
                "deployment_mode",
                "BALANCED"
            ),

        "recommendation":
            race.get(
                "recommendation",
                "ATTACK"
            )
    }


# ============================================================
# RANDOM FOREST PREDICTION
# ============================================================

def calculate_ml_probability(race):

    global ML_ERROR

    if not ML_AVAILABLE:

        return None


    features = build_ml_features(
        race
    )


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Use DataFrame instead of:
    #
    #     [features]
    #
    # This preserves feature names for sklearn.
    # --------------------------------------------------------

    df = pd.DataFrame(
        [features]
    )


    try:

        # ====================================================
        # CHECK EXPECTED FEATURES
        # ====================================================

        if hasattr(
            ML_MODEL,
            "feature_names_in_"
        ):

            expected_features = list(
                ML_MODEL.feature_names_in_
            )

            # Add missing columns if necessary.

            for column in expected_features:

                if column not in df.columns:

                    df[column] = 0


            # Remove unexpected columns and preserve
            # training order.

            df = df[
                expected_features
            ]


        # ====================================================
        # RANDOM FOREST PREDICTION
        # ====================================================

        probabilities = (
            ML_MODEL.predict_proba(
                df
            )
        )


        # ====================================================
        # BINARY CLASSIFICATION
        # ====================================================

        if probabilities.shape[1] >= 2:

            probability = (
                probabilities[0][1]
            )

        else:

            probability = (
                probabilities[0][0]
            )


        ML_ERROR = None

        return clamp(
            probability
        )


    except Exception as error:

        # Do NOT silently hide the error.

        ML_ERROR = (
            f"{type(error).__name__}: "
            f"{str(error)}"
        )

        return None


# ============================================================
# SECTOR FACTOR
# ============================================================

def calculate_sector_factor(race):

    return clamp(
        race.get(
            "sector_overtaking_base",
            0.5
        )
    )


# ============================================================
# HYBRID MODEL
# ============================================================

def calculate_overtake_probability(race):

    # --------------------------------------------------------
    # P1
    # --------------------------------------------------------

    if race.get(
        "position",
        6
    ) <= 1:

        return 0.0


    # --------------------------------------------------------
    # ML
    # --------------------------------------------------------

    ml_probability = (
        calculate_ml_probability(
            race
        )
    )


    # --------------------------------------------------------
    # HEURISTIC
    # --------------------------------------------------------

    heuristic_probability = (
        calculate_heuristic_probability(
            race
        )
    )


    # --------------------------------------------------------
    # HYBRID
    # --------------------------------------------------------

    if ml_probability is not None:

        probability = (

            ml_probability * 0.70

            + heuristic_probability * 0.30
        )

    else:

        # If RF genuinely cannot run, the AI still works
        # using the heuristic model.

        probability = (
            heuristic_probability
        )


    # --------------------------------------------------------
    # SECTOR
    # --------------------------------------------------------

    sector_factor = (
        calculate_sector_factor(
            race
        )
    )

    probability = (

        probability * 0.75

        + sector_factor * 0.25
    )


    # ========================================================
    # GAP
    # ========================================================

    gap = float(
        race.get(
            "gap_ahead",
            2.0
        )
    )

    if gap > 2.0:

        probability *= 0.25

    elif gap > 1.5:

        probability *= 0.50


    # ========================================================
    # TYRES
    # ========================================================

    tyre_advantage = clamp(
        race.get(
            "tyre_advantage",
            0.5
        )
    )

    if tyre_advantage < 0.20:

        probability *= 0.50

    elif tyre_advantage < 0.35:

        probability *= 0.75


    # ========================================================
    # BATTERY
    # ========================================================

    battery = float(
        race.get(
            "battery",
            100.0
        )
    )

    if battery < 15:

        probability *= 0.40

    elif battery < 25:

        probability *= 0.65


    # ========================================================
    # OPPORTUNITY
    # ========================================================

    opportunity = clamp(
        race.get(
            "overtake_opportunity",
            0.5
        )
    )

    if opportunity < 0.25:

        probability *= 0.45

    elif opportunity < 0.40:

        probability *= 0.70


    # ========================================================
    # TRACK LIMITS
    # ========================================================

    track_limit_risk = clamp(
        race.get(
            "track_limit_risk",
            0.0
        )
    )

    probability *= (
        1.0
        - 0.30 * track_limit_risk
    )


    # ========================================================
    # RACE CONTROL
    # ========================================================

    condition = race.get(
        "race_condition",
        "NORMAL"
    )

    probability *= {

        "NORMAL": 1.00,

        "WET": 0.88,

        "VSC": 0.35,

        "SAFETY CAR": 0.10

    }.get(
        condition,
        1.00
    )


    return round(
        clamp(
            probability,
            0.0,
            0.95
        ),
        3
    )


# ============================================================
# EXPLAINABILITY
# ============================================================

def calculate_overtake_factors(race):

    gap = float(
        race.get(
            "gap_ahead",
            2.0
        )
    )

    if gap <= 0.30:

        gap_score = 1.00

    elif gap <= 0.60:

        gap_score = 0.85

    elif gap <= 1.00:

        gap_score = 0.65

    elif gap <= 1.50:

        gap_score = 0.40

    else:

        gap_score = 0.15


    ml_probability = (
        calculate_ml_probability(
            race
        )
    )


    return {

        "gap":
            gap_score,

        "pace":
            clamp(
                (
                    race.get(
                        "pace_advantage",
                        0.5
                    )
                    + 0.5
                )
                / 1.0
            ),

        "tyres":
            clamp(
                race.get(
                    "tyre_advantage",
                    0.5
                )
            ),

        "energy":
            clamp(
                race.get(
                    "battery",
                    100.0
                )
                / 100.0
            ),

        "opportunity":
            clamp(
                race.get(
                    "overtake_opportunity",
                    0.5
                )
            ),

        "sector":
            clamp(
                race.get(
                    "sector_overtaking_base",
                    0.5
                )
            ),

        "track_limit_risk":
            clamp(
                race.get(
                    "track_limit_risk",
                    0.0
                )
            ),

        "rule_factor":
            calculate_rule_factor(
                race
            ),

        "race_condition":
            race.get(
                "race_condition",
                "NORMAL"
            ),

        "ml_probability":
            ml_probability
    }