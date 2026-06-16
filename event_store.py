event_history = []

# -------------------------
# SAVE EVENT
# -------------------------
def save_event(event):

    event_history.append(event)

    # keep latest 100 events only
    if len(event_history) > 100:
        event_history.pop(0)

# -------------------------
# GET EVENTS
# -------------------------
def get_events():
    return event_history