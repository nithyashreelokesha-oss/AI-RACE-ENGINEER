from simulator.race import RaceSimulator
from main import run_decision_engine


simulator = RaceSimulator()

for _ in range(15):

    race = simulator.race

    result = run_decision_engine(race)

    print("\n-----------------------------")

    print(
        f"Lap {race['lap']}/{race['total_laps']}"
    )

    print(
        f"Battery: {race['battery']:.1f}%"
    )

    print(
        f"Gap ahead: {race['gap_ahead']:.2f}s"
    )

    print(
        f"Gap behind: {race['gap_behind']:.2f}s"
    )

    print(
        f"Mode: {result['deployment_mode']}"
    )

    print(
        f"Decision: {result['recommendation']}"
    )

    print(
        f"Overtake: "
        f"{result['overtake_probability'] * 100:.0f}%"
    )

    print(
        f"Retention: "
        f"{result['retention_probability'] * 100:.0f}%"
    )

    print(
        f"Why: {result['explanation']}"
    )

    # Let the race evolve
    simulator.update(
        result["deployment_mode"]
    )