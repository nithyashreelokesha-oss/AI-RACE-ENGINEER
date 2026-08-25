import os
import math
import joblib
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml",
    "overtake_model.pkl"
)

DEFAULT_THRESHOLD = 0.50

ML_MODEL = None
ML_AVAILABLE = False
ML_ERROR = None
MODEL_THRESHOLD = DEFAULT_THRESHOLD
MODEL_FEATURES = []


# ============================================================
# MODEL LOADING
# ============================================================

def _load_model():
    global ML_MODEL, ML_AVAILABLE, ML_ERROR
    global MODEL_THRESHOLD, MODEL_FEATURES

    if ML_MODEL is not None:
        return True

    if not os.path.exists(MODEL_PATH):
        ML_AVAILABLE = False
        ML_ERROR = f"Model file not found: {MODEL_PATH}"
        return False

    try:
        package = joblib.load(MODEL_PATH)
    except Exception as error:
        ML_MODEL = None
        ML_AVAILABLE = False
        ML_ERROR = f"{type(error).__name__}: {error}"
        print(f"[ML] Failed to load overtake model: {ML_ERROR}")
        return False

    if isinstance(package, dict):
        ML_MODEL = package.get("pipeline") or package.get("model")

        MODEL_THRESHOLD = float(
            package.get(
                "recommended_threshold",
                package.get("threshold", DEFAULT_THRESHOLD)
            )
        )

        MODEL_FEATURES = package.get(
            "features",
            package.get("feature_list", [])
        )
    else:
        ML_MODEL = package
        MODEL_THRESHOLD = DEFAULT_THRESHOLD
        MODEL_FEATURES = []

    if ML_MODEL is None:
        ML_AVAILABLE = False
        ML_ERROR = "Model package loaded but no model/pipeline was found."
        return False

    ML_AVAILABLE = True
    ML_ERROR = None
    return True


def get_ml_status():
    _load_model()

    return {
        "available": ML_AVAILABLE,
        "model_loaded": ML_MODEL is not None,
        "model_path": MODEL_PATH,
        "threshold": MODEL_THRESHOLD,
        "features": MODEL_FEATURES,
        "error": ML_ERROR
    }


def get_model_info():
    _load_model()

    return {
        "available": ML_AVAILABLE,
        "path": MODEL_PATH,
        "threshold": MODEL_THRESHOLD,
        "features": MODEL_FEATURES,
        "error": ML_ERROR
    }


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        value = float(value)
        if not math.isfinite(value):
            return default
        return value
    except Exception:
        return default


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(float(value), maximum))


# ============================================================
# ML FEATURE BUILDER
# ============================================================
#
# MUST match the leakage-free training model.
#
# Never add:
#   next_position
#   position_delta
#   position_gain
#   position_gain_strength
#   overtake
#
# Those contain future/target information.
# ============================================================

def build_ml_features(race):

    lap = _safe_float(race.get("lap", 1), 1)
    position = _safe_float(race.get("position", 10), 10)

    # Current simulator may not yet have real telemetry fields.
    # Missing values are therefore represented safely.
    lap_time = _safe_float(race.get("lap_time", 0), 0)
    previous_lap_time = _safe_float(
        race.get("previous_lap_time", lap_time),
        lap_time
    )

    speed_mean = _safe_float(race.get("speed_mean", 0), 0)
    speed_max = _safe_float(race.get("speed_max", speed_mean), speed_mean)
    speed_min = _safe_float(race.get("speed_min", speed_mean), speed_mean)

    speed_range = _safe_float(
        race.get("speed_range", speed_max - speed_min),
        0
    )

    speed_std = _safe_float(
        race.get("speed_std", 0),
        0
    )

    speed_variation = _safe_float(
        race.get("speed_variation", 0),
        0
    )

    throttle_mean = _safe_float(
        race.get("throttle_mean", 0),
        0
    )

    throttle_max = _safe_float(
        race.get("throttle_max", throttle_mean),
        throttle_mean
    )

    throttle_full_usage = _safe_float(
        race.get("throttle_full_usage", 0),
        0
    )

    brake_mean = _safe_float(
        race.get("brake_mean", 0),
        0
    )

    brake_max = _safe_float(
        race.get("brake_max", brake_mean),
        brake_mean
    )

    brake_usage = _safe_float(
        race.get("brake_usage", 0),
        0
    )

    heavy_braking_usage = _safe_float(
        race.get("heavy_braking_usage", 0),
        0
    )

    rpm_mean = _safe_float(
        race.get("rpm_mean", 0),
        0
    )

    rpm_max = _safe_float(
        race.get("rpm_max", rpm_mean),
        rpm_mean
    )

    gear_mean = _safe_float(
        race.get("gear_mean", 0),
        0
    )

    gear_max = _safe_float(
        race.get("gear_max", gear_mean),
        gear_mean
    )

    gear_std = _safe_float(
        race.get("gear_std", 0),
        0
    )

    power_braking_balance = _safe_float(
        race.get("power_braking_balance", 0),
        0
    )

    tyre_life = _safe_float(
        race.get(
            "tyre_life",
            race.get("tyre_age", 0)
        ),
        0
    )

    tyre_life_squared = tyre_life * tyre_life

    position_ahead = max(1.0, position - 1.0)

    compound = str(
        race.get(
            "compound",
            race.get("tyre_compound", "MEDIUM")
        )
    ).upper()

    track_status = str(
        race.get("track_status", "1")
    )

    return {
        "lap": lap,
        "position": position,
        "lap_time": lap_time,
        "previous_lap_time": previous_lap_time,

        "speed_mean": speed_mean,
        "speed_max": speed_max,
        "speed_min": speed_min,
        "speed_range": speed_range,
        "speed_std": speed_std,
        "speed_variation": speed_variation,

        "throttle_mean": throttle_mean,
        "throttle_max": throttle_max,
        "throttle_full_usage": throttle_full_usage,

        "brake_mean": brake_mean,
        "brake_max": brake_max,
        "brake_usage": brake_usage,
        "heavy_braking_usage": heavy_braking_usage,

        "rpm_mean": rpm_mean,
        "rpm_max": rpm_max,

        "gear_mean": gear_mean,
        "gear_max": gear_max,
        "gear_std": gear_std,

        "power_braking_balance": power_braking_balance,

        "tyre_life": tyre_life,
        "tyre_life_squared": tyre_life_squared,

        "position_ahead": position_ahead,

        "compound": compound,
        "track_status": track_status
    }


# ============================================================
# RAW ML PROBABILITY
# ============================================================

def calculate_ml_probability(race):

    if not _load_model():
        return None

    try:
        features = build_ml_features(race)
        dataframe = pd.DataFrame([features])

        probabilities = ML_MODEL.predict_proba(dataframe)

        if (
            getattr(probabilities, "ndim", 0) != 2
            or probabilities.shape[1] < 2
        ):
            raise ValueError(
                f"Unexpected probability shape: "
                f"{getattr(probabilities, 'shape', None)}"
            )

        return clamp(float(probabilities[0][1]))

    except Exception as error:
        global ML_ERROR
        ML_ERROR = f"{type(error).__name__}: {error}"
        print(f"[ML] Prediction failed: {ML_ERROR}")
        return None


# ============================================================
# GAP SCORE
# ============================================================

def calculate_gap_score(gap):
    gap = max(0.0, _safe_float(gap, 99.0))

    if gap <= 0.20:
        return 1.00
    if gap <= 0.30:
        return 0.95
    if gap <= 0.40:
        return 0.88
    if gap <= 0.50:
        return 0.78
    if gap <= 0.60:
        return 0.62
    if gap <= 0.75:
        return 0.42
    if gap <= 0.90:
        return 0.24
    if gap <= 1.10:
        return 0.10

    return 0.0


# ============================================================
# SECTOR SCORE
# ============================================================

def calculate_sector_score(race):
    return clamp(
        _safe_float(
            race.get("sector_overtaking_base", 0.50),
            0.50
        )
    )


# ============================================================
# PACE SCORE
# ============================================================

def calculate_pace_score(race):
    pace = clamp(
        _safe_float(
            race.get("pace_advantage", 0.50),
            0.50
        )
    )

    return clamp(
        0.50 + (pace - 0.50) * 1.50
    )


# ============================================================
# TYRE SCORE
# ============================================================

def calculate_tyre_score(race):
    return clamp(
        _safe_float(
            race.get("tyre_advantage", 0.50),
            0.50
        )
    )


# ============================================================
# BATTERY SCORE
# ============================================================

def calculate_battery_score(race):
    battery = _safe_float(
        race.get("battery", 100),
        100
    )

    if battery >= 70:
        return 1.00
    if battery >= 50:
        return 0.90
    if battery >= 35:
        return 0.75
    if battery >= 25:
        return 0.55
    if battery >= 15:
        return 0.35

    return 0.15


# ============================================================
# RACE CONDITION
# ============================================================

def calculate_race_condition_factor(race):
    condition = str(
        race.get("race_condition", "NORMAL")
    ).upper()

    if condition == "SAFETY CAR":
        return 0.05

    if condition == "VSC":
        return 0.20

    if condition == "WET":
        return 0.80

    return 1.00


# ============================================================
# TRACK LIMITS
# ============================================================

def calculate_track_factor(race):
    risk = clamp(
        _safe_float(
            race.get("track_limit_risk", 0),
            0
        )
    )

    return clamp(
        1.0 - 0.20 * risk
    )


# ============================================================
# HEURISTIC PROBABILITY
# ============================================================

def calculate_heuristic_probability(race):

    gap_score = calculate_gap_score(
        race.get("gap_ahead", 99)
    )

    sector_score = calculate_sector_score(race)
    pace_score = calculate_pace_score(race)
    tyre_score = calculate_tyre_score(race)
    battery_score = calculate_battery_score(race)

    opportunity = clamp(
        _safe_float(
            race.get("overtake_opportunity", 0.50),
            0.50
        )
    )

    future = clamp(
        _safe_float(
            race.get("future_opportunity", 0.50),
            0.50
        )
    )

    condition_factor = calculate_race_condition_factor(race)
    track_factor = calculate_track_factor(race)

    # Current gap is deliberately dominant because the simulator
    # is making a real-time decision, not predicting a historical
    # lap-to-lap position change in isolation.
    score = (
        0.38 * gap_score
        + 0.18 * sector_score
        + 0.15 * pace_score
        + 0.10 * tyre_score
        + 0.07 * battery_score
        + 0.07 * opportunity
        + 0.05 * future
    )

    score *= condition_factor
    score *= track_factor

    return clamp(score)


# ============================================================
# HYBRID PROBABILITY
# ============================================================

def calculate_overtake_probability(race):

    ml_probability = calculate_ml_probability(race)
    heuristic_probability = calculate_heuristic_probability(race)

    if ml_probability is None:
        return heuristic_probability

    gap = max(
        0.0,
        _safe_float(
            race.get("gap_ahead", 99),
            99
        )
    )

    sector = calculate_sector_score(race)
    pace = calculate_pace_score(race)
    tyre = calculate_tyre_score(race)

    condition = str(
        race.get("race_condition", "NORMAL")
    ).upper()

    # --------------------------------------------------------
    # Base hybrid
    # --------------------------------------------------------
    #
    # ML provides learned telemetry context.
    # Heuristics provide the simulator's current race state.
    #
    # We intentionally do NOT allow ML to dominate the decision.
    # --------------------------------------------------------

    # The simulator does not have raw lap telemetry, so the historical
    # telemetry model is treated as supporting evidence rather than the
    # primary decision signal.
    hybrid = (
        0.30 * ml_probability
        + 0.70 * heuristic_probability
    )

    # --------------------------------------------------------
    # Gap correction
    # --------------------------------------------------------
    #
    # Historical ML cannot directly know the simulator's current
    # gap because gap is not a training feature.
    #
    # Therefore current gap gets an explicit correction.
    # --------------------------------------------------------

    if gap <= 0.30:
        hybrid += 0.20

    elif gap <= 0.40:
        hybrid += 0.15

    elif gap <= 0.50:
        hybrid += 0.10

    elif gap <= 0.60:
        hybrid += 0.05

    elif gap > 1.20:
        hybrid -= 0.18

    elif gap > 0.90:
        hybrid -= 0.10

    # --------------------------------------------------------
    # Strong opportunity correction
    # --------------------------------------------------------

    opportunity = clamp(
        _safe_float(
            race.get("overtake_opportunity", 0.50),
            0.50
        )
    )

    if opportunity >= 0.75:
        hybrid += 0.07
    elif opportunity >= 0.60:
        hybrid += 0.035
    elif opportunity < 0.25:
        hybrid -= 0.06

    # --------------------------------------------------------
    # Sector correction
    # --------------------------------------------------------

    if sector >= 0.70:
        hybrid += 0.07
    elif sector < 0.30:
        hybrid -= 0.10

    # --------------------------------------------------------
    # Pace correction
    # --------------------------------------------------------

    if pace >= 0.70:
        hybrid += 0.07
    elif pace < 0.35:
        hybrid -= 0.08

    # --------------------------------------------------------
    # Tyre correction
    # --------------------------------------------------------

    if tyre >= 0.70:
        hybrid += 0.04
    elif tyre < 0.30:
        hybrid -= 0.08

    # --------------------------------------------------------
    # Race control
    # --------------------------------------------------------

    if condition in ("VSC", "SAFETY CAR"):
        hybrid = min(hybrid, 0.08)

    # --------------------------------------------------------
    # Battery
    # --------------------------------------------------------

    battery = _safe_float(
        race.get("battery", 100),
        100
    )

    if battery < 15:
        hybrid *= 0.45
    elif battery < 25:
        hybrid *= 0.70

    # --------------------------------------------------------
    # Track limits
    # --------------------------------------------------------

    hybrid *= calculate_track_factor(race)

    return clamp(hybrid)


# ============================================================
# ATTACK DECISION
# ============================================================

def attack_is_allowed(race):

    position = int(
        _safe_float(
            race.get("position", 10),
            10
        )
    )

    if position <= 1:
        return False

    condition = str(
        race.get("race_condition", "NORMAL")
    ).upper()

    if condition in ("VSC", "SAFETY CAR"):
        return False

    gap = _safe_float(
        race.get("gap_ahead", 99),
        99
    )

    if gap > 1.20:
        return False

    sector = calculate_sector_score(race)

    # A poor overtaking sector can still be attacked if the cars
    # are already extremely close.
    if sector < 0.25 and gap > 0.45:
        return False

    return True


# ============================================================
# RECOMMENDATION
# ============================================================

def get_overtake_recommendation(race):

    probability = calculate_overtake_probability(race)

    gap = _safe_float(
        race.get("gap_ahead", 99),
        99
    )

    threat = clamp(
        _safe_float(
            race.get("threat_level", 0.40),
            0.40
        )
    )

    opportunity = clamp(
        _safe_float(
            race.get("overtake_opportunity", 0.50),
            0.50
        )
    )

    sector = calculate_sector_score(race)
    pace = calculate_pace_score(race)
    tyre = calculate_tyre_score(race)
    battery = calculate_battery_score(race)

    condition = str(
        race.get("race_condition", "NORMAL")
    ).upper()

    if condition in ("VSC", "SAFETY CAR"):
        return "DEFEND" if threat >= 0.70 else "STAY"

    if not attack_is_allowed(race):
        if threat >= 0.72:
            return "DEFEND"
        return "STAY"

    # --------------------------------------------------------
    # Clear immediate attack windows.
    # Current gap is intentionally dominant here.
    # --------------------------------------------------------

    if gap <= 0.35:
        if (
            sector >= 0.45
            and pace >= 0.42
            and tyre >= 0.30
            and battery >= 0.30
        ):
            return "ATTACK"

    if gap <= 0.50:
        if (
            probability >= 0.40
            and sector >= 0.50
            and pace >= 0.45
        ):
            return "ATTACK"

        if (
            opportunity >= 0.65
            and sector >= 0.60
            and pace >= 0.50
            and tyre >= 0.45
        ):
            return "ATTACK"

    if gap <= 0.65:
        if (
            probability >= 0.55
            and sector >= 0.60
            and pace >= 0.55
        ):
            return "ATTACK"

    # --------------------------------------------------------
    # Wider attack window only when ML + race state agree.
    # --------------------------------------------------------

    if (
        probability >= 0.62
        and gap <= 0.85
        and sector >= 0.65
        and pace >= 0.60
    ):
        return "ATTACK"

    # --------------------------------------------------------
    # Defence must be driven by the actual rear threat.
    # --------------------------------------------------------

    if threat >= 0.78 and gap > 0.70:
        return "DEFEND"

    return "STAY"


# ============================================================
# LEGACY / COMPATIBILITY API
# ============================================================

def calculate_overtake_probability_details(race):
    ml_probability = calculate_ml_probability(race)
    heuristic_probability = calculate_heuristic_probability(race)
    hybrid_probability = calculate_overtake_probability(race)

    return {
        "ml_probability": ml_probability,
        "heuristic_probability": heuristic_probability,
        "hybrid_probability": hybrid_probability,
        "recommendation": get_overtake_recommendation(race),
        "threshold": MODEL_THRESHOLD,
        "model_available": ML_AVAILABLE
    }


def calculate_overall_probability(race):
    return calculate_overtake_probability(race)


def predict_overtake(race):
    probability = calculate_overtake_probability(race)

    return {
        "probability": probability,
        "recommendation": get_overtake_recommendation(race),
        "model_available": ML_AVAILABLE
    }


# ============================================================
# INITIAL MODEL CHECK
# ============================================================

_load_model()