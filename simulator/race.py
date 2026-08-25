import random

from engine.overtake import calculate_overtake_probability
from engine.energy import calculate_deployment


class RaceSimulator:

    SECTORS = {
        1: {
            "name": "Sector 1",
            "type": "HIGH_SPEED",
            "energy_demand": 1.05,
            "overtaking_base": 0.55,
            "braking_importance": 0.55,
            "traction_importance": 0.45,
        },
        2: {
            "name": "Sector 2",
            "type": "TECHNICAL",
            "energy_demand": 0.90,
            "overtaking_base": 0.35,
            "braking_importance": 0.75,
            "traction_importance": 0.70,
        },
        3: {
            "name": "Sector 3",
            "type": "STRAIGHT",
            "energy_demand": 1.15,
            "overtaking_base": 0.75,
            "braking_importance": 0.65,
            "traction_importance": 0.80,
        },
    }

    TOTAL_SECTORS = 3

    SECTOR_TYPE_PROFILES = {
        "HIGH_SPEED": {
            "energy_demand": 1.05, "overtaking_base": 0.55,
            "braking_importance": 0.55, "traction_importance": 0.45
        },
        "TECHNICAL": {
            "energy_demand": 0.90, "overtaking_base": 0.35,
            "braking_importance": 0.75, "traction_importance": 0.70
        },
        "STRAIGHT": {
            "energy_demand": 1.15, "overtaking_base": 0.75,
            "braking_importance": 0.65, "traction_importance": 0.80
        },
        "MEDIUM_SPEED": {
            "energy_demand": 1.00, "overtaking_base": 0.50,
            "braking_importance": 0.65, "traction_importance": 0.65
        },
        "SLOW_CORNER": {
            "energy_demand": 0.85, "overtaking_base": 0.45,
            "braking_importance": 0.90, "traction_importance": 0.85
        },
    }

    TYRE_PROFILES = {
        "SOFT": {"base_life": 18.0, "pace": 1.08, "wear": 1.25},
        "MEDIUM": {"base_life": 28.0, "pace": 1.04, "wear": 1.00},
        "HARD": {"base_life": 38.0, "pace": 1.00, "wear": 0.82},
        "INTERMEDIATE": {"base_life": 24.0, "pace": 1.02, "wear": 1.10},
        "WET": {"base_life": 20.0, "pace": 0.98, "wear": 1.05},
    }

    def __init__(
        self,
        total_laps=57,
        start_lap=1,
        start_position=6,
        gap_ahead=0.65,
        gap_behind=0.90,
        start_sector=1,
        sector_types=None,
        start_compound="MEDIUM",
        start_tyre_age=0.0,
        start_battery=100.0,
    ):
        total_laps = max(1, int(total_laps))
        start_lap = max(1, min(int(start_lap), total_laps))
        start_position = max(1, min(int(start_position), 20))
        start_sector = max(1, min(int(start_sector), 3))

        if sector_types is None:
            sector_types = {
                1: "HIGH_SPEED",
                2: "TECHNICAL",
                3: "STRAIGHT",
            }
        else:
            sector_types = {
                1: sector_types.get(1, "HIGH_SPEED"),
                2: sector_types.get(2, "TECHNICAL"),
                3: sector_types.get(3, "STRAIGHT"),
            }

        for number in sector_types:
            if sector_types[number] not in self.SECTOR_TYPE_PROFILES:
                sector_types[number] = "HIGH_SPEED"

        self.sector_types = sector_types
        start_type = sector_types[start_sector]
        start_profile = self.SECTOR_TYPE_PROFILES[start_type]

        compound = str(start_compound).upper()
        if compound not in self.TYRE_PROFILES:
            compound = "MEDIUM"

        self.race = {
            "lap": start_lap,
            "total_laps": total_laps,
            "position": start_position,

            "sector": start_sector,
            "sector_name": f"Sector {start_sector}",
            "sector_type": start_type,
            "sector_energy_demand": start_profile["energy_demand"],
            "sector_overtaking_base": start_profile["overtaking_base"],
            "sector_braking_importance": start_profile["braking_importance"],
            "sector_traction_importance": start_profile["traction_importance"],

            "battery": max(0.0, min(100.0, float(start_battery))),

            "gap_ahead": (
                0.0 if start_position <= 1
                else max(0.05, float(gap_ahead))
            ),
            "gap_behind": max(0.05, float(gap_behind)),

            "tyre_compound": compound,
            "tyre_age": max(0.0, float(start_tyre_age)),
            "tyre_wear": 0.0,
            "tyre_degradation": 0.0,
            "tyre_condition": "FRESH",
            "tyre_advantage": 0.89,
            "base_tyre_life": self.TYRE_PROFILES[compound]["base_life"],
            "effective_tyre_life": self.TYRE_PROFILES[compound]["base_life"],
            "tyre_life_remaining": self.TYRE_PROFILES[compound]["base_life"],

            "pace_advantage": 0.55,

            "overtake_opportunity": 0.55,
            "future_opportunity": 0.60,

            "threat_level": 0.40,

            "track_limit_risk": 0.05,
            "race_condition": "NORMAL",

            "last_overtake": False,
            "last_position_change": False,

            "deployment_mode": "BALANCED",
            "recommendation": "STAY",

            "driver_override_count": 0,
            "ai_follow_count": 0,
            "strategy_deviation": 0.0,
            "last_driver_override": False,
            "last_ai_deployment": "BALANCED",
            "last_ai_recommendation": "STAY",
            "attack_cooldown_sectors": 0,
            "last_attack_probability": 0.0,
            "last_attack_attempt": False,
            "last_pit_stop": False,
            "pit_position_change": 0,
            "pit_position_before": start_position,
            "pit_position_after": start_position,
            "pit_time_loss": 0.0,
            "pit_rear_gap_before": max(0.05, float(gap_behind)),
            "pit_rear_gap_after": max(0.05, float(gap_behind)),
            "driver_energy_penalty": 0.0,
            "driver_tyre_penalty": 0.0,
            "driver_energy_multiplier": 1.0,
            "driver_tyre_multiplier": 1.0,
            "driver_gap_effect": 0.0,
        }

        profile = self.TYRE_PROFILES[compound]
        self.race["base_tyre_life"] = profile["base_life"]
        self.race["effective_tyre_life"] = profile["base_life"]

        age_ratio = self.race["tyre_age"] / max(profile["base_life"], 1.0)
        compound_pace = (profile["pace"] - 1.0) * 0.55

        self.race["tyre_advantage"] = max(
            0.0,
            min(1.0, 0.92 - age_ratio * 0.92 + compound_pace),
        )
        # Tyre wear is cumulative and can never decrease.  Starting a
        # simulation with an older tyre therefore starts with corresponding
        # accumulated wear rather than a fresh wear calculation.
        self.race["tyre_wear"] = min(
            profile["base_life"],
            self.race["tyre_age"] * profile["wear"],
        )
        self.race["tyre_life_remaining"] = max(
            0.0, profile["base_life"] - self.race["tyre_wear"]
        )
        self.race["tyre_degradation"] = min(
            100.0,
            self.race["tyre_wear"] / max(profile["base_life"], 1.0) * 100.0,
        )

        if self.race["tyre_age"] <= 0.01:
            self.race["tyre_condition"] = "FRESH"
        elif self.race["tyre_advantage"] >= 0.65:
            self.race["tyre_condition"] = "GOOD"
        elif self.race["tyre_advantage"] >= 0.35:
            self.race["tyre_condition"] = "MEDIUM"
        else:
            self.race["tyre_condition"] = "POOR"

    def get_state(self):
        return self.race.copy()

    def apply_sector(self, sector_number):
        sector_number = max(1, min(int(sector_number), 3))
        default = self.SECTORS[sector_number]
        sector_type = self.sector_types.get(sector_number, default["type"])
        profile = self.SECTOR_TYPE_PROFILES.get(
            sector_type,
            self.SECTOR_TYPE_PROFILES[default["type"]],
        )

        self.race["sector"] = sector_number
        self.race["sector_name"] = f"Sector {sector_number}"
        self.race["sector_type"] = sector_type
        self.race["sector_energy_demand"] = profile["energy_demand"]
        self.race["sector_overtaking_base"] = profile["overtaking_base"]
        self.race["sector_braking_importance"] = profile["braking_importance"]
        self.race["sector_traction_importance"] = profile["traction_importance"]

    def update_energy(self, deployment_mode):
        deployment = calculate_deployment(self.race, deployment_mode)

        target_energy = float(
            deployment.get("target_energy_per_sector", 0.0)
        )

        actual_consumption = (
            target_energy
            * random.uniform(0.94, 1.06)
            * self.race.get("driver_energy_multiplier", 1.0)
        )

        self.race["battery"] = max(
            0.0,
            self.race["battery"] - actual_consumption,
        )

        return {
            "target_energy_per_sector": round(target_energy, 3),
            "actual_energy_per_sector": round(actual_consumption, 3),
            "target_energy_per_lap": round(target_energy * 3, 3),
            "baseline_energy_per_sector": round(
                deployment.get("baseline_energy_per_sector", 0.0), 3
            ),
            "baseline_energy_per_lap": round(
                deployment.get("baseline_energy_per_sector", 0.0) * 3, 3
            ),
            "target_percentage": deployment.get("target_percentage", 100.0),
            "baseline_percentage": deployment.get("baseline_percentage", 100.0),
            "projected_battery": round(self.race["battery"], 2),
            "remaining_laps": deployment.get(
                "remaining_laps",
                self.race["total_laps"] - self.race["lap"],
            ),
        }

    def update_pace(self, deployment_mode):
        pace_change = {
            "PUSH": 0.035,
            "BALANCED": 0.010,
            "HARVEST": -0.015,
            "CONSERVE": -0.025,
        }.get(deployment_mode, 0.0)

        if self.race["sector_type"] == "HIGH_SPEED":
            pace_change *= 1.05
        elif self.race["sector_type"] == "STRAIGHT":
            pace_change *= 1.10
        elif self.race["sector_type"] == "TECHNICAL":
            pace_change *= 0.90

        self.race["pace_advantage"] += pace_change

        noise = (
            random.uniform(-0.014, 0.014)
            if self.race["race_condition"] == "WET"
            else random.uniform(-0.012, 0.012)
        )
        self.race["pace_advantage"] = max(
            0.0,
            min(1.0, self.race["pace_advantage"] + noise),
        )

    def update_tyres(self, deployment_mode):
        """
        Update tyre wear using a cumulative, irreversible wear model.

        tyre_age = actual elapsed tyre time in laps.
        tyre_wear = accumulated wear measured in equivalent base-life laps.
        tyre_life_remaining = base_life - tyre_wear.

        Deployment, sector, weather, track limits and driver behaviour change
        the *rate* of wear.  They never restore previously accumulated wear.
        """
        compound = self.race["tyre_compound"]
        profile = self.TYRE_PROFILES.get(
            compound,
            self.TYRE_PROFILES["MEDIUM"],
        )

        mode_factor = {
            "PUSH": 1.22,
            "BALANCED": 1.00,
            "HARVEST": 0.82,
            "CONSERVE": 0.72,
        }.get(deployment_mode, 1.00)

        sector_factor = {
            "TECHNICAL": 1.15,
            "HIGH_SPEED": 1.05,
            "STRAIGHT": 0.90,
            "MEDIUM_SPEED": 1.00,
            "SLOW_CORNER": 1.12,
        }.get(self.race["sector_type"], 1.00)

        rule_factor = 1.0 + 0.20 * float(
            self.race.get("track_limit_risk", 0.0)
        )

        weather_factor = 1.0
        if self.race["race_condition"] == "WET":
            if compound in ("SOFT", "MEDIUM", "HARD"):
                weather_factor = 1.15
            elif compound == "INTERMEDIATE":
                weather_factor = 1.02

        driver_factor = max(
            0.85,
            min(1.30, float(self.race.get("driver_tyre_multiplier", 1.0))),
        )

        # One sector is one third of a racing lap.  The compound's wear
        # coefficient and the current conditions determine how much of the
        # tyre's finite life is consumed by that sector.
        sector_wear = (
            (1.0 / self.TOTAL_SECTORS)
            * profile["wear"]
            * mode_factor
            * sector_factor
            * rule_factor
            * weather_factor
            * driver_factor
        )

        previous_wear = float(self.race.get("tyre_wear", 0.0))
        new_wear = max(
            previous_wear,
            min(profile["base_life"], previous_wear + sector_wear),
        )

        self.race["tyre_wear"] = new_wear

        # Age is time elapsed on the tyre, not a derived quantity.
        self.race["tyre_age"] += 1.0 / self.TOTAL_SECTORS

        self.race["base_tyre_life"] = profile["base_life"]

        # Keep this field stable and interpretable.  It is the compound's
        # nominal life; remaining life is based on cumulative wear below.
        self.race["effective_tyre_life"] = profile["base_life"]

        self.race["tyre_life_remaining"] = max(
            0.0,
            profile["base_life"] - self.race["tyre_wear"],
        )

        self.race["tyre_degradation"] = min(
            100.0,
            (self.race["tyre_wear"] / max(profile["base_life"], 1.0)) * 100.0,
        )

        wear_ratio = self.race["tyre_wear"] / max(
            profile["base_life"],
            1.0,
        )

        compound_pace = (profile["pace"] - 1.0) * 0.55

        self.race["tyre_advantage"] = max(
            0.0,
            min(1.0, 0.92 - wear_ratio * 0.92 + compound_pace),
        )

        tyre_value = self.race["tyre_advantage"]

        if tyre_value >= 0.75:
            condition = "FRESH"
        elif tyre_value >= 0.65:
            condition = "GOOD"
        elif tyre_value >= 0.35:
            condition = "MEDIUM"
        else:
            condition = "POOR"

        self.race["tyre_condition"] = condition

    def update_gaps(self, deployment_mode):
        """
        Update gaps without teleporting either car.

        Important:
        - A car more than ~1 s behind cannot suddenly cause a position loss.
        - Gap changes are small per sector.
        - Driver override effects are bounded.
        """
        if self.race["position"] <= 1:
            self.race["gap_ahead"] = 0.0
        else:
            pace_effect = self.race["pace_advantage"] - 0.5

            if deployment_mode == "PUSH":
                self.race["gap_ahead"] -= pace_effect * 0.035
            elif deployment_mode == "BALANCED":
                self.race["gap_ahead"] -= pace_effect * 0.015
            elif deployment_mode == "CONSERVE":
                self.race["gap_ahead"] += 0.012
            elif deployment_mode == "HARVEST":
                self.race["gap_ahead"] += 0.020

            self.race["gap_ahead"] += random.uniform(-0.014, 0.014)
            self.race["gap_ahead"] += max(
                -0.012,
                min(0.012, self.race.get("driver_gap_effect", 0.0)),
            )

            self.race["gap_ahead"] = max(
                0.05,
                min(3.0, self.race["gap_ahead"]),
            )

        # Rear gap evolves slowly. It cannot jump from 1.2 s to 0.2 s.
        rear_change = random.uniform(-0.018, 0.018)

        if deployment_mode == "PUSH":
            rear_change += 0.015
        elif deployment_mode == "CONSERVE":
            rear_change -= 0.010
        elif deployment_mode == "HARVEST":
            rear_change -= 0.015

        old_rear_gap = self.race["gap_behind"]
        new_rear_gap = old_rear_gap + rear_change

        # Preserve a meaningful gap unless the car was already under threat.
        if old_rear_gap > 1.00:
            new_rear_gap = max(0.75, new_rear_gap)
        elif old_rear_gap > 0.75:
            new_rear_gap = max(0.55, new_rear_gap)

        self.race["gap_behind"] = max(
            0.05,
            min(3.0, new_rear_gap),
        )

    def update_overtake_opportunity(self):
        base = self.race["sector_overtaking_base"]
        gap = self.race["gap_ahead"]
        pace = self.race["pace_advantage"]
        tyres = self.race["tyre_advantage"]

        opportunity = base

        if gap < 0.40:
            opportunity += 0.18
        elif gap < 0.70:
            opportunity += 0.08
        elif gap > 1.50:
            opportunity -= 0.18

        opportunity += (pace - 0.5) * 0.25
        opportunity += (tyres - 0.5) * 0.15

        if self.race["race_condition"] == "WET":
            opportunity -= 0.05
        elif self.race["race_condition"] == "VSC":
            opportunity *= 0.45
        elif self.race["race_condition"] == "SAFETY CAR":
            opportunity *= 0.15

        opportunity *= (
            1.0
            - 0.15 * self.race.get("track_limit_risk", 0.0)
        )

        opportunity += random.uniform(-0.018, 0.018)

        self.race["overtake_opportunity"] = max(
            0.0,
            min(1.0, opportunity),
        )

    def update_future_opportunity(self):
        next_sector = self.race["sector"] + 1
        if next_sector > 3:
            next_sector = 1

        default = self.SECTORS[next_sector]
        next_type = self.sector_types.get(next_sector, default["type"])
        profile = self.SECTOR_TYPE_PROFILES.get(
            next_type,
            self.SECTOR_TYPE_PROFILES[default["type"]],
        )

        future = profile["overtaking_base"]

        if self.race["gap_ahead"] < 0.6:
            future += 0.10

        future += random.uniform(-0.03, 0.03)

        self.race["future_opportunity"] = max(
            0.0,
            min(1.0, future),
        )

    def update_threat(self):
        """
        Rear threat responds to the actual rear gap.
        A rear car > 1 second away should not generate a strong
        defensive threat.
        """
        gap = self.race["gap_behind"]
        threat = self.race["threat_level"]

        if gap > 1.20:
            threat -= 0.12
        elif gap > 0.90:
            threat -= 0.08
        elif gap < 0.30:
            threat += 0.14
        elif gap < 0.50:
            threat += 0.08
        elif gap < 0.70:
            threat += 0.035
        else:
            threat += random.uniform(-0.015, 0.015)

        if self.race["tyre_advantage"] < 0.35:
            threat += 0.04

        if self.race["battery"] < 25:
            threat += 0.025

        # Hard physical consistency: a distant car cannot be a huge threat.
        if gap > 1.00:
            threat = min(threat, 0.35)
        elif gap > 0.80:
            threat = min(threat, 0.50)

        self.race["threat_level"] = max(
            0.0,
            min(1.0, threat),
        )

    def resolve_overtake(self, deployment_mode, recommendation):
        """
        Resolve an ATTACK using the hybrid probability while keeping
        overtakes physically and temporally realistic.

        Important design rules:
        - An attack is evaluated once per sector, but a successful
          overtake creates a cooldown so the car cannot pass again
          immediately in the next sector.
        - Close gaps increase the chance of an attack, but do not
          guarantee it.
        - The ML probability is supporting evidence, not a guarantee.
        """
        self.race["last_attack_attempt"] = False

        if self.race["attack_cooldown_sectors"] > 0:
            self.race["attack_cooldown_sectors"] -= 1
            self.race["last_attack_probability"] = 0.0
            return False

        if self.race["position"] <= 1:
            self.race["gap_ahead"] = 0.0
            self.race["last_attack_probability"] = 0.0
            return False

        if recommendation != "ATTACK":
            self.race["last_attack_probability"] = 0.0
            return False

        if self.race["race_condition"] in ("VSC", "SAFETY CAR"):
            self.race["last_attack_probability"] = 0.0
            return False

        gap = float(self.race["gap_ahead"])
        sector_base = float(self.race["sector_overtaking_base"])

        # Do not launch an attack from too far back.
        if gap > 1.05:
            self.race["last_attack_probability"] = 0.0
            return False

        if sector_base < 0.25 and gap > 0.45:
            self.race["last_attack_probability"] = 0.0
            return False

        probability = float(calculate_overtake_probability(self.race))

        # Start from the hybrid model, then moderate it.
        execution_probability = 0.52 * probability

        # Gap is the strongest real-time factor.
        if gap <= 0.30:
            execution_probability += 0.18
        elif gap <= 0.45:
            execution_probability += 0.12
        elif gap <= 0.60:
            execution_probability += 0.07
        elif gap <= 0.80:
            execution_probability += 0.015
        else:
            execution_probability -= 0.06

        # Sector suitability.
        execution_probability += (sector_base - 0.50) * 0.16

        # Pace advantage.
        pace = float(self.race["pace_advantage"])
        execution_probability += (pace - 0.50) * 0.12

        # Tyres.
        tyre = float(self.race["tyre_advantage"])
        if tyre < 0.30:
            execution_probability *= 0.55
        elif tyre < 0.45:
            execution_probability *= 0.78
        elif tyre >= 0.70:
            execution_probability += 0.025

        # Battery.
        battery = float(self.race["battery"])
        if battery < 15:
            execution_probability *= 0.45
        elif battery < 25:
            execution_probability *= 0.65
        elif battery < 40:
            execution_probability *= 0.85

        if deployment_mode == "PUSH":
            execution_probability += 0.035
        elif deployment_mode == "BALANCED":
            execution_probability += 0.010
        elif deployment_mode == "HARVEST":
            execution_probability -= 0.035
        elif deployment_mode == "CONSERVE":
            execution_probability -= 0.045

        execution_probability *= (
            1.0 - 0.20 * self.race.get("track_limit_risk", 0.0)
        )

        # Keep the result in a realistic range.
        execution_probability = max(
            0.0, min(0.58, execution_probability)
        )

        self.race["last_attack_probability"] = execution_probability
        self.race["last_attack_attempt"] = True

        if random.random() > execution_probability:
            # A failed attack should not immediately trigger another
            # attempt in the next sector.
            self.race["attack_cooldown_sectors"] = 1
            return False

        # ------------------------------------------------------
        # Successful overtake
        # ------------------------------------------------------
        old_gap = gap

        self.race["position"] = max(
            1, self.race["position"] - 1
        )

        self.race["last_overtake"] = True
        self.race["last_position_change"] = True

        # The next car ahead is not immediately on the gearbox.
        self.race["gap_ahead"] = (
            0.0 if self.race["position"] <= 1
            else random.uniform(0.45, 0.75)
        )

        # The overtaken car remains close enough to create a battle,
        # but not so close that an instant counter-pass is guaranteed.
        post_gap = old_gap + random.uniform(0.18, 0.32)
        self.race["gap_behind"] = max(
            0.35, min(0.85, post_gap)
        )

        self.race["threat_level"] = max(
            0.25, min(0.55, self.race["threat_level"])
        )

        # Four sectors means the next attack opportunity cannot occur
        # immediately. This prevents unrealistic chains of overtakes.
        self.race["attack_cooldown_sectors"] = 4

        return True

    def resolve_defensive_risk(self, recommendation):
        """
        Position loss is only possible when a real rear threat exists.
        """
        if self.race["position"] <= 1:
            self.race["gap_ahead"] = 0.0
            return False

        if recommendation == "DEFEND":
            return False

        gap = self.race["gap_behind"]
        threat = self.race["threat_level"]

        # Absolutely no random loss from a distant car.
        if gap > 0.90:
            return False

        if gap > 0.70:
            return False

        if gap <= 0.30:
            chance = 0.065
        elif gap <= 0.45:
            chance = 0.035
        elif gap <= 0.60:
            chance = 0.015
        else:
            chance = 0.006

        # Threat modifies the probability, but cannot create a threat
        # when the rear gap itself is large.
        if threat > 0.80:
            chance += 0.015
        elif threat > 0.65:
            chance += 0.015

        if self.race["tyre_advantage"] < 0.30:
            chance += 0.015

        if self.race["battery"] < 25:
            chance += 0.012

        if self.race["race_condition"] == "WET":
            chance += 0.010

        chance = max(0.0, min(0.10, chance))

        if random.random() > chance:
            return False

        self.race["position"] = min(
            20,
            self.race["position"] + 1,
        )

        self.race["last_position_change"] = True

        # After being passed, the attacking car is nearby, not
        # automatically 1+ seconds away.
        self.race["gap_behind"] = random.uniform(
            0.25,
            0.55,
        )

        self.race["gap_ahead"] = random.uniform(
            0.28,
            0.60,
        )

        return True

    def advance_sector(self):
        current_sector = self.race["sector"]

        if current_sector < 3:
            self.apply_sector(current_sector + 1)
            return False

        self.race["lap"] += 1

        if self.race["lap"] > self.race["total_laps"]:
            self.race["lap"] = self.race["total_laps"]
            return True

        self.apply_sector(1)
        return False

    def calculate_driver_deviation(
        self,
        actual_deployment,
        actual_recommendation,
        ai_deployment,
        ai_recommendation,
        driver_controlled,
    ):
        self.race["last_ai_deployment"] = ai_deployment
        self.race["last_ai_recommendation"] = ai_recommendation

        if not driver_controlled:
            self.race["ai_follow_count"] += 1
            self.race["last_driver_override"] = False
            self.race["driver_energy_penalty"] = 0.0
            self.race["driver_tyre_penalty"] = 0.0
            self.race["strategy_deviation"] = max(
                0.0,
                self.race["strategy_deviation"] - 1.0,
            )
            return 1.0, 1.0, 0.0

        self.race["driver_override_count"] += 1
        self.race["last_driver_override"] = True

        deployment_delta = {
            ("PUSH", "BALANCED"): 0.12,
            ("PUSH", "HARVEST"): 0.22,
            ("PUSH", "CONSERVE"): 0.28,
            ("BALANCED", "PUSH"): -0.08,
            ("HARVEST", "BALANCED"): -0.10,
            ("CONSERVE", "BALANCED"): -0.14,
        }.get((actual_deployment, ai_deployment), 0.0)

        recommendation_delta = 0.0
        if actual_recommendation == "ATTACK" and ai_recommendation != "ATTACK":
            recommendation_delta = 0.12
        elif actual_recommendation == "DEFEND" and ai_recommendation == "ATTACK":
            recommendation_delta = 0.06
        elif actual_recommendation == "STAY" and ai_recommendation == "ATTACK":
            recommendation_delta = -0.04

        deviation = (
            abs(deployment_delta) * 20.0
            + abs(recommendation_delta) * 25.0
        )

        self.race["strategy_deviation"] = min(
            100.0,
            self.race["strategy_deviation"] + deviation,
        )

        energy_multiplier = max(
            0.82,
            1.0
            + deployment_delta
            + max(0.0, recommendation_delta) * 0.35,
        )

        tyre_multiplier = max(
            0.85,
            1.0
            + abs(deployment_delta) * 0.55
            + max(0.0, recommendation_delta) * 0.40,
        )

        gap_effect = (
            0.018
            if actual_recommendation == "ATTACK"
            else -0.008
            if actual_recommendation == "DEFEND"
            else 0.0
        )

        self.race["driver_energy_penalty"] = (
            energy_multiplier - 1.0
        ) * 100.0

        self.race["driver_tyre_penalty"] = (
            tyre_multiplier - 1.0
        ) * 100.0

        return energy_multiplier, tyre_multiplier, gap_effect

    def update(
        self,
        deployment_mode,
        recommendation,
        ai_deployment_mode=None,
        ai_recommendation=None,
        driver_controlled=False,
    ):
        self.race["last_overtake"] = False
        self.race["last_position_change"] = False
        self.race["last_pit_stop"] = False
        self.race["pit_position_change"] = 0

        if ai_deployment_mode is None:
            ai_deployment_mode = deployment_mode

        if ai_recommendation is None:
            ai_recommendation = recommendation

        (
            self.race["driver_energy_multiplier"],
            self.race["driver_tyre_multiplier"],
            self.race["driver_gap_effect"],
        ) = self.calculate_driver_deviation(
            deployment_mode,
            recommendation,
            ai_deployment_mode,
            ai_recommendation,
            driver_controlled,
        )

        self.race["deployment_mode"] = deployment_mode
        self.race["recommendation"] = recommendation

        completed_lap = self.race["lap"]
        completed_sector = self.race["sector"]
        completed_sector_name = self.race["sector_name"]
        completed_sector_type = self.race["sector_type"]

        deployment = self.update_energy(deployment_mode)
        self.update_pace(deployment_mode)
        self.update_tyres(deployment_mode)
        self.update_gaps(deployment_mode)
        self.update_overtake_opportunity()
        self.update_future_opportunity()
        self.update_threat()

        overtook = self.resolve_overtake(
            deployment_mode,
            recommendation,
        )

        lost_position = False

        if not overtook:
            lost_position = self.resolve_defensive_risk(
                recommendation
            )

        race_finished = self.advance_sector()

        if self.race["position"] <= 1:
            self.race["position"] = 1
            self.race["gap_ahead"] = 0.0

        return {
            "overtook": overtook,
            "lost_position": lost_position,

            "completed_lap": completed_lap,
            "completed_sector": completed_sector,
            "completed_sector_name": completed_sector_name,
            "completed_sector_type": completed_sector_type,

            "position": self.race["position"],
            "lap": self.race["lap"],
            "sector": self.race["sector"],
            "sector_name": self.race["sector_name"],
            "sector_type": self.race["sector_type"],

            "deployment": deployment,
            "battery": self.race["battery"],

            "tyre_compound": self.race["tyre_compound"],
            "tyre_age": self.race["tyre_age"],
            "tyre_wear": self.race["tyre_wear"],
            "tyre_condition": self.race["tyre_condition"],
            "tyre_advantage": self.race["tyre_advantage"],
            "tyre_degradation": self.race["tyre_degradation"],
            "effective_tyre_life": self.race["effective_tyre_life"],
            "tyre_life_remaining": self.race["tyre_life_remaining"],

            "gap_ahead": self.race["gap_ahead"],
            "gap_behind": self.race["gap_behind"],

            "overtake_opportunity": self.race["overtake_opportunity"],
            "future_opportunity": self.race["future_opportunity"],

            "track_limit_risk": self.race["track_limit_risk"],
            "race_condition": self.race["race_condition"],

            "last_pit_stop": self.race["last_pit_stop"],
            "pit_position_change": self.race["pit_position_change"],
            "pit_position_before": self.race["pit_position_before"],
            "pit_position_after": self.race["pit_position_after"],
            "pit_time_loss": self.race["pit_time_loss"],
            "pit_rear_gap_before": self.race["pit_rear_gap_before"],
            "pit_rear_gap_after": self.race["pit_rear_gap_after"],

            "driver_override": self.race["last_driver_override"],
            "driver_override_count": self.race["driver_override_count"],
            "ai_follow_count": self.race["ai_follow_count"],
            "strategy_deviation": self.race["strategy_deviation"],
            "driver_energy_penalty": self.race["driver_energy_penalty"],
            "driver_tyre_penalty": self.race["driver_tyre_penalty"],

            "overtake_probability": self.race.get(
                "last_attack_probability", 0.0
            ),

            "lap_completed": completed_sector == 3,
            "race_finished": race_finished,
        }

    def pit_stop(self, compound):
        """
        Perform a pit stop and apply a dynamic position consequence.

        The simulator currently tracks the nearest car behind via
        ``gap_behind`` rather than a full field of individual gaps.
        Therefore the pit-stop model uses that live rear gap to decide
        whether the nearest rival can realistically pass during the
        pit-loss window. A second position loss is only possible when
        the rear gap is extremely small and the car is already in a
        dense battle.

        Important: the pit-stop position change is separate from the
        normal overtaking/defensive logic.
        """
        compound = str(compound).upper()

        if compound not in self.TYRE_PROFILES:
            compound = "MEDIUM"

        profile = self.TYRE_PROFILES[compound]

        position_before = int(self.race["position"])
        rear_gap_before = float(self.race["gap_behind"])

        # Typical pit-lane time loss varies with track/conditions.
        # Keep this as a simulation variable rather than a fixed number.
        pit_time_loss = random.uniform(20.0, 24.0)

        # Reset per-event pit metadata.
        self.race["last_pit_stop"] = True
        self.race["pit_position_before"] = position_before
        self.race["pit_rear_gap_before"] = rear_gap_before
        self.race["pit_time_loss"] = pit_time_loss
        self.race["pit_position_change"] = 0

        # ------------------------------------------------------
        # POSITION LOSS FROM THE NEAREST CAR BEHIND
        # ------------------------------------------------------
        #
        # gap_behind is the live race gap before entering the pits.
        # A car only 0.4 s behind is effectively certain to gain the
        # place during a normal pit stop. A car several seconds behind
        # still has a chance, but the chance falls as the gap grows.
        #
        # We deliberately do NOT use the pit time loss directly as
        # ``20 seconds -> 20 positions``. The gap is the meaningful
        # information available from this simulator.

        if position_before < 20:
            if rear_gap_before <= 0.50:
                nearest_pass_probability = 0.98
            elif rear_gap_before <= 0.80:
                nearest_pass_probability = 0.95
            elif rear_gap_before <= 1.20:
                nearest_pass_probability = 0.90
            elif rear_gap_before <= 1.80:
                nearest_pass_probability = 0.78
            elif rear_gap_before <= 2.50:
                nearest_pass_probability = 0.58
            else:
                nearest_pass_probability = 0.30

            # A very fresh tyre does not undo the time lost in the
            # pit lane, so it does not directly cancel the pass.
            nearest_pass = random.random() < nearest_pass_probability
        else:
            nearest_pass = False

        positions_lost = 1 if nearest_pass else 0

        # ------------------------------------------------------
        # OPTIONAL SECOND POSITION LOSS
        # ------------------------------------------------------
        #
        # We don't know the exact gap to P(N+2), so only allow a second
        # place to be lost when the tracked rear car was already very
        # close. This represents a tightly packed group rather than
        # inventing several unseen cars.

        if nearest_pass and position_before < 19:
            if rear_gap_before <= 0.35:
                second_pass_probability = 0.28
            elif rear_gap_before <= 0.60:
                second_pass_probability = 0.16
            elif rear_gap_before <= 0.90:
                second_pass_probability = 0.07
            else:
                second_pass_probability = 0.0

            if random.random() < second_pass_probability:
                positions_lost = 2

        self.race["position"] = min(
            20,
            position_before + positions_lost,
        )

        self.race["pit_position_change"] = (
            self.race["position"] - position_before
        )

        self.race["pit_position_after"] = self.race["position"]
        self.race["last_position_change"] = positions_lost > 0

        # ------------------------------------------------------
        # POST-PIT GAPS
        # ------------------------------------------------------
        #
        # If a rival passed us, it should be ahead by a realistic
        # amount after we rejoin, not magically 5+ seconds away.
        # The more closely the rival was following before the stop,
        # the closer the post-pit battle remains.

        if positions_lost > 0:
            if rear_gap_before <= 0.50:
                passed_car_gap = random.uniform(0.35, 0.75)
            elif rear_gap_before <= 1.20:
                passed_car_gap = random.uniform(0.45, 0.95)
            else:
                passed_car_gap = random.uniform(0.60, 1.20)

            # The car that passed us is now ahead.
            self.race["gap_ahead"] = min(
                2.0,
                passed_car_gap,
            )

            # If two places were lost, the second car is represented
            # as the rear battle car. Keep the gap realistic.
            self.race["gap_behind"] = random.uniform(0.55, 1.20)

        else:
            # We rejoin ahead of the nearest rival. The rear gap should
            # remain related to the live pre-pit gap rather than jumping
            # to an arbitrary value.
            self.race["gap_ahead"] = (
                0.0 if self.race["position"] <= 1
                else max(0.20, min(1.50, self.race["gap_ahead"] + random.uniform(-0.10, 0.20)))
            )

            self.race["gap_behind"] = max(
                0.35,
                min(2.50, rear_gap_before + random.uniform(0.20, 0.70)),
            )

        self.race["pit_rear_gap_after"] = self.race["gap_behind"]

        # ------------------------------------------------------
        # RESET TYRE STATE
        # ------------------------------------------------------

        self.race["tyre_compound"] = compound
        self.race["tyre_age"] = 0.0
        self.race["tyre_wear"] = 0.0
        self.race["tyre_degradation"] = 0.0

        self.race["tyre_advantage"] = max(
            0.0,
            min(
                1.0,
                0.92 + (profile["pace"] - 1.0) * 0.55,
            ),
        )

        self.race["base_tyre_life"] = profile["base_life"]
        self.race["effective_tyre_life"] = profile["base_life"]
        self.race["tyre_life_remaining"] = profile["base_life"]
        self.race["tyre_condition"] = "FRESH"

        return {
            "compound": compound,
            "tyre_age": 0.0,
            "tyre_wear": 0.0,
            "tyre_condition": "FRESH",
            "tyre_life_remaining": profile["base_life"],
            "position_before": position_before,
            "position_after": self.race["position"],
            "positions_lost": positions_lost,
            "pit_position_change": self.race["pit_position_change"],
            "pit_time_loss": round(pit_time_loss, 2),
            "rear_gap_before": round(rear_gap_before, 3),
            "rear_gap_after": round(self.race["gap_behind"], 3),
            "gap_ahead_after": round(self.race["gap_ahead"], 3),
        }

    def reset(self):
        self.__init__()