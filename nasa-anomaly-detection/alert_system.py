"""
alert_system.py

This file contains the function that decides if an engine is OK or ALERT.
It uses only the anomaly scores (no RUL needed).

How to use in your code:

    from alert_system import get_alert_level

    # scores_history is a list of anomaly scores from oldest to newest
    # current_alert is "OK" or "ALERT" (what the engine is right now)
    new_alert = get_alert_level(scores_history, current_alert="OK")
"""

import numpy as np


def get_alert_level(scores_history, current_alert="OK"):
    """
    Decide the alert level (OK or ALERT) from recent anomaly scores.

    The function looks at the last 5 cycles. If all 5 are "bad", it raises an
    ALERT. If already in ALERT, it needs 3 out of 5 "good" cycles to go back to OK.

    A cycle is "bad" if:
        - The average of its last 10 scores is negative (trend is down)
        - OR there are 3 or more consecutive negative scores (persistent)
        - OR the score itself is below -0.003 (slightly abnormal)
    """

    # ------------------------------------------------------------------
    # Step 1: If we have very little data, we cannot judge. Stay OK.
    # ------------------------------------------------------------------
    if len(scores_history) <= 10:
        return "OK"

    # ------------------------------------------------------------------
    # Step 2: Convert the list of scores into a NumPy array for easy math.
    # ------------------------------------------------------------------
    scores = np.array(scores_history)

    # ------------------------------------------------------------------
    # Step 3: Count how many of the last 5 cycles are "bad" or "good".
    # ------------------------------------------------------------------
    bad_count = 0
    good_count = 0

    # Look at each of the last 5 cycles
    for i in range(len(scores) - 5, len(scores)):

        # ------------------------------------------------------------------
        # 3a. Average of the last 10 cycles (including this one)
        # ------------------------------------------------------------------
        avg_of_last_10 = np.mean(scores[i-9:i+1])

        # ------------------------------------------------------------------
        # 3b. Count consecutive negative scores backwards from this cycle
        # ------------------------------------------------------------------
        consecutive_negatives = 0
        for j in range(i, -1, -1):   # go backwards from i to 0
            if scores[j] < 0:
                consecutive_negatives += 1
            else:
                break   # stop as soon as we hit a positive score

        # ------------------------------------------------------------------
        # 3c. Decide if this single cycle is "bad"
        # ------------------------------------------------------------------
        is_bad = (
            avg_of_last_10 < 0.0          # overall trend is negative
            or consecutive_negatives >= 3 # many negatives in a row
            or scores[i] < -0.003         # score itself is slightly below zero
        )

        # ------------------------------------------------------------------
        # 3d. Update counters
        # ------------------------------------------------------------------
        if is_bad:
            bad_count += 1
        else:
            good_count += 1

    # ------------------------------------------------------------------
    # Step 4: Make the final decision, depending on current alert state.
    # ------------------------------------------------------------------
    if current_alert == "OK":
        # We are currently OK. We need all 5 of the last 5 cycles to be bad
        # before we warn the engineer.
        if bad_count >= 5:
            return "ALERT"
        else:
            return "OK"

    elif current_alert == "ALERT":
        # We are already in ALERT. We need at least 3 good cycles out of the
        # last 5 to be sure the engine is healthy again.
        if good_count >= 3:
            return "OK"
        else:
            return "ALERT"

    # Fallback (should never reach here)
    return "OK"