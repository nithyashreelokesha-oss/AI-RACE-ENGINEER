def generate_explanation(
    race,
    deployment_mode,
    recommendation,
    overtake_probability,
    retention_probability
):

    battery = race["battery"]
    opportunity = race["overtake_opportunity"]
    threat = race["threat_level"]
    future = race["future_opportunity"]

    if recommendation == "ATTACK":

        if overtake_probability >= 0.75:
            reason = (
                f"Attack now. Overtake probability is "
                f"{overtake_probability * 100:.0f}% and the current "
                f"opportunity is strong."
            )

        else:
            reason = (
                "Attack because the combined strategic value "
                "of gaining position outweighs the energy and risk cost."
            )

        if retention_probability >= 0.75:
            reason += (
                f" Position retention is strong at "
                f"{retention_probability * 100:.0f}%, so enough energy "
                "remains to defend afterward."
            )
        else:
            reason += (
                " However, position retention is relatively weak, "
                "so post-overtake defense will be important."
            )

        return reason

    elif recommendation == "STAY":

        if future >= 0.70:
            return (
                "Stay and harvest. The current opportunity is not valuable "
                "enough to justify the energy cost, while a stronger "
                "opportunity is predicted soon."
            )

        return (
            "Stay and harvest to preserve the energy budget and improve "
            "future strategic flexibility."
        )

    else:

        if threat >= 0.70:
            return (
                "Defend now. The car behind represents a significant threat, "
                "so energy should be allocated toward maintaining the current "
                "position."
            )

        if battery < 30:
            return (
                "Defend conservatively. Energy reserves are low and the "
                "priority is preventing the race strategy from becoming "
                "energy-limited."
            )

        return (
            "Defend because protecting the current position has higher "
            "strategic value than attempting an overtake."
        )