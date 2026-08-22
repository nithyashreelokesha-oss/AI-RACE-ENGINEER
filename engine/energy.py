# ============================================================
# ENGINE / ENERGY.PY
# Sector-level energy deployment system
# ============================================================


def clamp(value, minimum=0.0, maximum=1.0):
    return max(
        minimum,
        min(float(value), maximum)
    )


# ============================================================
# SECTOR ENERGY MULTIPLIERS
# ============================================================

SECTOR_MULTIPLIERS = {

    "STRAIGHT": 1.15,

    "HIGH_SPEED": 1.10,

    "BRAKING": 0.90,

    "TECHNICAL": 0.85,

    "TRACTION": 1.05,

    "MIXED": 1.00
}


# ============================================================
# DEPLOYMENT MODE MULTIPLIERS
# ============================================================

DEPLOYMENT_MULTIPLIERS = {

    "PUSH": 1.20,

    "BALANCED": 1.00,

    "CONSERVE": 0.75,

    "HARVEST": 0.55
}


# ============================================================
# BASELINE ENERGY
# ============================================================

def calculate_baseline_energy(race):

    """
    Calculates the normal energy requirement
    for the CURRENT SECTOR.
    """

    sector_demand = float(
        race.get(
            "sector_energy_demand",
            1.0
        )
    )

    sector_type = race.get(
        "sector_type",
        "MIXED"
    )

    sector_multiplier = SECTOR_MULTIPLIERS.get(
        sector_type,
        1.0
    )

    baseline_energy = (
        sector_demand
        * sector_multiplier
    )

    return max(
        0.1,
        baseline_energy
    )


# ============================================================
# DEPLOYMENT MODE DECISION
# ============================================================

def get_deployment_mode(
    race,
    strategy_weights=None
):

    """
    Determines the deployment mode for the CURRENT SECTOR.

    The decision is deterministic.

    PUSH:
        Strong immediate opportunity.

    BALANCED:
        Normal race management.

    CONSERVE:
        Battery is getting low or defensive pressure
        requires energy preservation.

    HARVEST:
        Current opportunity is weak and a stronger
        opportunity is expected soon.
    """

    if strategy_weights is None:

        strategy_weights = {}


    # ========================================================
    # STATE
    # ========================================================

    battery = float(
        race.get(
            "battery",
            100.0
        )
    )

    tyre = clamp(
        race.get(
            "tyre_advantage",
            0.7
        )
    )

    opportunity = clamp(
        race.get(
            "overtake_opportunity",
            0.5
        )
    )

    future_opportunity = clamp(
        race.get(
            "future_opportunity",
            0.5
        )
    )

    gap_ahead = float(
        race.get(
            "gap_ahead",
            1.0
        )
    )

    threat = clamp(
        race.get(
            "threat_level",
            0.4
        )
    )

    sector_demand = float(
        race.get(
            "sector_energy_demand",
            1.0
        )
    )

    sector_type = race.get(
        "sector_type",
        "MIXED"
    )

    lap = int(
        race.get(
            "lap",
            1
        )
    )

    total_laps = int(
        race.get(
            "total_laps",
            57
        )
    )

    remaining_laps = max(
        0,
        total_laps - lap
    )


    # ========================================================
    # WEIGHTS
    # ========================================================

    energy_weight = float(
        strategy_weights.get(
            "energy",
            1.0
        )
    )

    overtake_weight = float(
        strategy_weights.get(
            "overtake",
            1.0
        )
    )

    future_weight = float(
        strategy_weights.get(
            "future_opportunity",
            1.0
        )
    )

    tyre_weight = float(
        strategy_weights.get(
            "tyres",
            1.0
        )
    )

    threat_weight = float(
        strategy_weights.get(
            "threat",
            1.0
        )
    )


    # ========================================================
    # BATTERY RESERVE LOGIC
    # ========================================================

    # Battery required per remaining lap.
    #
    # This prevents the AI from continuously spending
    # energy simply because the current battery percentage
    # is still high.

    baseline_energy = calculate_baseline_energy(
        race
    )

    estimated_remaining_energy_need = (
        baseline_energy
        * remaining_laps
    )

    # A percentage-based reserve is used for the prototype.
    reserve_ratio = 0.22

    energy_reserve = (
        estimated_remaining_energy_need
        * reserve_ratio
    )


    # --------------------------------------------------------
    # Critical battery
    # --------------------------------------------------------

    if battery < 15:

        return "HARVEST"


    # --------------------------------------------------------
    # Low battery
    # --------------------------------------------------------

    if battery < 25:

        if threat >= 0.70:

            return "CONSERVE"

        return "HARVEST"


    # ========================================================
    # NORMALIZED FACTORS
    # ========================================================

    # --------------------------------------------------------
    # Gap score
    # --------------------------------------------------------

    if gap_ahead <= 0.30:

        gap_score = 1.00

    elif gap_ahead <= 0.50:

        gap_score = 0.90

    elif gap_ahead <= 0.70:

        gap_score = 0.75

    elif gap_ahead <= 1.00:

        gap_score = 0.55

    elif gap_ahead <= 1.30:

        gap_score = 0.35

    else:

        gap_score = 0.15


    # --------------------------------------------------------
    # Sector opportunity
    # --------------------------------------------------------

    opportunity_score = (
        opportunity
        * overtake_weight
    )


    # --------------------------------------------------------
    # Tyre readiness
    # --------------------------------------------------------

    tyre_score = (
        tyre
        * tyre_weight
    )


    # --------------------------------------------------------
    # Immediate attack value
    # --------------------------------------------------------

    immediate_attack = (

        opportunity_score * 0.45

        + gap_score
        * overtake_weight
        * 0.30

        + tyre_score
        * 0.15

        + clamp(
            sector_demand / 1.5
        )
        * 0.10
    )


    # ========================================================
    # FUTURE OPPORTUNITY
    # ========================================================

    future_score = (
        future_opportunity
        * future_weight
    )


    # ========================================================
    # DEFENSIVE PRESSURE
    # ========================================================

    defensive_pressure = (
        threat
        * threat_weight
    )


    # ========================================================
    # SECTOR CHARACTER
    # ========================================================

    # These sectors are more suitable for deployment.

    high_value_sector = (

        sector_type in (
            "STRAIGHT",
            "HIGH_SPEED",
            "TRACTION"
        )
    )


    technical_sector = (

        sector_type in (
            "TECHNICAL",
            "BRAKING"
        )
    )


    # ========================================================
    # ENERGY STRESS
    # ========================================================

    # If battery is disproportionately low compared with
    # the energy still needed for the race, protect it.

    energy_stress = 0.0

    if estimated_remaining_energy_need > 0:

        energy_ratio = (
            battery
            / estimated_remaining_energy_need
        )

        if energy_ratio < 0.70:

            energy_stress = 1.0

        elif energy_ratio < 1.00:

            energy_stress = 0.65

        elif energy_ratio < 1.20:

            energy_stress = 0.30


    # ========================================================
    # CONSERVE DECISION
    # ========================================================

    if battery < 35:

        if defensive_pressure > 0.65:

            return "CONSERVE"

        if energy_stress >= 0.65:

            return "CONSERVE"


    # ========================================================
    # HARVEST DECISION
    # ========================================================

    # If the next opportunity is clearly better than the
    # current one, save energy instead of attacking now.

    future_advantage = (
        future_score
        - immediate_attack
    )


    if (

        future_advantage > 0.18

        and opportunity < 0.60

        and battery < 70

    ):

        return "HARVEST"


    # ========================================================
    # PUSH DECISION
    # ========================================================

    # IMPORTANT:
    #
    # PUSH now requires a genuinely strong combination:
    #
    #   1. Good current opportunity
    #   2. Close car
    #   3. Good tyres
    #   4. Suitable sector
    #   5. Enough battery
    #
    # This prevents PUSH from becoming the default mode.

    push_allowed = (

        battery >= 45

        and tyre >= 0.45

        and opportunity >= 0.62

        and gap_ahead <= 0.80

        and immediate_attack >= 0.62

        and high_value_sector
    )


    if push_allowed:

        return "PUSH"


    # ========================================================
    # DEFENSIVE BALANCED MODE
    # ========================================================

    if (

        defensive_pressure >= 0.70

        and battery >= 30

    ):

        return "BALANCED"


    # ========================================================
    # BALANCED MODE
    # ========================================================

    # Strong current opportunity but not strong enough
    # for PUSH.

    if (

        opportunity >= 0.45

        and battery >= 35

    ):

        return "BALANCED"


    # ========================================================
    # TECHNICAL / LOW-OPPORTUNITY SECTORS
    # ========================================================

    if technical_sector:

        if future_opportunity > opportunity:

            return "HARVEST"

        return "BALANCED"


    # ========================================================
    # DEFAULT
    # ========================================================

    return "BALANCED"


# ============================================================
# TARGET DEPLOYMENT
# ============================================================

def calculate_deployment(
    race,
    deployment_mode
):

    """
    Calculates energy deployment for the CURRENT SECTOR.

    baseline_energy:
        Normal physical energy requirement.

    target_energy:
        Energy actually planned for this sector based
        on deployment mode.
    """

    battery = float(
        race.get(
            "battery",
            100.0
        )
    )


    total_laps = int(
        race.get(
            "total_laps",
            57
        )
    )

    current_lap = int(
        race.get(
            "lap",
            1
        )
    )

    remaining_laps = max(
        0,
        total_laps - current_lap
    )


    # ========================================================
    # CURRENT SECTOR
    # ========================================================

    sector_type = race.get(
        "sector_type",
        "MIXED"
    )


    # ========================================================
    # BASELINE
    # ========================================================

    baseline_energy = calculate_baseline_energy(
        race
    )


    # ========================================================
    # DEPLOYMENT MULTIPLIER
    # ========================================================

    deployment_multiplier = (
        DEPLOYMENT_MULTIPLIERS.get(
            deployment_mode,
            1.0
        )
    )


    # ========================================================
    # TARGET
    # ========================================================

    target_energy = (
        baseline_energy
        * deployment_multiplier
    )


    # ========================================================
    # BATTERY PROTECTION
    # ========================================================

    if battery < 20:

        target_energy = min(
            target_energy,
            baseline_energy * 0.60
        )

    elif battery < 30:

        target_energy = min(
            target_energy,
            baseline_energy * 0.75
        )

    elif battery < 40:

        target_energy = min(
            target_energy,
            baseline_energy * 0.90
        )


    # ========================================================
    # DEPLOYMENT %
    # ========================================================

    if baseline_energy > 0:

        target_percentage = (
            target_energy
            / baseline_energy
            * 100.0
        )

    else:

        target_percentage = 0.0


    baseline_percentage = 100.0


    # ========================================================
    # PROJECTED BATTERY
    # ========================================================

    projected_battery = max(
        0.0,
        battery - target_energy
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "deployment_mode":
            deployment_mode,

        "sector_type":
            sector_type,

        # Current sector
        "baseline_energy_per_sector":
            round(
                baseline_energy,
                3
            ),

        "target_energy_per_sector":
            round(
                target_energy,
                3
            ),

        # Full lap equivalent
        "baseline_energy_per_lap":
            round(
                baseline_energy * 3,
                3
            ),

        "target_energy_per_lap":
            round(
                target_energy * 3,
                3
            ),

        # Percentages
        "baseline_percentage":
            round(
                baseline_percentage,
                1
            ),

        "target_percentage":
            round(
                target_percentage,
                1
            ),

        # Battery
        "projected_battery_mj":
            round(
                projected_battery,
                2
            ),

        # Race
        "remaining_laps":
            remaining_laps
    }