from engine.energy import get_deployment_mode

from engine.overtake import (
    calculate_overtake_probability
)

from engine.retention import (
    calculate_retention_probability
)

from engine.strategy import (
    evaluate_strategy
)

from engine.explanation import (
    generate_explanation
)

from engine.rules import (
    check_constraints
)

from engine.whatif import (
    run_what_if
)

from engine.confidence import (
    calculate_confidence
)

from engine.opponent import (
    estimate_opponent_state
)


def run_decision_engine(race):

    # -------------------------------
    # ENERGY
    # -------------------------------

    deployment_mode = get_deployment_mode(
        race
    )


    # -------------------------------
    # OVERTAKE
    # -------------------------------

    overtake_probability = (
        calculate_overtake_probability(
            race
        )
    )


    # -------------------------------
    # RETENTION
    # -------------------------------

    retention_probability = (
        calculate_retention_probability(
            race,
            deployment_mode
        )
    )


    # -------------------------------
    # CONSTRAINTS
    # -------------------------------

    constraints = check_constraints(
        race
    )


    # -------------------------------
    # STRATEGY
    # -------------------------------

    scores, recommendation = (
        evaluate_strategy(
            race,
            deployment_mode
        )
    )


    # -------------------------------
    # WHY
    # -------------------------------

    explanation = generate_explanation(
        race,
        deployment_mode,
        recommendation,
        overtake_probability,
        retention_probability
    )


    # -------------------------------
    # WHAT IF
    # -------------------------------

    what_if = run_what_if(
        race
    )


    # -------------------------------
    # CONFIDENCE
    # -------------------------------

    confidence = calculate_confidence(
        race
    )


    # -------------------------------
    # OPPONENT
    # -------------------------------

    opponent = estimate_opponent_state(
        race
    )


    return {

        "deployment_mode":
            deployment_mode,

        "overtake_probability":
            overtake_probability,

        "retention_probability":
            retention_probability,

        "constraints":
            constraints,

        "strategic_scores":
            scores,

        "recommendation":
            recommendation,

        "explanation":
            explanation,

        "what_if":
            what_if,

        "confidence":
            confidence,

        "opponent":
            opponent
    }