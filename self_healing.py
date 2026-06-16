from datetime import datetime

# -------------------------
# SELF HEALING ACTIONS
# -------------------------
def auto_remediate(service, risk):

    actions = []

    # -------------------------
    # CRITICAL RISK
    # -------------------------
    if risk >= 0.9:

        actions.append(
            f"Restarted {service} service"
        )

        actions.append(
            f"Scaled {service} replicas"
        )

        actions.append(
            f"Triggered failover for {service}"
        )

    # -------------------------
    # HIGH RISK
    # -------------------------
    elif risk >= 0.75:

        actions.append(
            f"Increased resources for {service}"
        )

        actions.append(
            f"Cleared traffic spikes"
        )

    # -------------------------
    # MODERATE RISK
    # -------------------------
    elif risk >= 0.6:

        actions.append(
            f"Monitoring {service} closely"
        )

    return {
        "service": service,
        "risk": round(risk, 2),
        "actions": actions,
        "time": datetime.now().strftime("%H:%M:%S")
    }