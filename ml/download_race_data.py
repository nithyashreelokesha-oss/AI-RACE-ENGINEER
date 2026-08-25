import os
import time
import warnings
import json

import numpy as np
import pandas as pd
import fastf1


# ============================================================
# CONFIGURATION
# ============================================================

YEARS = [
    2023,
    2024,
    2025,
    2026
]

MAX_RETRIES = 3
RETRY_DELAY = 5
RACE_DELAY = 2


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RAW_BASE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw"
)

CACHE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "fastf1_cache"
)

FAILED_LOG_PATH = os.path.join(
    BASE_DIR,
    "data",
    "failed_downloads.json"
)


os.makedirs(
    RAW_BASE_DIR,
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
# FAILED DOWNLOAD TRACKING
# ============================================================

def load_failed_downloads():

    if not os.path.exists(
        FAILED_LOG_PATH
    ):

        return []

    try:

        with open(
            FAILED_LOG_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


def save_failed_download(
    year,
    round_number,
    event_name,
    error
):

    failed = load_failed_downloads()

    record = {

        "year":
            year,

        "round":
            round_number,

        "event":
            event_name,

        "error":
            str(error)
    }


    # Prevent duplicate entries.

    already_exists = any(

        item.get("year") == year
        and item.get("round") == round_number

        for item in failed
    )


    if not already_exists:

        failed.append(
            record
        )


    with open(
        FAILED_LOG_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            failed,
            file,
            indent=4
        )


# ============================================================
# TELEMETRY AGGREGATION
# ============================================================

def aggregate_telemetry(
    telemetry
):

    if telemetry is None:

        return {}


    if telemetry.empty:

        return {}


    result = {}


    # --------------------------------------------------------
    # SPEED
    # --------------------------------------------------------

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

            result["speed_range"] = float(
                speed.max()
                - speed.min()
            )

            result["speed_std"] = float(
                speed.std()
            )

            result["speed_variation"] = float(
                speed.std()
                / max(
                    speed.mean(),
                    1.0
                )
            )


    # --------------------------------------------------------
    # THROTTLE
    # --------------------------------------------------------

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

            result["throttle_full_usage"] = float(
                (throttle >= 95).mean()
            )


    # --------------------------------------------------------
    # BRAKE
    # --------------------------------------------------------

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
                (brake_numeric > 0).mean()
            )

            result["heavy_braking_usage"] = float(
                (brake_numeric > 80).mean()
            )


    # --------------------------------------------------------
    # RPM
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # GEAR
    # --------------------------------------------------------

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

            result["gear_std"] = float(
                gear.std()
            )


    # --------------------------------------------------------
    # DISTANCE
    # --------------------------------------------------------

    if "Distance" in telemetry.columns:

        distance = pd.to_numeric(
            telemetry["Distance"],
            errors="coerce"
        ).dropna()


        if not distance.empty:

            result["distance_min"] = float(
                distance.min()
            )

            result["distance_max"] = float(
                distance.max()
            )

            result["distance_range"] = float(
                distance.max()
                - distance.min()
            )


    # --------------------------------------------------------
    # POSITION DATA
    # --------------------------------------------------------

    if "X" in telemetry.columns:

        x = pd.to_numeric(
            telemetry["X"],
            errors="coerce"
        ).dropna()


        if not x.empty:

            result["x_range"] = float(
                x.max()
                - x.min()
            )


    if "Y" in telemetry.columns:

        y = pd.to_numeric(
            telemetry["Y"],
            errors="coerce"
        ).dropna()


        if not y.empty:

            result["y_range"] = float(
                y.max()
                - y.min()
            )


    if "Z" in telemetry.columns:

        z = pd.to_numeric(
            telemetry["Z"],
            errors="coerce"
        ).dropna()


        if not z.empty:

            result["z_range"] = float(
                z.max()
                - z.min()
            )


    return result


# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(
    value,
    default=np.nan
):

    if value is None:

        return default


    try:

        if pd.isna(value):

            return default

    except Exception:

        pass


    return value


# ============================================================
# TIME → SECONDS
# ============================================================

def timedelta_to_seconds(
    value
):

    if value is None:

        return np.nan


    try:

        if pd.isna(value):

            return np.nan

    except Exception:

        return np.nan


    try:

        return float(
            value.total_seconds()
        )

    except Exception:

        try:

            return float(value)

        except Exception:

            return np.nan


# ============================================================
# PIT DETECTION
# ============================================================

def lap_has_pit(
    lap
):

    pit_in = lap.get(
        "PitInTime",
        pd.NaT
    )

    pit_out = lap.get(
        "PitOutTime",
        pd.NaT
    )


    try:

        if pd.notna(pit_in):

            return True

    except Exception:

        pass


    try:

        if pd.notna(pit_out):

            return True

    except Exception:

        pass


    return False


# ============================================================
# GREEN LAP
# ============================================================

def is_green_lap(
    track_status
):

    if track_status is None:

        return False


    status = str(
        track_status
    ).strip()


    return status == "1"


# ============================================================
# OUTPUT FILE NAME
# ============================================================

def get_output_path(
    year,
    round_number,
    event_name
):

    year_dir = os.path.join(
        RAW_BASE_DIR,
        str(year)
    )


    os.makedirs(
        year_dir,
        exist_ok=True
    )


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


    return os.path.join(
        year_dir,
        f"{round_number:02d}_"
        f"{safe_event_name}_race.csv"
    )


# ============================================================
# PROCESS ONE RACE
# ============================================================

def process_race(
    year,
    round_number,
    event_name
):

    print()
    print(
        "=" * 75
    )

    print(
        f"Loading {year} - {event_name}"
    )

    print(
        "=" * 75
    )


    output_path = get_output_path(
        year,
        round_number,
        event_name
    )


    # ========================================================
    # EXISTING FILE
    # ========================================================

    if os.path.exists(
        output_path
    ):

        print(
            "✓ Already downloaded"
        )

        print(
            f"  {output_path}"
        )

        return True


    # ========================================================
    # RETRY LOOP
    # ========================================================

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        print()
        print(
            f"Attempt "
            f"{attempt}/{MAX_RETRIES}"
        )


        try:

            # ------------------------------------------------
            # SESSION
            # ------------------------------------------------

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


            # ------------------------------------------------
            # LAPS
            # ------------------------------------------------

            laps = session.laps.copy()


            if laps.empty:

                raise RuntimeError(
                    "No lap data available."
                )


            print(
                f"Drivers: "
                f"{len(session.drivers)}"
            )

            print(
                f"Lap records: "
                f"{len(laps)}"
            )


            # =================================================
            # PROCESS DRIVERS
            # =================================================

            rows = []


            drivers = list(
                laps["Driver"]
                .dropna()
                .unique()
            )


            for driver in drivers:

                print(
                    f"  Processing "
                    f"{driver}..."
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


                # =============================================
                # PROCESS EACH LAP
                # =============================================

                for index, lap in (
                    driver_laps.iterrows()
                ):

                    lap_number = safe_value(
                        lap.get(
                            "LapNumber",
                            np.nan
                        )
                    )


                    if pd.isna(
                        lap_number
                    ):

                        continue


                    # -----------------------------------------
                    # BASIC DATA
                    # -----------------------------------------

                    lap_time = (
                        timedelta_to_seconds(
                            lap.get(
                                "LapTime",
                                pd.NaT
                            )
                        )
                    )


                    position = safe_value(
                        lap.get(
                            "Position",
                            np.nan
                        )
                    )


                    compound = str(
                        lap.get(
                            "Compound",
                            "UNKNOWN"
                        )
                    ).upper()


                    tyre_life = safe_value(
                        lap.get(
                            "TyreLife",
                            np.nan
                        )
                    )


                    stint = safe_value(
                        lap.get(
                            "Stint",
                            np.nan
                        )
                    )


                    track_status = str(
                        lap.get(
                            "TrackStatus",
                            "UNKNOWN"
                        )
                    )


                    # -----------------------------------------
                    # PIT
                    # -----------------------------------------

                    pit_current = (
                        lap_has_pit(
                            lap
                        )
                    )


                    # -----------------------------------------
                    # NEXT LAP
                    # -----------------------------------------

                    next_position = np.nan
                    next_lap_time = np.nan
                    next_track_status = "UNKNOWN"
                    pit_next = False


                    if (
                        index + 1
                        < len(driver_laps)
                    ):

                        next_lap = (
                            driver_laps.iloc[
                                index + 1
                            ]
                        )


                        next_position = safe_value(
                            next_lap.get(
                                "Position",
                                np.nan
                            )
                        )


                        next_lap_time = (
                            timedelta_to_seconds(
                                next_lap.get(
                                    "LapTime",
                                    pd.NaT
                                )
                            )
                        )


                        next_track_status = str(
                            next_lap.get(
                                "TrackStatus",
                                "UNKNOWN"
                            )
                        )


                        pit_next = (
                            lap_has_pit(
                                next_lap
                            )
                        )


                    # -----------------------------------------
                    # TELEMETRY
                    # -----------------------------------------

                    telemetry_available = False

                    telemetry_features = {}


                    try:

                        telemetry = (
                            lap.get_telemetry()
                        )


                        if (
                            telemetry is not None
                            and not telemetry.empty
                        ):

                            telemetry_available = True


                            telemetry_features = (
                                aggregate_telemetry(
                                    telemetry
                                )
                            )


                    except Exception as telemetry_error:

                        # One bad telemetry lap should
                        # NOT kill the entire race.

                        print(
                            f"    Telemetry warning: "
                            f"{driver} lap "
                            f"{lap_number} -> "
                            f"{telemetry_error}"
                        )


                    # -----------------------------------------
                    # PREVIOUS LAP
                    # -----------------------------------------

                    previous_lap_time = np.nan


                    if index > 0:

                        previous_lap = (
                            driver_laps.iloc[
                                index - 1
                            ]
                        )


                        previous_lap_time = (
                            timedelta_to_seconds(
                                previous_lap.get(
                                    "LapTime",
                                    pd.NaT
                                )
                            )
                        )


                    # -----------------------------------------
                    # LAP TIME DELTA
                    # -----------------------------------------

                    if (
                        pd.notna(lap_time)
                        and
                        pd.notna(previous_lap_time)
                    ):

                        lap_time_delta = (
                            lap_time
                            - previous_lap_time
                        )

                    else:

                        lap_time_delta = np.nan


                    # -----------------------------------------
                    # POSITION DELTA
                    # -----------------------------------------

                    if (
                        pd.notna(position)
                        and
                        pd.notna(next_position)
                    ):

                        position_delta = (
                            float(position)
                            - float(next_position)
                        )

                    else:

                        position_delta = np.nan


                    # -----------------------------------------
                    # CLEAN OVERTAKE TARGET
                    # -----------------------------------------

                    clean_position_gain = (

                        pd.notna(
                            position_delta
                        )

                        and

                        position_delta > 0

                        and

                        not pit_current

                        and

                        not pit_next

                        and

                        is_green_lap(
                            track_status
                        )

                        and

                        is_green_lap(
                            next_track_status
                        )
                    )


                    overtake = (
                        1
                        if clean_position_gain
                        else 0
                    )


                    # -----------------------------------------
                    # BUILD ROW
                    # -----------------------------------------

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
                            position,

                        "lap_time":
                            lap_time,

                        "previous_lap_time":
                            previous_lap_time,

                        "lap_time_delta":
                            lap_time_delta,

                        "compound":
                            compound,

                        "tyre_life":
                            tyre_life,

                        "stint":
                            stint,

                        "track_status":
                            track_status,

                        "next_track_status":
                            next_track_status,

                        "next_position":
                            next_position,

                        "position_delta":
                            position_delta,

                        "pit_current":
                            int(
                                pit_current
                            ),

                        "pit_next":
                            int(
                                pit_next
                            ),

                        "telemetry_available":
                            int(
                                telemetry_available
                            ),

                        "overtake":
                            overtake
                    }


                    row.update(
                        telemetry_features
                    )


                    rows.append(
                        row
                    )


            # =================================================
            # DATAFRAME
            # =================================================

            if not rows:

                raise RuntimeError(
                    "No dataset rows generated."
                )


            dataframe = pd.DataFrame(
                rows
            )


            # =================================================
            # SAVE ONLY AFTER FULL RACE
            # =================================================

            dataframe.to_csv(
                output_path,
                index=False
            )


            telemetry_count = int(
                dataframe[
                    "telemetry_available"
                ].sum()
            )


            overtake_count = int(
                dataframe[
                    "overtake"
                ].sum()
            )


            print()
            print(
                "✓ RACE COMPLETE"
            )


            print(
                f"Saved: "
                f"{output_path}"
            )


            print(
                f"Rows: "
                f"{len(dataframe)}"
            )


            print(
                f"Telemetry rows: "
                f"{telemetry_count}"
            )


            print(
                f"Clean overtake candidates: "
                f"{overtake_count}"
            )


            return True


        except Exception as error:

            print()
            print(
                f"[WARNING] "
                f"Race failed on attempt "
                f"{attempt}:"
            )


            print(
                f"  {type(error).__name__}: "
                f"{error}"
            )


            if attempt < MAX_RETRIES:

                wait_time = (
                    RETRY_DELAY
                    * attempt
                )


                print(
                    f"Retrying in "
                    f"{wait_time} seconds..."
                )


                time.sleep(
                    wait_time
                )

            else:

                print(
                    "✗ Giving up on this race."
                )


                save_failed_download(
                    year,
                    round_number,
                    event_name,
                    error
                )


                return False


# ============================================================
# GET COMPLETED RACES
# ============================================================

def get_completed_races(
    year
):

    print()
    print(
        f"Getting {year} calendar..."
    )


    try:

        schedule = (
            fastf1.get_event_schedule(
                year,
                include_testing=False
            )
        )


    except Exception as error:

        print(
            f"[ERROR] Calendar failed "
            f"for {year}: {error}"
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

            round_number = safe_value(
                event.get(
                    "RoundNumber",
                    np.nan
                )
            )


            if pd.isna(
                round_number
            ):

                continue


            completed.append(
                (
                    int(
                        round_number
                    ),

                    str(
                        event.get(
                            "EventName",
                            "Unknown"
                        )
                    )
                )
            )


    return completed


# ============================================================
# GET EXISTING RACES
# ============================================================

def get_existing_races(
    year,
    completed_races
):

    existing = []


    for round_number, event_name in (
        completed_races
    ):

        output_path = get_output_path(
            year,
            round_number,
            event_name
        )


        if os.path.exists(
            output_path
        ):

            existing.append(
                (
                    round_number,
                    event_name
                )
            )


    return existing


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 75
    )

    print(
        "🏎️ F1 AI RACE ENGINEER"
    )

    print(
        "MULTI-SEASON REAL F1 TELEMETRY DOWNLOADER"
    )

    print(
        "=" * 75
    )


    total_completed = 0
    total_existing = 0
    total_downloaded = 0
    total_failed = 0


    # ========================================================
    # SEASONS
    # ========================================================

    for year in YEARS:

        print()
        print(
            "#" * 75
        )

        print(
            f"SEASON {year}"
        )

        print(
            "#" * 75
        )


        completed_races = (
            get_completed_races(
                year
            )
        )


        if not completed_races:

            print(
                f"No completed races "
                f"found for {year}."
            )

            continue


        total_completed += (
            len(
                completed_races
            )
        )


        existing_races = (
            get_existing_races(
                year,
                completed_races
            )
        )


        print()
        print(
            f"Completed races: "
            f"{len(completed_races)}"
        )


        print(
            f"Already downloaded: "
            f"{len(existing_races)}"
        )


        print(
            f"Remaining: "
            f"{len(completed_races) - len(existing_races)}"
        )


        # ====================================================
        # RACE LOOP
        # ====================================================

        for race_index, (
            round_number,
            event_name
        ) in enumerate(
            completed_races,
            start=1
        ):

            output_path = get_output_path(
                year,
                round_number,
                event_name
            )


            print()
            print(
                "-" * 75
            )


            print(
                f"{year} "
                f"Race {race_index}/"
                f"{len(completed_races)}"
            )


            print(
                f"Round {round_number}: "
                f"{event_name}"
            )


            # =================================================
            # SKIP EXISTING
            # =================================================

            if os.path.exists(
                output_path
            ):

                print(
                    "✓ Already downloaded."
                )

                total_existing += 1

                continue


            # =================================================
            # DOWNLOAD
            # =================================================

            success = process_race(
                year,
                round_number,
                event_name
            )


            if success:

                total_downloaded += 1

            else:

                total_failed += 1


            # =================================================
            # DELAY
            # =================================================

            print()
            print(
                f"Waiting "
                f"{RACE_DELAY}s before "
                f"next race..."
            )


            time.sleep(
                RACE_DELAY
            )


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print(
        "=" * 75
    )

    print(
        "DOWNLOAD COMPLETE"
    )

    print(
        "=" * 75
    )


    print()
    print(
        f"Total completed races found: "
        f"{total_completed}"
    )


    print(
        f"Already existed: "
        f"{total_existing}"
    )


    print(
        f"Newly downloaded: "
        f"{total_downloaded}"
    )


    print(
        f"Failed: "
        f"{total_failed}"
    )


    print()
    print(
        "Raw data location:"
    )


    print(
        RAW_BASE_DIR
    )


    # ========================================================
    # FAILED RACES
    # ========================================================

    failed = load_failed_downloads()


    if failed:

        print()
        print(
            "RACES THAT NEED RETRY:"
        )


        for item in failed:

            print(
                f"  {item['year']} "
                f"Round {item['round']} - "
                f"{item['event']}"
            )


        print()
        print(
            "Failure log:"
        )


        print(
            FAILED_LOG_PATH
        )

    else:

        print()
        print(
            "✓ No failed races."
        )


    print()
    print(
        "You can safely run this script "
        "again at any time."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()