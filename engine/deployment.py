def get_remaining_laps(race):
    """
    Calculate remaining laps in the race.
    """

    return max(
        1,
        race["total_laps"] - race["lap"]
    )


def get_deployment_target(race, deployment_mode):
    """
    Calculate energy deployment for the current lap.

    Energy model:
        100 MJ = 100% battery

    Baseline:
        Sustainable energy available per remaining lap.

    Target:
        Recommended energy deployment based on AI mode.
    """

    battery_mj = max(
        0.0,
        race["battery"]
    )

    remaining_laps = get_remaining_laps(
        race
    )

    # ========================================================
    # BASELINE ENERGY
    # ========================================================

    baseline = (
        battery_mj
        / remaining_laps
    )

    # ========================================================
    # DEPLOYMENT MULTIPLIERS
    # ========================================================

    multipliers = {

        "PUSH": 1.35,

        "BALANCED": 1.00,

        "HARVEST": 0.65,

        "CONSERVE": 0.40
    }

    multiplier = multipliers.get(
        deployment_mode,
        1.00
    )

    # ========================================================
    # TARGET ENERGY
    # ========================================================

    target = (
        baseline
        * multiplier
    )

    # Maximum energy that can be deployed
    # in one lap in our simplified model.

    max_deployment = 8.5

    target = min(
        target,
        max_deployment
    )

    # Never deploy more energy than available.

    target = min(
        target,
        battery_mj
    )

    # ========================================================
    # PROJECTED BATTERY
    # ========================================================

    if deployment_mode in [
        "PUSH",
        "BALANCED"
    ]:

        projected_battery = (
            battery_mj
            - target
        )

    else:

        # For HARVEST / CONSERVE,
        # energy usage is lower than baseline.
        # The difference is treated as recovered energy.

        recovery = max(
            0.0,
            baseline - target
        )

        projected_battery = (
            battery_mj
            + recovery
        )

    projected_battery = max(
        0.0,
        min(
            100.0,
            projected_battery
        )
    )

    # ========================================================
    # PERCENTAGES
    # ========================================================

    if battery_mj > 0:

        target_percentage = (
            target
            / battery_mj
        ) * 100

        baseline_percentage = (
            baseline
            / battery_mj
        ) * 100

    else:

        target_percentage = 0.0

        baseline_percentage = 0.0

    projected_percentage = (
        projected_battery
        / 100.0
    ) * 100.0

    return {

        "mode":
            deployment_mode,

        "target_energy_per_lap":
            round(
                target,
                2
            ),

        "baseline_energy_per_lap":
            round(
                baseline,
                2
            ),

        "target_percentage":
            round(
                target_percentage,
                1
            ),

        "baseline_percentage":
            round(
                baseline_percentage,
                1
            ),

        "battery_mj":
            round(
                battery_mj,
                2
            ),

        "remaining_laps":
            remaining_laps,

        "projected_battery_mj":
            round(
                projected_battery,
                2
            ),

        "projected_battery_percentage":
            round(
                projected_percentage,
                1
            ),

        "multiplier":
            multiplier
    }