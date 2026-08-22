# ============================================================
# RACE RULES / SAFETY CONSTRAINTS
# ============================================================

MAX_LAP_DEPLOYMENT = 8.5

END_OF_RACE_ENERGY_FLOOR = 5.0


# ============================================================
# DEPLOYMENT LEGALITY
# ============================================================

def deployment_is_legal(deployment):

    target = deployment.get(
        "target_energy_per_lap",
        0.0
    )

    # Cannot deploy negative energy.

    if target < 0:

        return False

    # Cannot exceed the maximum allowed
    # deployment per lap.

    if target > MAX_LAP_DEPLOYMENT:

        return False

    return True


# ============================================================
# ENERGY CHECK
# ============================================================

def enough_energy_for_race(
    race,
    target_energy
):

    remaining_laps = max(
        1,
        race["total_laps"]
        - race["lap"]
    )

    projected_energy = (
        race["battery"]
        - (
            target_energy
            * remaining_laps
        )
    )

    return (
        projected_energy
        >= END_OF_RACE_ENERGY_FLOOR
    )


# ============================================================
# ATTACK ELIGIBILITY
# ============================================================

def attack_is_allowed(
    race,
    deployment
):

    # --------------------------------------------------------
    # Cannot attack from P1
    # --------------------------------------------------------

    if race["position"] <= 1:

        return False

    # --------------------------------------------------------
    # Deployment must be legal
    # --------------------------------------------------------

    if not deployment_is_legal(
        deployment
    ):

        return False

    target = deployment.get(
        "target_energy_per_lap",
        0.0
    )

    battery = race.get(
        "battery",
        0.0
    )

    # --------------------------------------------------------
    # Need enough battery for the attack
    # --------------------------------------------------------

    if (
        battery - target
        < END_OF_RACE_ENERGY_FLOOR
    ):

        return False

    return True


# ============================================================
# RULE STATUS
# ============================================================

def get_rule_status(
    race,
    deployment
):

    deployment_legal = (
        deployment_is_legal(
            deployment
        )
    )

    attack_allowed = (
        attack_is_allowed(
            race,
            deployment
        )
    )

    return {

        "deployment_legal":
            deployment_legal,

        "attack_allowed":
            attack_allowed,

        "lap_deployment_limit":
            MAX_LAP_DEPLOYMENT,

        "minimum_energy_reserve":
            END_OF_RACE_ENERGY_FLOOR
    }
# ============================================================
# COMPATIBILITY FUNCTION
# ============================================================

def check_attack_allowed(
    race,
    deployment
):
    """
    Compatibility wrapper for whatif.py.

    Uses the same attack-rule logic as
    attack_is_allowed().
    """

    return attack_is_allowed(
        race,
        deployment
    )