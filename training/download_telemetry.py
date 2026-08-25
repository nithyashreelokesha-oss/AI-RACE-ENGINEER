import os
import time
import warnings

import numpy as np
import pandas as pd
import fastf1


# ============================================================
# CONFIGURATION
# ============================================================

YEAR = 2026

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RAW_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    str(YEAR)
)

CACHE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "fastf1_cache"
)


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs(
    RAW_DIR,
    exist_ok=True
)

os.makedirs(
    CACHE_DIR,
    exist_ok=True
)


# ============================================================
# FASTF1 CACHE
# ============================================================

fastf1.Cache.enable_cache(
    CACHE_DIR
)

warnings.filterwarnings(
    "ignore"
)


# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(
    value,
    default=np.nan
):

    try:

        if pd.isna(value):

            return default

    except Exception:

        pass

    return value


# ============================================================
# TIME CONVERSION
# ============================================================

def convert_time_to_seconds(
    value
):

    if value is None:

        return np.nan

    try:

        if pd.isna(value):

            return np.nan

    except Exception:

        pass


    try:

        if isinstance(
            value,
            pd.Timedelta
        ):

            return (
                value.total_seconds()
            )


        if hasattr(
            value,
            "total_seconds"
        ):

            return (
                value.total_seconds()
            )


        return float(
            value
        )

    except Exception:

        return np.nan


# ============================================================
# TELEMETRY AGGREGATION
# ============================================================

def aggregate_telemetry(
    telemetry
):

    """
    Convert telemetry samples into lap-level statistics.

    No missing telemetry is replaced with artificial values.
    """

    if telemetry is None:

        return {}


    if telemetry.empty:

        return {}


    result = {}


    # ========================================================
    # SPEED
    # ========================================================

    if "Speed" in telemetry.columns:

        speed = pd.to_numeric(
            telemetry["Speed"],
            errors="coerce"
        ).dropna()


        if not speed.empty:

            result["speed_mean"] = float(
                speed.mean()
            )

            result["speed_max"] = float(
                speed.max()
            )

            result["speed_min"] = float(
                speed.min()
            )

            result["speed_std"] = float(
                speed.std()
            ) if len(speed) > 1 else 0.0


    # ========================================================
    # THROTTLE
    # ========================================================

    if "Throttle" in telemetry.columns:

        throttle = pd.to_numeric(
            telemetry["Throttle"],
            errors="coerce"
        ).dropna()


        if not throttle.empty:

            result["throttle_mean"] = float(
                throttle.mean()
            )

            result["throttle_max"] = float(
                throttle.max()
            )


    # ========================================================
    # BRAKE
    # ========================================================

    if "Brake" in telemetry.columns:

        brake = telemetry[
            "Brake"
        ]


        if brake.dtype == bool:

            brake_numeric = (
                brake.astype(float)
            )

        else:

            brake_numeric = pd.to_numeric(
                brake,
                errors="coerce"
            )


        brake_numeric = (
            brake_numeric
            .dropna()
        )


        if not brake_numeric.empty:

            result["brake_mean"] = float(
                brake_numeric.mean()
            )

            result["brake_max"] = float(
                brake_numeric.max()
            )

            result["brake_usage"] = float(
                (
                    brake_numeric > 0
                ).mean()
            )


    # ========================================================
    # RPM
    # ========================================================

    if "RPM" in telemetry.columns:

        rpm = pd.to_numeric(
            telemetry["RPM"],
            errors="coerce"
        ).dropna()


        if not rpm.empty:

            result["rpm_mean"] = float(
                rpm.mean()
            )

            result["rpm_max"] = float(
                rpm.max()
            )


    # ========================================================
    # GEAR
    # ========================================================

    if "nGear" in telemetry.columns:

        gear = pd.to_numeric(
            telemetry["nGear"],
            errors="coerce"
        ).dropna()


        if not gear.empty:

            result["gear_mean"] = float(
                gear.mean()
            )

            result["gear_max"] = float(
                gear.max()
            )


    # ========================================================
    # DISTANCE
    # ========================================================

    if "Distance" in telemetry.columns:

        distance = pd.to_numeric(
            telemetry["Distance"],
            errors="coerce"
        ).dropna()


        if not distance.empty:

            result["distance_start"] = float(
                distance.min()
            )

            result["distance_end"] = float(
                distance.max()
            )


    # ========================================================
    # X / Y / Z
    # ========================================================

    for column in [
        "X",
        "Y",
        "Z"
    ]:

        if column not in telemetry.columns:

            continue


        values = pd.to_numeric(
            telemetry[column],
            errors="coerce"
        ).dropna()


        if values.empty:

            continue


        result[
            f"{column.lower()}_mean"
        ] = float(
            values.mean()
        )


    # ========================================================
    # TELEMETRY SAMPLE COUNT
    # ========================================================

    result[
        "telemetry_samples"
    ] = int(
        len(telemetry)
    )


    return result


# ============================================================
# EXTRACT TELEMETRY FOR ONE LAP
# ============================================================

def get_lap_telemetry(
    lap
):

    """
    Safely obtain telemetry for one lap.

    The important point is that we do not assume the returned
    telemetry dataframe contains a 'Date' column.
    """

    try:

        telemetry = (
            lap.get_telemetry()
        )

    except Exception:

        return None


    if telemetry is None:

        return None


    if telemetry.empty:

        return None


    return telemetry


# ============================================================
# PROCESS ONE RACE
# ============================================================

def process_race(
    year,
    round_number,
    event_name
):

    print()
    print("=" * 70)

    print(
        f"Loading {year} {event_name}"
    )

    print("=" * 70)


    # ========================================================
    # SESSION
    # ========================================================

    try:

        session = fastf1.get_session(
            year,
            round_number,
            "R"
        )


        session.load(
            laps=True,
            telemetry=True,
            weather=True,
            messages=True
        )

    except Exception as error:

        print(
            f"[WARNING] Could not load "
            f"{event_name}: {error}"
        )

        return None


    # ========================================================
    # LAPS
    # ========================================================

    try:

        laps = (
            session.laps
            .copy()
        )

    except Exception as error:

        print(
            f"[WARNING] Could not access laps: "
            f"{error}"
        )

        return None


    if laps.empty:

        print(
            "[WARNING] No lap data available."
        )

        return None


    print(
        f"Drivers found: "
        f"{len(session.drivers)}"
    )

    print(
        f"Lap records: "
        f"{len(laps)}"
    )


    # ========================================================
    # DATASET
    # ========================================================

    rows = []


    total_laps_processed = 0

    telemetry_success = 0

    telemetry_failed = 0


    # ========================================================
    # DRIVERS
    # ========================================================

    drivers = list(
        laps[
            "Driver"
        ]
        .dropna()
        .unique()
    )


    for driver in drivers:

        print(
            f"  Processing {driver}..."
        )


        driver_laps = (
            laps[
                laps["Driver"] == driver
            ]
            .copy()
            .sort_values(
                "LapNumber"
            )
            .reset_index(
                drop=True
            )
        )


        # ====================================================
        # PROCESS LAPS
        # ====================================================

        for index, lap in (
            driver_laps.iterrows()
        ):

            lap_number = lap.get(
                "LapNumber",
                np.nan
            )


            if pd.isna(
                lap_number
            ):

                continue


            total_laps_processed += 1


            # =================================================
            # LAP TIME
            # =================================================

            lap_time_value = (
                lap.get(
                    "LapTime",
                    pd.NaT
                )
            )


            lap_time_seconds = (
                convert_time_to_seconds(
                    lap_time_value
                )
            )


            # =================================================
            # BASIC RACE STATE
            # =================================================

            row = {

                "year":
                    year,

                "round":
                    round_number,

                "event":
                    event_name,

                "driver":
                    driver,

                "lap":
                    lap_number,

                "position":
                    safe_value(
                        lap.get(
                            "Position",
                            np.nan
                        )
                    ),

                "lap_time":
                    lap_time_seconds,

                "compound":
                    lap.get(
                        "Compound",
                        "UNKNOWN"
                    ),

                "tyre_life":
                    safe_value(
                        lap.get(
                            "TyreLife",
                            np.nan
                        )
                    ),

                "stint":
                    safe_value(
                        lap.get(
                            "Stint",
                            np.nan
                        )
                    ),

                "track_status":
                    lap.get(
                        "TrackStatus",
                        "UNKNOWN"
                    ),

                "is_accurate":
                    lap.get(
                        "IsAccurate",
                        True
                    ),

                "telemetry_available":
                    0
            }


            # =================================================
            # TELEMETRY
            # =================================================

            telemetry = (
                get_lap_telemetry(
                    lap
                )
            )


            if telemetry is not None:

                telemetry_features = (
                    aggregate_telemetry(
                        telemetry
                    )
                )


                if telemetry_features:

                    row.update(
                        telemetry_features
                    )

                    row[
                        "telemetry_available"
                    ] = 1

                    telemetry_success += 1

                else:

                    telemetry_failed += 1

            else:

                telemetry_failed += 1


            # =================================================
            # NEXT POSITION
            # =================================================

            next_position = np.nan


            if (
                index + 1
                < len(driver_laps)
            ):

                next_lap = (
                    driver_laps.iloc[
                        index + 1
                    ]
                )


                next_position = (
                    next_lap.get(
                        "Position",
                        np.nan
                    )
                )


            row[
                "next_position"
            ] = safe_value(
                next_position
            )


            # =================================================
            # POSITION CHANGE
            # =================================================

            if (
                pd.notna(
                    row["position"]
                )
                and pd.notna(
                    next_position
                )
            ):

                position_change = (

                    float(
                        row["position"]
                    )

                    -

                    float(
                        next_position
                    )
                )


                row[
                    "position_gain"
                ] = position_change


                row[
                    "overtake"
                ] = (

                    1

                    if position_change > 0

                    else 0
                )

            else:

                row[
                    "position_gain"
                ] = np.nan

                row[
                    "overtake"
                ] = np.nan


            rows.append(
                row
            )


    # ========================================================
    # CHECK
    # ========================================================

    if not rows:

        print(
            "[WARNING] No rows created."
        )

        return None


    dataframe = pd.DataFrame(
        rows
    )


    # ========================================================
    # SAVE
    # ========================================================

    safe_event_name = (
        event_name
        .replace(
            " ",
            "_"
        )
        .replace(
            "/",
            "_"
        )
    )


    output_path = os.path.join(
        RAW_DIR,
        f"{round_number:02d}_"
        f"{safe_event_name}_race.csv"
    )


    dataframe.to_csv(
        output_path,
        index=False
    )


    # ========================================================
    # STATISTICS
    # ========================================================

    overtake_count = 0


    if (
        "overtake" in dataframe.columns
    ):

        valid_overtakes = (
            dataframe[
                "overtake"
            ]
            .dropna()
        )


        if not valid_overtakes.empty:

            overtake_count = int(
                valid_overtakes.sum()
            )


    telemetry_percentage = (

        (
            telemetry_success
            /
            total_laps_processed
        )
        * 100

        if total_laps_processed > 0

        else 0
    )


    # ========================================================
    # OUTPUT
    # ========================================================

    print()

    print(
        f"Saved: {output_path}"
    )

    print(
        f"Rows: {len(dataframe)}"
    )

    print(
        f"Overtake examples: "
        f"{overtake_count}"
    )

    print(
        f"Telemetry available: "
        f"{telemetry_success}/"
        f"{total_laps_processed}"
        f" ({telemetry_percentage:.1f}%)"
    )

    print(
        f"Telemetry unavailable: "
        f"{telemetry_failed}"
    )


    return dataframe


# ============================================================
# GET COMPLETED RACES
# ============================================================

def get_completed_races():

    print()

    print(
        "Getting 2026 race calendar..."
    )


    try:

        schedule = (
            fastf1.get_event_schedule(
                YEAR,
                include_testing=False
            )
        )

    except Exception as error:

        print(
            f"[ERROR] Could not get "
            f"calendar: {error}"
        )

        return []


    completed = []


    today = pd.Timestamp(
        "today"
    ).normalize()


    for _, event in (
        schedule.iterrows()
    ):

        event_date = pd.to_datetime(
            event.get(
                "EventDate",
                pd.NaT
            ),
            errors="coerce"
        )


        if pd.isna(
            event_date
        ):

            continue


        if (
            event_date.normalize()
            <= today
        ):

            completed.append(
                (
                    int(
                        event[
                            "RoundNumber"
                        ]
                    ),

                    str(
                        event[
                            "EventName"
                        ]
                    )
                )
            )


    return completed


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 70)

    print(
        "F1 AI RACE ENGINEER"
    )

    print(
        "REAL 2026 TELEMETRY DOWNLOADER"
    )

    print("=" * 70)


    # ========================================================
    # CALENDAR
    # ========================================================

    completed_races = (
        get_completed_races()
    )


    if not completed_races:

        print(
            "No completed races found."
        )

        return


    print()

    print(
        "Completed races:"
    )


    for (
        round_number,
        event_name
    ) in completed_races:

        print(
            f"  Round {round_number}: "
            f"{event_name}"
        )


    print()

    print(
        f"Total races to process: "
        f"{len(completed_races)}"
    )


    # ========================================================
    # PROCESS
    # ========================================================

    for (
        race_index,
        (
            round_number,
            event_name
        )
    ) in enumerate(
        completed_races,
        start=1
    ):

        print()

        print(
            f"[{race_index}/"
            f"{len(completed_races)}]"
        )


        # ====================================================
        # OUTPUT PATH
        # ====================================================

        safe_event_name = (
            event_name
            .replace(
                " ",
                "_"
            )
            .replace(
                "/",
                "_"
            )
        )


        output_path = os.path.join(
            RAW_DIR,
            f"{round_number:02d}_"
            f"{safe_event_name}_race.csv"
        )


        # ====================================================
        # EXISTING FILE
        # ====================================================

        if os.path.exists(
            output_path
        ):

            print(
                "Already downloaded:"
            )

            print(
                output_path
            )

            print(
                "Skipping..."
            )

            continue


        # ====================================================
        # PROCESS
        # ====================================================

        process_race(
            YEAR,
            round_number,
            event_name
        )


        time.sleep(
            2
        )


    # ========================================================
    # COMPLETE
    # ========================================================

    print()

    print("=" * 70)

    print(
        "DOWNLOAD COMPLETE"
    )

    print("=" * 70)

    print()

    print(
        "Raw data location:"
    )

    print(
        RAW_DIR
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()