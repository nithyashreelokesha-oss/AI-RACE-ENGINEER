import streamlit as st

from engine.energy import (
    get_deployment_mode,
    calculate_deployment
)

from engine.overtake import (
    calculate_overtake_probability,
    calculate_ml_probability,
    get_ml_status
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

from engine.whatif import (
    run_what_if
)

from simulator.race import (
    RaceSimulator
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Race Engineer",
    page_icon="🏎️",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "simulator" not in st.session_state:
    st.session_state.simulator = RaceSimulator()

simulator = st.session_state.simulator


# ============================================================
# TITLE
# ============================================================

st.title("🏎️ AI Race Engineer")

st.caption(
    "AI Motorsport Intelligence • "
    "Energy • Overtaking • Tyres • Strategy • ML"
)


# ============================================================
# CUSTOM RACE START
# ============================================================

with st.expander("🏁 Custom Race Start", expanded=True):

    st.caption(
        "Start the simulation from any lap and race state. "
        "Set the gaps, starting position, sector layout and current tyre/energy state."
    )

    custom_col1, custom_col2, custom_col3, custom_col4 = st.columns(4)

    with custom_col1:
        custom_total_laps = st.number_input(
            "Total Laps",
            min_value=1,
            max_value=200,
            value=int(simulator.race.get("total_laps", 57)),
            step=1
        )

    with custom_col2:
        custom_start_lap = st.number_input(
            "Start Lap",
            min_value=1,
            max_value=int(custom_total_laps),
            value=min(
                int(simulator.race.get("lap", 1)),
                int(custom_total_laps)
            ),
            step=1
        )

    with custom_col3:
        custom_start_position = st.number_input(
            "Starting Position",
            min_value=1,
            max_value=20,
            value=int(simulator.race.get("position", 6)),
            step=1
        )

    with custom_col4:
        custom_start_sector = st.selectbox(
            "Starting Sector",
            [1, 2, 3],
            index=int(simulator.race.get("sector", 1)) - 1
        )

    gap_col1, gap_col2, tyre_col1, tyre_col2 = st.columns(4)

    with gap_col1:
        custom_gap_ahead = st.number_input(
            "Gap Ahead (s)",
            min_value=0.0,
            max_value=10.0,
            value=0.65 if custom_start_position > 1 else 0.0,
            step=0.05
        )

    with gap_col2:
        custom_gap_behind = st.number_input(
            "Gap Behind (s)",
            min_value=0.05,
            max_value=10.0,
            value=0.90,
            step=0.05
        )

    with tyre_col1:
        custom_compound = st.selectbox(
            "Starting Tyre Compound",
            ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"],
            index=["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"].index(
                simulator.race.get("tyre_compound", "MEDIUM")
            )
        )

    with tyre_col2:
        custom_tyre_age = st.number_input(
            "Starting Tyre Age (laps)",
            min_value=0.0,
            max_value=60.0,
            value=float(simulator.race.get("tyre_age", 0.0)),
            step=0.1
        )

    battery_col, sector1_col, sector2_col, sector3_col = st.columns(4)

    with battery_col:
        custom_battery = st.number_input(
            "Starting Battery (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(simulator.race.get("battery", 100.0)),
            step=1.0
        )

    sector_options = [
        "HIGH_SPEED",
        "TECHNICAL",
        "STRAIGHT",
        "MEDIUM_SPEED",
        "SLOW_CORNER"
    ]

    current_sector_types = simulator.sector_types

    with sector1_col:
        custom_s1 = st.selectbox(
            "Sector 1 Type",
            sector_options,
            index=sector_options.index(
                current_sector_types.get(1, "HIGH_SPEED")
            )
        )

    with sector2_col:
        custom_s2 = st.selectbox(
            "Sector 2 Type",
            sector_options,
            index=sector_options.index(
                current_sector_types.get(2, "TECHNICAL")
            )
        )

    with sector3_col:
        custom_s3 = st.selectbox(
            "Sector 3 Type",
            sector_options,
            index=sector_options.index(
                current_sector_types.get(3, "STRAIGHT")
            )
        )

    if st.button(
        "🏁 START CUSTOM RACE",
        type="primary",
        use_container_width=True
    ):
        st.session_state.simulator = RaceSimulator(
            total_laps=int(custom_total_laps),
            start_lap=int(custom_start_lap),
            start_position=int(custom_start_position),
            gap_ahead=float(custom_gap_ahead),
            gap_behind=float(custom_gap_behind),
            start_sector=int(custom_start_sector),
            sector_types={
                1: custom_s1,
                2: custom_s2,
                3: custom_s3
            },
            start_compound=custom_compound,
            start_tyre_age=float(custom_tyre_age),
            start_battery=float(custom_battery)
        )
        st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Strategy Preferences")

st.sidebar.caption(
    "Adjust how strongly each factor influences "
    "the AI decision."
)


# ============================================================
# STRATEGY WEIGHTS
# ============================================================

weight_overtake = st.sidebar.slider(
    "🏎️ Overtake Opportunity",
    0.0, 2.0, 1.0, 0.1
)

weight_retention = st.sidebar.slider(
    "🛡️ Position Retention",
    0.0, 2.0, 1.0, 0.1
)

weight_current = st.sidebar.slider(
    "⚡ Current Opportunity",
    0.0, 2.0, 1.0, 0.1
)

weight_future = st.sidebar.slider(
    "🔮 Future Opportunity",
    0.0, 2.0, 1.0, 0.1
)

weight_energy = st.sidebar.slider(
    "🔋 Battery / Energy",
    0.0, 2.0, 1.0, 0.1
)

weight_tyres = st.sidebar.slider(
    "🛞 Tyre Condition",
    0.0, 2.0, 1.0, 0.1
)

weight_threat = st.sidebar.slider(
    "⚠️ Threat Behind",
    0.0, 2.0, 1.0, 0.1
)


strategy_weights = {

    "overtake": weight_overtake,

    "retention": weight_retention,

    "current_opportunity": weight_current,

    "future_opportunity": weight_future,

    "energy": weight_energy,

    "tyres": weight_tyres,

    "threat": weight_threat
}


# ============================================================
# RACE CONTEXT
# ============================================================

st.sidebar.divider()

st.sidebar.subheader("🏁 Race Conditions")

track_limit_risk = st.sidebar.slider(
    "⚠️ Track-Limit Risk",
    0.0,
    1.0,
    0.05,
    0.05
)

race_condition = st.sidebar.selectbox(
    "🚦 Race Control",
    [
        "NORMAL",
        "WET",
        "VSC",
        "SAFETY CAR"
    ]
)




# Apply race context
simulator.race["track_limit_risk"] = track_limit_risk
simulator.race["race_condition"] = race_condition



# ============================================================
# PIT STOP
# ============================================================

st.sidebar.divider()

st.sidebar.subheader("🛞 Pit Wall")

new_compound = st.sidebar.selectbox(
    "New Tyre Compound",
    [
        "SOFT",
        "MEDIUM",
        "HARD",
        "INTERMEDIATE",
        "WET"
    ],
    index=1
)

if st.sidebar.button(
    "🛞 PIT STOP",
    type="primary",
    use_container_width=True
):

    pit_result = simulator.pit_stop(
        new_compound
    )

    st.sidebar.success(
        f"Fitted {pit_result['compound']} tyres. "
        f"Tyre age reset to 0 laps."
    )

    st.rerun()


# ============================================================
# RESET
# ============================================================

if st.sidebar.button(
    "🔄 Reset Race",
    use_container_width=True
):

    st.session_state.simulator = RaceSimulator()

    st.rerun()


# ============================================================
# CURRENT RACE STATE
# ============================================================

race = simulator.get_state()


# ============================================================
# AI CALCULATIONS
# ============================================================

deployment_mode = get_deployment_mode(
    race,
    strategy_weights
)

deployment = calculate_deployment(
    race,
    deployment_mode
)

overtake_probability = calculate_overtake_probability(
    race
)

ml_probability = calculate_ml_probability(
    race
)

ml_status = get_ml_status()

retention_probability = calculate_retention_probability(
    race,
    deployment_mode
)

scores, recommendation = evaluate_strategy(
    race,
    deployment_mode,
    strategy_weights
)


# ============================================================
# TOP LIVE DASHBOARD
# ============================================================

st.subheader("📡 Live Race Dashboard")

top1, top2, top3, top4, top5, top6 = st.columns(6)

with top1:
    st.metric(
        "Lap",
        f"{race['lap']} / {race['total_laps']}"
    )

with top2:
    st.metric(
        "Sector",
        f"S{race['sector']}"
    )

with top3:
    st.metric(
        "Position",
        f"P{race['position']}"
    )

with top4:
    st.metric(
        "Battery",
        f"{race['battery']:.1f}%"
    )

with top5:
    st.metric(
        "Tyres",
        race["tyre_compound"]
    )

with top6:
    st.metric(
        "Tyre Life",
        f"{race['tyre_life_remaining']:.1f} laps"
    )


# ============================================================
# AI DECISION
# ============================================================

st.subheader("🤖 AI Race Decision")

dec1, dec2, dec3, dec4 = st.columns(4)

with dec1:

    st.metric(
        "Deployment",
        deployment_mode
    )

    st.caption(
        f"{deployment['target_percentage']:.1f}% target"
    )

with dec2:

    st.metric(
        "Strategy",
        recommendation
    )

    st.caption(
        f"Retention: "
        f"{retention_probability * 100:.0f}%"
    )

with dec3:

    st.metric(
        "Hybrid Overtake",
        f"{overtake_probability * 100:.1f}%"
    )

    st.caption(
        f"Opportunity: "
        f"{race['overtake_opportunity'] * 100:.0f}%"
    )

with dec4:

    if ml_probability is not None:

        st.metric(
            "Random Forest",
            f"{ml_probability * 100:.1f}%"
        )

        difference = (
            overtake_probability
            - ml_probability
        )

        st.caption(
            f"Hybrid difference: "
            f"{difference * 100:+.1f}%"
        )

    else:

        st.metric(
            "Random Forest",
            "Unavailable"
        )

        st.caption(
            "Check model compatibility"
        )


# ============================================================
# ML STATUS
# ============================================================

if ml_status["available"]:

    st.success(
        "🤖 Random Forest Overtake Model: ACTIVE"
    )

else:

    st.warning(
        "⚠️ Random Forest Overtake Model: NOT AVAILABLE"
    )

    if ml_status.get("error"):

        st.caption(
            f"Model error: {ml_status['error']}"
        )


# ============================================================
# SECTOR ACTION
# ============================================================

st.subheader("🏁 Sector Control")

action1, action2, action3 = st.columns(3)

with action1:

    st.metric(
        "Current Sector",
        f"S{race['sector']} — {race['sector_name']}"
    )

with action2:

    st.metric(
        "Gap Ahead",
        "—"
        if race["position"] == 1
        else f"{race['gap_ahead']:.2f}s"
    )

with action3:

    st.metric(
        "Gap Behind",
        f"{race['gap_behind']:.2f}s"
    )


# ============================================================
# DRIVER CONTROL / AI OVERRIDE
# ============================================================

st.subheader("🎮 Driver Control")

control_col1, control_col2, control_col3 = st.columns(3)

with control_col1:
    control_mode = st.radio(
        "Who controls this sector?",
        ["Follow AI", "Manual Driver Input"],
        horizontal=True
    )

if control_mode == "Manual Driver Input":
    with control_col2:
        driver_deployment = st.selectbox(
            "Driver Deployment",
            ["PUSH", "BALANCED", "HARVEST", "CONSERVE"],
            index=["PUSH", "BALANCED", "HARVEST", "CONSERVE"].index(
                deployment_mode
            )
        )

    with control_col3:
        driver_strategy = st.selectbox(
            "Driver Strategy",
            ["ATTACK", "STAY", "DEFEND"],
            index=["ATTACK", "STAY", "DEFEND"].index(
                recommendation
            )
        )

    actual_deployment = driver_deployment
    actual_strategy = driver_strategy
    driver_controlled = True

    st.warning(
        f"AI recommends **{deployment_mode} + {recommendation}**, "
        f"but the driver will use **{actual_deployment} + {actual_strategy}**. "
        "The simulator will carry the consequences of this override forward."
    )
else:
    actual_deployment = deployment_mode
    actual_strategy = recommendation
    driver_controlled = False

    st.success(
        f"Driver follows AI: **{deployment_mode} + {recommendation}**"
    )


# ============================================================
# RUN SECTOR
# ============================================================

if st.button(
    "▶️ RUN NEXT SECTOR",
    type="primary",
    use_container_width=True
):

    result = simulator.update(
        actual_deployment,
        actual_strategy,
        ai_deployment_mode=deployment_mode,
        ai_recommendation=recommendation,
        driver_controlled=driver_controlled
    )

    if result["overtook"]:

        st.success(
            f"🏎️ OVERTAKE SUCCESSFUL! "
            f"Moved to P{result['position']}."
        )

    elif result["lost_position"]:

        st.error(
            f"⚠️ POSITION LOST! "
            f"Dropped to P{result['position']}."
        )

    else:

        st.info(
            f"Sector completed. "
            f"Position remains P{result['position']}."
        )

    st.write(
        f"**Completed:** "
        f"Lap {result['completed_lap']} — "
        f"{result['completed_sector_name']}"
    )

    energy_used = result["deployment"].get(
        "target_energy_per_sector",
        0
    )

    st.write(
        f"Energy deployed: **{energy_used:.2f}**"
    )

    st.write(
        f"Battery remaining: "
        f"**{result['battery']:.1f}%**"
    )

    st.write(
        f"Tyres: **{result['tyre_compound']} — "
        f"{result['tyre_condition']}**"
    )

    st.write(
        f"Tyre age: **{result['tyre_age']:.1f} laps**"
    )

    st.write(
        f"Tyre life remaining: "
        f"**{result['tyre_life_remaining']:.1f} laps**"
    )

    if result["lap_completed"]:

        st.success(
            f"🏁 Lap completed! "
            f"Now entering Lap {result['lap']} — Sector 1."
        )

    if result["race_finished"]:

        st.success(
            f"🏆 RACE FINISHED! "
            f"Final position: P{result['position']}"
        )

    st.rerun()


# ============================================================
# COMPACT INFORMATION TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🛞 Tyres & Rules",
        "🔋 Energy",
        "📊 Strategy",
        "🧠 AI Analysis"
    ]
)


# ============================================================
# TAB 1 — TYRES + RULES
# ============================================================

with tab1:

    tyre1, tyre2, tyre3, tyre4 = st.columns(4)

    with tyre1:
        st.metric(
            "Compound",
            race["tyre_compound"]
        )

    with tyre2:
        st.metric(
            "Tyre Status",
            race["tyre_condition"]
        )

    with tyre3:
        st.metric(
            "Tyre Age",
            f"{race['tyre_age']:.1f} laps"
        )

    with tyre4:
        st.metric(
            "Life Remaining",
            f"{race['tyre_life_remaining']:.1f}"
        )

    st.progress(
        min(
            max(
                race["tyre_life_remaining"]
                / max(race["effective_tyre_life"], 1),
                0.0
            ),
            1.0
        )
    )

    st.write(
        f"**Base compound life:** "
        f"{race['base_tyre_life']:.1f} laps"
    )

    st.write(
        f"**Effective life:** "
        f"{race['effective_tyre_life']:.1f} laps"
    )

    st.write(
        f"**Tyre degradation:** "
        f"{race['tyre_degradation']:.1f}%"
    )

    st.write(
        f"**Tyre advantage:** "
        f"{race['tyre_advantage']:.2f}"
    )

    st.divider()

    st.subheader("🏁 Rule & Race Context")

    r1, r2, r3 = st.columns(3)

    with r1:
        st.metric(
            "Track-Limit Risk",
            f"{race['track_limit_risk'] * 100:.0f}%"
        )

    with r2:
        st.metric(
            "Race Control",
            race["race_condition"]
        )

   
    if race["race_condition"] == "NORMAL":
        st.caption(
            "Normal racing conditions."
        )

    elif race["race_condition"] == "WET":
        st.caption(
            "Wet conditions reduce confidence in dry-line assumptions."
        )

    elif race["race_condition"] == "VSC":
        st.caption(
            "VSC significantly restricts normal overtaking opportunities."
        )

    else:
        st.caption(
            "Safety Car conditions strongly restrict overtaking."
        )


# ============================================================
# TAB 2 — ENERGY
# ============================================================

with tab2:

    e1, e2, e3 = st.columns(3)

    with e1:
        st.metric(
            "Target Deployment",
            f"{deployment['target_percentage']:.1f}%"
        )

    with e2:
        st.metric(
            "Baseline Deployment",
            f"{deployment['baseline_percentage']:.1f}%"
        )

    with e3:
        st.metric(
            "Battery",
            f"{race['battery']:.1f}%"
        )

    st.progress(
        min(
            max(
                deployment["target_percentage"] / 100,
                0
            ),
            1
        )
    )

    st.write(
        f"**Baseline energy / sector:** "
        f"{deployment['baseline_energy_per_sector']:.2f}"
    )

    st.write(
        f"**Target energy / sector:** "
        f"{deployment['target_energy_per_sector']:.2f}"
    )

    st.write(
        f"**Remaining laps:** "
        f"{deployment['remaining_laps']}"
    )


# ============================================================
# TAB 3 — STRATEGY
# ============================================================

with tab3:

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric(
            "ATTACK",
            f"{scores['ATTACK']:.2f}"
        )

    with s2:
        st.metric(
            "STAY",
            f"{scores['STAY']:.2f}"
        )

    with s3:
        st.metric(
            "DEFEND",
            f"{scores['DEFEND']:.2f}"
        )

    st.divider()

    st.subheader("Strategy Weights")

    w1, w2 = st.columns(2)

    with w1:

        st.write(
            f"Overtake: **{weight_overtake:.1f}**"
        )

        st.write(
            f"Retention: **{weight_retention:.1f}**"
        )

        st.write(
            f"Current Opportunity: **{weight_current:.1f}**"
        )

        st.write(
            f"Future Opportunity: **{weight_future:.1f}**"
        )

    with w2:

        st.write(
            f"Energy: **{weight_energy:.1f}**"
        )

        st.write(
            f"Tyres: **{weight_tyres:.1f}**"
        )

        st.write(
            f"Threat: **{weight_threat:.1f}**"
        )

    st.divider()

    st.subheader("🎮 Driver / AI Alignment")

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        st.metric(
            "AI Follows",
            race["ai_follow_count"]
        )

    with a2:
        st.metric(
            "Driver Overrides",
            race["driver_override_count"]
        )

    with a3:
        st.metric(
            "Strategy Deviation",
            f"{race["strategy_deviation"]:.1f}"
        )

    with a4:
        st.metric(
            "Last Override",
            "YES" if race["last_driver_override"] else "NO"
        )

    if race["last_driver_override"]:
        st.caption(
            f"Last AI plan: **{race["last_ai_deployment"]} + "
            f"{race["last_ai_recommendation"]}** • "
            f"Driver energy penalty: **{race["driver_energy_penalty"]:.1f}%** • "
            f"Tyre penalty: **{race["driver_tyre_penalty"]:.1f}%**"
        )

    st.divider()

    st.subheader("🔮 What-If Analysis")

    if st.button(
        "Run What-If Analysis",
        use_container_width=True
    ):

        scenarios = run_what_if(
            race,
            strategy_weights
        )

        q1, q2, q3 = st.columns(3)

        with q1:

            st.markdown("### 🏎️ ATTACK")

            st.write(
                f"Score: **{scenarios['ATTACK']['score']:.2f}**"
            )

            st.write(
                f"Overtake: "
                f"**{scenarios['ATTACK']['overtake_probability'] * 100:.0f}%**"
            )

            st.write(
                f"Position: **P{scenarios['ATTACK']['position']}**"
            )

        with q2:

            st.markdown("### 🟡 STAY")

            st.write(
                f"Score: **{scenarios['STAY']['score']:.2f}**"
            )

            st.write(
                f"Retention: "
                f"**{scenarios['STAY']['retention_probability'] * 100:.0f}%**"
            )

            st.write(
                f"Position: **P{scenarios['STAY']['position']}**"
            )

        with q3:

            st.markdown("### 🛡️ DEFEND")

            st.write(
                f"Score: **{scenarios['DEFEND']['score']:.2f}**"
            )

            st.write(
                f"Retention: "
                f"**{scenarios['DEFEND']['retention_probability'] * 100:.0f}%**"
            )

            st.write(
                f"Position: **P{scenarios['DEFEND']['position']}**"
            )


# ============================================================
# TAB 4 — AI ANALYSIS
# ============================================================

with tab4:

    st.subheader("🧠 Random Forest + Heuristic")

    m1, m2, m3 = st.columns(3)

    with m1:

        if ml_probability is not None:

            st.metric(
                "Random Forest",
                f"{ml_probability * 100:.1f}%"
            )

        else:

            st.metric(
                "Random Forest",
                "Unavailable"
            )

    with m2:

        st.metric(
            "Heuristic / Hybrid",
            f"{overtake_probability * 100:.1f}%"
        )

    with m3:

        if ml_probability is not None:

            difference = (
                overtake_probability
                - ml_probability
            )

            st.metric(
                "Hybrid Difference",
                f"{difference * 100:+.1f}%"
            )

        else:

            st.metric(
                "Hybrid Difference",
                "N/A"
            )

    st.divider()

    st.subheader("Sector Intelligence")

    c1, c2 = st.columns(2)

    with c1:

        st.write(
            f"**Sector type:** {race['sector_type']}"
        )

        st.write(
            f"**Energy demand:** "
            f"{race['sector_energy_demand']:.2f}"
        )

        st.write(
            f"**Overtaking base:** "
            f"{race['sector_overtaking_base']:.0%}"
        )

        st.write(
            f"**Braking importance:** "
            f"{race['sector_braking_importance']:.2f}"
        )

    with c2:

        st.write(
            f"**Traction importance:** "
            f"{race['sector_traction_importance']:.2f}"
        )

        st.write(
            f"**Current opportunity:** "
            f"{race['overtake_opportunity']:.0%}"
        )

        st.write(
            f"**Future opportunity:** "
            f"{race['future_opportunity']:.0%}"
        )

        st.write(
            f"**Threat behind:** "
            f"{race['threat_level']:.0%}"
        )

    st.divider()

    st.subheader("🧠 AI Reasoning")

    explanation = generate_explanation(
        race,
        deployment_mode,
        recommendation,
        overtake_probability,
        retention_probability
    )

    st.info(explanation)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Race Engineer • Sector-level race intelligence • "
    "Energy • Overtaking • Tyres • Strategy • Hybrid ML"
)