from .overtake import calculate_overtake_probability
from .retention import calculate_retention_probability
from .strategy import evaluate_strategy
from .rules import check_attack_allowed


def run_what_if(race, strategy_weights=None):

    # Default weights
    if strategy_weights is None:

        strategy_weights = {
            "overtake": 1.0,
            "retention": 1.0,
            "current_opportunity": 1.0,
            "future_opportunity": 1.0,
            "energy": 1.0,
            "tyres": 1.0,
            "threat": 1.0
        }

    scenarios = {}

    # ========================================================
    # ATTACK
    # ========================================================

    attack_race = race.copy()

    attack_race["overtake_opportunity"] = min(
        1.0,
        attack_race["overtake_opportunity"] + 0.15
    )

    attack_race["pace_advantage"] = min(
        1.0,
        attack_race["pace_advantage"] + 0.10
    )

    attack_probability = (
        calculate_overtake_probability(
            attack_race
        )
    )

    attack_retention = (
        calculate_retention_probability(
            attack_race,
            "PUSH"
        )
    )

    attack_scores, _ = evaluate_strategy(
        attack_race,
        "PUSH",
        strategy_weights
    )

    attack_allowed = check_attack_allowed(
        attack_race,
        {
            "target_energy_per_lap":
                5.0
        }
    )

    attack_position = attack_race["position"]

    if (
        attack_allowed
        and attack_probability >= 0.65
        and attack_race["position"] > 1
    ):

        attack_position -= 1


    scenarios["ATTACK"] = {

        "score":
            attack_scores["ATTACK"],

        "overtake_probability":
            attack_probability,

        "retention_probability":
            attack_retention,

        "position":
            max(
                1,
                attack_position
            ),

        "allowed":
            attack_allowed
    }


    # ========================================================
    # STAY
    # ========================================================

    stay_race = race.copy()

    stay_probability = (
        calculate_retention_probability(
            stay_race,
            "BALANCED"
        )
    )

    stay_scores, _ = evaluate_strategy(
        stay_race,
        "BALANCED",
        strategy_weights
    )

    scenarios["STAY"] = {

        "score":
            stay_scores["STAY"],

        "overtake_probability":
            calculate_overtake_probability(
                stay_race
            ),

        "retention_probability":
            stay_probability,

        "position":
            stay_race["position"],

        "allowed":
            True
    }


    # ========================================================
    # DEFEND
    # ========================================================

    defend_race = race.copy()

    defend_race["threat_level"] = min(
        1.0,
        defend_race["threat_level"] + 0.10
    )

    defend_probability = (
        calculate_retention_probability(
            defend_race,
            "PUSH"
        )
    )

    defend_scores, _ = evaluate_strategy(
        defend_race,
        "PUSH",
        strategy_weights
    )

    defend_position = (
        defend_race["position"]
    )

    # Higher retention means lower chance
    # of losing the position.

    if defend_probability < 0.40:

        defend_position += 1

    scenarios["DEFEND"] = {

        "score":
            defend_scores["DEFEND"],

        "overtake_probability":
            calculate_overtake_probability(
                defend_race
            ),

        "retention_probability":
            defend_probability,

        "position":
            min(
                20,
                defend_position
            ),

        "allowed":
            True
    }


    return scenarios