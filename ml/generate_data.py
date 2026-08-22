import csv
import os
import random
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)


# ============================================================
# IMPORT SIMULATOR
# ============================================================

from simulator.race import RaceSimulator


# ============================================================
# CONFIGURATION
# ============================================================

NUMBER_OF_RACES = 500

OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "overtake_dataset.csv"
)


DEPLOYMENT_MODES = [
    "PUSH",
    "BALANCED",
    "HARVEST",
    "CONSERVE"
]


RECOMMENDATIONS = [
    "ATTACK",
    "STAY",
    "DEFEND"
]


# ============================================================
# GENERATE DATA
# ============================================================

def generate_dataset():

    rows = []

    print()
    print("=" * 60)
    print("GENERATING OVERTAKE TRAINING DATA")
    print("=" * 60)

    for race_number in range(
        NUMBER_OF_RACES
    ):

        simulator = RaceSimulator()

        while True:

            race = simulator.get_state()

            # ------------------------------------------------
            # Stop if race is finished
            # ------------------------------------------------

            if (
                race["lap"]
                >= race["total_laps"]
                and race["sector"] == 3
            ):
                break


            # ------------------------------------------------
            # Random strategy/deployment
            #
            # We intentionally randomize these so the ML model
            # sees different race situations.
            # ------------------------------------------------

            deployment_mode = random.choice(
                DEPLOYMENT_MODES
            )

            recommendation = random.choice(
                RECOMMENDATIONS
            )


            # ------------------------------------------------
            # Record state BEFORE the sector is simulated
            # ------------------------------------------------

            row = {

                # Race state
                "lap":
                    race["lap"],

                "sector":
                    race["sector"],

                "position":
                    race["position"],

                # Energy
                "battery":
                    race["battery"],

                # Gaps
                "gap_ahead":
                    race["gap_ahead"],

                "gap_behind":
                    race["gap_behind"],

                # Tyres
                "tyre_advantage":
                    race["tyre_advantage"],

                # Pace
                "pace_advantage":
                    race["pace_advantage"],

                # Overtake
                "overtake_opportunity":
                    race["overtake_opportunity"],

                "future_opportunity":
                    race["future_opportunity"],

                # Threat
                "threat_level":
                    race["threat_level"],

                # Sector characteristics
                "sector_type":
                    race["sector_type"],

                "sector_energy_demand":
                    race["sector_energy_demand"],

                "sector_overtaking_base":
                    race["sector_overtaking_base"],

                "sector_braking_importance":
                    race["sector_braking_importance"],

                "sector_traction_importance":
                    race["sector_traction_importance"],

                # Driver decision
                "deployment_mode":
                    deployment_mode,

                "recommendation":
                    recommendation
            }


            # ------------------------------------------------
            # Simulate this sector
            # ------------------------------------------------

            result = simulator.update(
                deployment_mode,
                recommendation
            )


            # ------------------------------------------------
            # TARGET
            #
            # 1 = successful overtake
            # 0 = no successful overtake
            # ------------------------------------------------

            row["overtake_success"] = (
                1
                if result["overtook"]
                else 0
            )


            rows.append(row)


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            race_number + 1
        ) % 25 == 0:

            print(
                f"Generated "
                f"{race_number + 1} / "
                f"{NUMBER_OF_RACES} races"
            )


    # ========================================================
    # WRITE CSV
    # ========================================================

    fieldnames = list(
        rows[0].keys()
    )


    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


    print()
    print("=" * 60)
    print("DATASET GENERATED")
    print("=" * 60)

    print(
        f"Rows: {len(rows)}"
    )

    print(
        f"File: {OUTPUT_FILE}"
    )

    successful = sum(
        row["overtake_success"]
        for row in rows
    )

    print(
        f"Successful overtakes: "
        f"{successful}"
    )

    print(
        f"Non-overtakes: "
        f"{len(rows) - successful}"
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_dataset()