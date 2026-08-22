import random

from engine.overtake import (
    calculate_overtake_probability
)

from engine.energy import (
    calculate_deployment
)


class RaceSimulator:

    # ==========================================================
    # SECTOR DEFINITIONS
    # ==========================================================

    SECTORS = {

        1: {
            "name": "Sector 1",
            "type": "HIGH_SPEED",
            "energy_demand": 1.05,
            "overtaking_base": 0.55,
            "braking_importance": 0.55,
            "traction_importance": 0.45
        },

        2: {
            "name": "Sector 2",
            "type": "TECHNICAL",
            "energy_demand": 0.90,
            "overtaking_base": 0.35,
            "braking_importance": 0.75,
            "traction_importance": 0.70
        },

        3: {
            "name": "Sector 3",
            "type": "STRAIGHT",
            "energy_demand": 1.15,
            "overtaking_base": 0.75,
            "braking_importance": 0.65,
            "traction_importance": 0.80
        }
    }

    TOTAL_SECTORS = 3


    # ==========================================================
    # TYRE COMPOUNDS
    # ==========================================================

    TYRE_PROFILES = {

        "SOFT": {
            "base_life": 18.0,
            "pace": 1.08,
            "wear": 1.25
        },

        "MEDIUM": {
            "base_life": 28.0,
            "pace": 1.04,
            "wear": 1.00
        },

        "HARD": {
            "base_life": 38.0,
            "pace": 1.00,
            "wear": 0.82
        },

        "INTERMEDIATE": {
            "base_life": 24.0,
            "pace": 1.02,
            "wear": 1.10
        },

        "WET": {
            "base_life": 20.0,
            "pace": 0.98,
            "wear": 1.05
        }
    }


    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):

        self.race = {

            "lap": 1,

            "total_laps": 57,

            "position": 6,


            # --------------------------------------------------
            # SECTOR
            # --------------------------------------------------

            "sector": 1,

            "sector_name": "Sector 1",

            "sector_type": "HIGH_SPEED",

            "sector_energy_demand": 1.05,

            "sector_overtaking_base": 0.55,

            "sector_braking_importance": 0.55,

            "sector_traction_importance": 0.45,


            # --------------------------------------------------
            # ENERGY
            # --------------------------------------------------

            "battery": 100.0,


            # --------------------------------------------------
            # GAPS
            # --------------------------------------------------

            "gap_ahead": 0.65,

            "gap_behind": 0.90,


            # --------------------------------------------------
            # TYRES
            # --------------------------------------------------

            "tyre_compound": "MEDIUM",

            "tyre_age": 0.0,

            "tyre_degradation": 0.0,

            "tyre_condition": "FRESH",

            "tyre_advantage": 0.89,

            "base_tyre_life": 28.0,

            "effective_tyre_life": 28.0,

            "tyre_life_remaining": 28.0,


            # --------------------------------------------------
            # PERFORMANCE
            # --------------------------------------------------

            "pace_advantage": 0.55,


            # --------------------------------------------------
            # OVERTAKING
            # --------------------------------------------------

            "overtake_opportunity": 0.55,

            "future_opportunity": 0.60,


            # --------------------------------------------------
            # DEFENCE
            # --------------------------------------------------

            "threat_level": 0.40,


            # --------------------------------------------------
            # RULES / CONTEXT
            # --------------------------------------------------

            "track_limit_risk": 0.05,

            "race_condition": "NORMAL",

            "drs_available": True,


            # --------------------------------------------------
            # EVENTS
            # --------------------------------------------------

            "last_overtake": False,

            "last_position_change": False,


            # --------------------------------------------------
            # DECISION
            # --------------------------------------------------

            "deployment_mode": "BALANCED",

            "recommendation": "STAY"
        }


    # ==========================================================
    # GET STATE
    # ==========================================================

    def get_state(self):

        return self.race.copy()


    # ==========================================================
    # APPLY SECTOR
    # ==========================================================

    def apply_sector(
        self,
        sector_number
    ):

        sector = self.SECTORS[
            sector_number
        ]

        self.race["sector"] = sector_number

        self.race["sector_name"] = (
            sector["name"]
        )

        self.race["sector_type"] = (
            sector["type"]
        )

        self.race["sector_energy_demand"] = (
            sector["energy_demand"]
        )

        self.race["sector_overtaking_base"] = (
            sector["overtaking_base"]
        )

        self.race["sector_braking_importance"] = (
            sector["braking_importance"]
        )

        self.race["sector_traction_importance"] = (
            sector["traction_importance"]
        )


    # ==========================================================
    # ENERGY
    # ==========================================================

    def update_energy(
        self,
        deployment_mode
    ):

        deployment = calculate_deployment(
            self.race,
            deployment_mode
        )

        target_energy = float(
            deployment.get(
                "target_energy_per_sector",
                0.0
            )
        )

        variation = random.uniform(
            0.94,
            1.06
        )

        actual_consumption = (
            target_energy
            * variation
        )

        self.race["battery"] -= (
            actual_consumption
        )

        self.race["battery"] = max(
            0.0,
            self.race["battery"]
        )

        return {

            "target_energy_per_sector":
                round(
                    target_energy,
                    3
                ),

            "actual_energy_per_sector":
                round(
                    actual_consumption,
                    3
                ),

            "target_energy_per_lap":
                round(
                    target_energy * 3,
                    3
                ),

            "baseline_energy_per_sector":
                round(
                    deployment.get(
                        "baseline_energy_per_sector",
                        0.0
                    ),
                    3
                ),

            "baseline_energy_per_lap":
                round(
                    deployment.get(
                        "baseline_energy_per_sector",
                        0.0
                    ) * 3,
                    3
                ),

            "target_percentage":
                deployment.get(
                    "target_percentage",
                    100.0
                ),

            "baseline_percentage":
                deployment.get(
                    "baseline_percentage",
                    100.0
                ),

            "projected_battery":
                round(
                    self.race["battery"],
                    2
                ),

            "remaining_laps":
                deployment.get(
                    "remaining_laps",
                    self.race["total_laps"]
                    - self.race["lap"]
                )
        }


    # ==========================================================
    # PACE
    # ==========================================================

    def update_pace(
        self,
        deployment_mode
    ):

        pace_change = {

            "PUSH": 0.035,

            "BALANCED": 0.010,

            "HARVEST": -0.015,

            "CONSERVE": -0.025

        }.get(
            deployment_mode,
            0.0
        )


        sector_type = self.race[
            "sector_type"
        ]


        if sector_type == "HIGH_SPEED":

            pace_change *= 1.05

        elif sector_type == "STRAIGHT":

            pace_change *= 1.10

        elif sector_type == "TECHNICAL":

            pace_change *= 0.90


        self.race[
            "pace_advantage"
        ] += pace_change


        # Wet conditions make pace less predictable.

        if self.race["race_condition"] == "WET":

            self.race[
                "pace_advantage"
            ] += random.uniform(
                -0.020,
                0.020
            )

        else:

            self.race[
                "pace_advantage"
            ] += random.uniform(
                -0.012,
                0.012
            )


        self.race[
            "pace_advantage"
        ] = max(
            0.0,
            min(
                1.0,
                self.race[
                    "pace_advantage"
                ]
            )
        )


    # ==========================================================
    # TYRE UPDATE
    # ==========================================================

    def update_tyres(
        self,
        deployment_mode
    ):

        compound = self.race.get(
            "tyre_compound",
            "MEDIUM"
        )

        profile = self.TYRE_PROFILES.get(
            compound,
            self.TYRE_PROFILES["MEDIUM"]
        )


        # ------------------------------------------------------
        # Deployment affects wear
        # ------------------------------------------------------

        mode_factor = {

            "PUSH": 1.22,

            "BALANCED": 1.00,

            "HARVEST": 0.82,

            "CONSERVE": 0.72

        }.get(
            deployment_mode,
            1.00
        )


        # ------------------------------------------------------
        # Sector affects wear
        # ------------------------------------------------------

        sector_factor = {

            "TECHNICAL": 1.15,

            "HIGH_SPEED": 1.05,

            "STRAIGHT": 0.90

        }.get(
            self.race["sector_type"],
            1.00
        )


        # ------------------------------------------------------
        # Track-limit risk
        # ------------------------------------------------------

        rule_wear_factor = (

            1.0

            + 0.20
            * float(
                self.race.get(
                    "track_limit_risk",
                    0.0
                )
            )
        )


        # ------------------------------------------------------
        # Wet conditions
        # ------------------------------------------------------

        weather_wear_factor = 1.0

        if self.race["race_condition"] == "WET":

            if compound in (
                "SOFT",
                "MEDIUM",
                "HARD"
            ):

                weather_wear_factor = 1.15


        # ------------------------------------------------------
        # Calculate effective tyre life
        # ------------------------------------------------------

        effective_life = (

            profile["base_life"]

            / (

                profile["wear"]

                * mode_factor

                * sector_factor

                * rule_wear_factor

                * weather_wear_factor
            )
        )


        effective_life = max(
            5.0,
            min(
                profile["base_life"] * 1.35,
                effective_life
            )
        )


        self.race[
            "effective_tyre_life"
        ] = effective_life


        self.race[
            "base_tyre_life"
        ] = profile[
            "base_life"
        ]


        # ------------------------------------------------------
        # One update = one sector = 1/3 lap
        # ------------------------------------------------------

        self.race[
            "tyre_age"
        ] += 1.0 / self.TOTAL_SECTORS


        # ------------------------------------------------------
        # Degradation
        # ------------------------------------------------------

        life_used = (

            1.0
            / effective_life
            * 100.0
        )


        self.race[
            "tyre_degradation"
        ] = max(

            0.0,

            min(

                100.0,

                self.race.get(
                    "tyre_degradation",
                    0.0
                )
                + life_used
            )
        )


        # ------------------------------------------------------
        # Tyre advantage
        # ------------------------------------------------------

        age_ratio = (

            self.race["tyre_age"]
            / max(
                effective_life,
                1.0
            )
        )


        compound_pace = (

            profile["pace"]
            - 1.0
        ) * 0.55


        self.race[
            "tyre_advantage"
        ] = max(

            0.0,

            min(

                1.0,

                0.92

                - age_ratio * 0.92

                + compound_pace
            )
        )


        # ------------------------------------------------------
        # Remaining life
        # ------------------------------------------------------

        self.race[
            "tyre_life_remaining"
        ] = max(

            0.0,

            effective_life
            - self.race["tyre_age"]
        )


        # ------------------------------------------------------
        # Tyre condition
        # ------------------------------------------------------

        tyre_value = self.race[
            "tyre_advantage"
        ]


        if tyre_value >= 0.75:

            self.race[
                "tyre_condition"
            ] = "FRESH"

        elif tyre_value >= 0.65:

            self.race[
                "tyre_condition"
            ] = "GOOD"

        elif tyre_value >= 0.35:

            self.race[
                "tyre_condition"
            ] = "MEDIUM"

        else:

            self.race[
                "tyre_condition"
            ] = "POOR"


    # ==========================================================
    # GAP UPDATE
    # ==========================================================

    def update_gaps(
        self,
        deployment_mode
    ):

        if self.race["position"] <= 1:

            self.race[
                "gap_ahead"
            ] = 0.0

        else:

            pace_effect = (

                self.race[
                    "pace_advantage"
                ]
                - 0.5
            )


            if deployment_mode == "PUSH":

                self.race[
                    "gap_ahead"
                ] -= pace_effect * 0.035

            elif deployment_mode == "BALANCED":

                self.race[
                    "gap_ahead"
                ] -= pace_effect * 0.015

            elif deployment_mode == "CONSERVE":

                self.race[
                    "gap_ahead"
                ] += 0.012

            elif deployment_mode == "HARVEST":

                self.race[
                    "gap_ahead"
                ] += 0.020


            self.race[
                "gap_ahead"
            ] += random.uniform(
                -0.025,
                0.025
            )


            self.race[
                "gap_ahead"
            ] = max(

                0.08,

                min(
                    3.0,
                    self.race[
                        "gap_ahead"
                    ]
                )
            )


        # ------------------------------------------------------
        # Gap behind
        # ------------------------------------------------------

        self.race[
            "gap_behind"
        ] += random.uniform(
            -0.035,
            0.035
        )


        if deployment_mode == "PUSH":

            self.race[
                "gap_behind"
            ] += 0.015

        elif deployment_mode == "CONSERVE":

            self.race[
                "gap_behind"
            ] -= 0.010

        elif deployment_mode == "HARVEST":

            self.race[
                "gap_behind"
            ] -= 0.015


        self.race[
            "gap_behind"
        ] = max(

            0.08,

            min(
                3.0,
                self.race[
                    "gap_behind"
                ]
            )
        )


    # ==========================================================
    # OVERTAKE OPPORTUNITY
    # ==========================================================

    def update_overtake_opportunity(self):

        base = self.race[
            "sector_overtaking_base"
        ]

        gap = self.race[
            "gap_ahead"
        ]

        pace = self.race[
            "pace_advantage"
        ]

        tyres = self.race[
            "tyre_advantage"
        ]


        opportunity = base


        # Gap

        if gap < 0.40:

            opportunity += 0.18

        elif gap < 0.70:

            opportunity += 0.08

        elif gap > 1.50:

            opportunity -= 0.18


        # Pace

        opportunity += (
            pace - 0.5
        ) * 0.25


        # Tyres

        opportunity += (
            tyres - 0.5
        ) * 0.15


        # DRS

        if (
            not self.race.get(
                "drs_available",
                True
            )
            and self.race["sector_type"]
            in (
                "HIGH_SPEED",
                "STRAIGHT"
            )
        ):

            opportunity -= 0.08


        # Wet

        if self.race["race_condition"] == "WET":

            opportunity -= 0.05


        # VSC / Safety Car

        if self.race["race_condition"] == "VSC":

            opportunity *= 0.45

        elif self.race["race_condition"] == "SAFETY CAR":

            opportunity *= 0.15


        # Track limits

        opportunity *= (

            1.0
            - 0.15
            * self.race.get(
                "track_limit_risk",
                0.0
            )
        )


        opportunity += random.uniform(
            -0.035,
            0.035
        )


        self.race[
            "overtake_opportunity"
        ] = max(

            0.0,

            min(
                1.0,
                opportunity
            )
        )


    # ==========================================================
    # FUTURE OPPORTUNITY
    # ==========================================================

    def update_future_opportunity(self):

        next_sector = (
            self.race["sector"] + 1
        )

        if next_sector > 3:

            next_sector = 1


        next_data = self.SECTORS[
            next_sector
        ]


        future = next_data[
            "overtaking_base"
        ]


        if self.race[
            "gap_ahead"
        ] < 0.6:

            future += 0.10


        future += random.uniform(
            -0.04,
            0.04
        )


        self.race[
            "future_opportunity"
        ] = max(

            0.0,

            min(
                1.0,
                future
            )
        )


    # ==========================================================
    # THREAT
    # ==========================================================

    def update_threat(self):

        gap = self.race[
            "gap_behind"
        ]

        threat = self.race[
            "threat_level"
        ]


        if gap < 0.40:

            threat += 0.10

        elif gap < 0.70:

            threat += 0.04

        elif gap > 1.30:

            threat -= 0.08

        else:

            threat += random.uniform(
                -0.025,
                0.025
            )


        if self.race[
            "tyre_advantage"
        ] < 0.35:

            threat += 0.05


        self.race[
            "threat_level"
        ] = max(

            0.0,

            min(
                1.0,
                threat
            )
        )


    # ==========================================================
    # OVERTAKE RESOLUTION
    # ==========================================================

    def resolve_overtake(
        self,
        deployment_mode,
        recommendation
    ):

        if self.race[
            "position"
        ] <= 1:

            self.race[
                "gap_ahead"
            ] = 0.0

            return False


        if recommendation != "ATTACK":

            return False


        sector_base = self.race[
            "sector_overtaking_base"
        ]


        if sector_base < 0.30:

            return False


        gap = self.race[
            "gap_ahead"
        ]


        if gap > 1.20:

            return False


        # ------------------------------------------------------
        # Race-control restrictions
        # ------------------------------------------------------

        if self.race[
            "race_condition"
        ] in (
            "VSC",
            "SAFETY CAR"
        ):

            return False


        probability = (
            calculate_overtake_probability(
                self.race
            )
        )


        execution_probability = (
            probability * 0.22
        )


        # Deployment

        if deployment_mode == "PUSH":

            execution_probability += 0.045

        elif deployment_mode == "BALANCED":

            execution_probability += 0.010

        elif deployment_mode in (
            "CONSERVE",
            "HARVEST"
        ):

            execution_probability -= 0.035


        # Sector

        execution_probability *= (

            0.70
            + sector_base * 0.50
        )


        # Battery

        if self.race[
            "battery"
        ] < 25:

            execution_probability *= 0.55

        elif self.race[
            "battery"
        ] < 40:

            execution_probability *= 0.75


        # Tyres

        if self.race[
            "tyre_advantage"
        ] < 0.30:

            execution_probability *= 0.55

        elif self.race[
            "tyre_advantage"
        ] < 0.45:

            execution_probability *= 0.80


        # Gap

        if gap > 0.90:

            execution_probability *= 0.60

        elif gap > 0.70:

            execution_probability *= 0.80


        # Track limits

        execution_probability *= (

            1.0
            - 0.20
            * self.race.get(
                "track_limit_risk",
                0.0
            )
        )


        # DRS

        if (
            not self.race.get(
                "drs_available",
                True
            )
            and self.race["sector_type"]
            in (
                "HIGH_SPEED",
                "STRAIGHT"
            )
        ):

            execution_probability *= 0.80


        # Hard realism cap

        execution_probability = max(

            0.0,

            min(
                execution_probability,
                0.20
            )
        )


        if random.random() <= (
            execution_probability
        ):

            self.race[
                "position"
            ] -= 1

            self.race[
                "last_overtake"
            ] = True

            self.race[
                "last_position_change"
            ] = True


            if self.race[
                "position"
            ] <= 1:

                self.race[
                    "position"
                ] = 1

                self.race[
                    "gap_ahead"
                ] = 0.0

            else:

                self.race[
                    "gap_ahead"
                ] = random.uniform(
                    0.15,
                    0.45
                )


            self.race[
                "gap_behind"
            ] = random.uniform(
                0.65,
                1.40
            )

            return True


        return False


    # ==========================================================
    # DEFENSIVE RISK
    # ==========================================================

    def resolve_defensive_risk(
        self,
        recommendation
    ):

        if self.race[
            "position"
        ] <= 1:

            self.race[
                "gap_ahead"
            ] = 0.0

            return False


        if recommendation == "DEFEND":

            return False


        threat = self.race[
            "threat_level"
        ]


        if threat > 0.85:

            chance = 0.12

        elif threat > 0.70:

            chance = 0.07

        elif threat > 0.55:

            chance = 0.035

        else:

            chance = 0.008


        if self.race[
            "tyre_advantage"
        ] < 0.30:

            chance += 0.04


        if self.race[
            "battery"
        ] < 25:

            chance += 0.035


        chance = min(
            chance,
            0.18
        )


        if random.random() <= chance:

            self.race[
                "position"
            ] += 1

            self.race[
                "last_position_change"
            ] = True

            self.race[
                "gap_behind"
            ] = random.uniform(
                0.60,
                1.30
            )

            return True


        return False


    # ==========================================================
    # ADVANCE SECTOR
    # ==========================================================

    def advance_sector(self):

        current_sector = self.race[
            "sector"
        ]


        if current_sector < 3:

            self.apply_sector(
                current_sector + 1
            )

            return False


        # Sector 3 → next lap

        self.race[
            "lap"
        ] += 1


        if self.race[
            "lap"
        ] > self.race[
            "total_laps"
        ]:

            self.race[
                "lap"
            ] = self.race[
                "total_laps"
            ]

            return True


        self.apply_sector(1)

        return False


    # ==========================================================
    # FULL UPDATE
    # ==========================================================

    def update(
        self,
        deployment_mode,
        recommendation
    ):

        self.race[
            "last_overtake"
        ] = False

        self.race[
            "last_position_change"
        ] = False


        self.race[
            "deployment_mode"
        ] = deployment_mode

        self.race[
            "recommendation"
        ] = recommendation


        completed_lap = self.race[
            "lap"
        ]

        completed_sector = self.race[
            "sector"
        ]

        completed_sector_name = self.race[
            "sector_name"
        ]

        completed_sector_type = self.race[
            "sector_type"
        ]


        # ------------------------------------------------------
        # Sector simulation
        # ------------------------------------------------------

        deployment = self.update_energy(
            deployment_mode
        )

        self.update_pace(
            deployment_mode
        )

        self.update_tyres(
            deployment_mode
        )

        self.update_gaps(
            deployment_mode
        )

        self.update_overtake_opportunity()

        self.update_future_opportunity()

        self.update_threat()


        # ------------------------------------------------------
        # Overtake
        # ------------------------------------------------------

        overtook = self.resolve_overtake(
            deployment_mode,
            recommendation
        )


        # ------------------------------------------------------
        # Defence
        # ------------------------------------------------------

        lost_position = False

        if not overtook:

            lost_position = (
                self.resolve_defensive_risk(
                    recommendation
                )
            )


        # ------------------------------------------------------
        # Next sector
        # ------------------------------------------------------

        race_finished = (
            self.advance_sector()
        )


        # ------------------------------------------------------
        # P1 safety
        # ------------------------------------------------------

        if self.race[
            "position"
        ] <= 1:

            self.race[
                "position"
            ] = 1

            self.race[
                "gap_ahead"
            ] = 0.0


        # ------------------------------------------------------
        # Result
        # ------------------------------------------------------

        return {

            "overtook":
                overtook,

            "lost_position":
                lost_position,


            "completed_lap":
                completed_lap,

            "completed_sector":
                completed_sector,

            "completed_sector_name":
                completed_sector_name,

            "completed_sector_type":
                completed_sector_type,


            "position":
                self.race[
                    "position"
                ],

            "lap":
                self.race[
                    "lap"
                ],

            "sector":
                self.race[
                    "sector"
                ],

            "sector_name":
                self.race[
                    "sector_name"
                ],

            "sector_type":
                self.race[
                    "sector_type"
                ],


            "deployment":
                deployment,

            "battery":
                self.race[
                    "battery"
                ],


            "tyre_compound":
                self.race[
                    "tyre_compound"
                ],

            "tyre_age":
                self.race[
                    "tyre_age"
                ],

            "tyre_condition":
                self.race[
                    "tyre_condition"
                ],

            "tyre_advantage":
                self.race[
                    "tyre_advantage"
                ],

            "tyre_degradation":
                self.race[
                    "tyre_degradation"
                ],

            "effective_tyre_life":
                self.race[
                    "effective_tyre_life"
                ],

            "tyre_life_remaining":
                self.race[
                    "tyre_life_remaining"
                ],


            "gap_ahead":
                self.race[
                    "gap_ahead"
                ],

            "gap_behind":
                self.race[
                    "gap_behind"
                ],


            "overtake_opportunity":
                self.race[
                    "overtake_opportunity"
                ],

            "future_opportunity":
                self.race[
                    "future_opportunity"
                ],


            "track_limit_risk":
                self.race[
                    "track_limit_risk"
                ],

            "race_condition":
                self.race[
                    "race_condition"
                ],

            "drs_available":
                self.race[
                    "drs_available"
                ],


            "lap_completed":
                completed_sector == 3,

            "race_finished":
                race_finished
        }


    # ==========================================================
    # PIT STOP
    # ==========================================================

    def pit_stop(
        self,
        compound
    ):

        compound = str(
            compound
        ).upper()


        if compound not in self.TYRE_PROFILES:

            compound = "MEDIUM"


        profile = self.TYRE_PROFILES[
            compound
        ]


        # ------------------------------------------------------
        # Reset tyre state
        # ------------------------------------------------------

        self.race[
            "tyre_compound"
        ] = compound

        self.race[
            "tyre_age"
        ] = 0.0

        self.race[
            "tyre_degradation"
        ] = 0.0


        # Fresh tyre advantage depends on compound.

        self.race[
            "tyre_advantage"
        ] = max(

            0.0,

            min(

                1.0,

                0.92

                + (
                    profile["pace"]
                    - 1.0
                ) * 0.55
            )
        )


        self.race[
            "base_tyre_life"
        ] = profile[
            "base_life"
        ]

        self.race[
            "effective_tyre_life"
        ] = profile[
            "base_life"
        ]

        self.race[
            "tyre_life_remaining"
        ] = profile[
            "base_life"
        ]

        self.race[
            "tyre_condition"
        ] = "FRESH"


        return {

            "compound":
                compound,

            "tyre_age":
                0.0,

            "tyre_condition":
                "FRESH",

            "tyre_life_remaining":
                profile[
                    "base_life"
                ]
        }


    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.__init__()