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

    The function looks at the last 5 cycles. If enough are "bad", it raises an
    ALERT. If already in ALERT, it needs enough "good" cycles to go back to OK.

    UPDATE: Thresholds now adapt to data maturity:
        - Cycles 1-5: Always OK (features too unstable)
        - Cycles 6-15: Stricter trigger (5/5), easier clear (2/5)
        - Cycles 16+: Standard trigger (4/5), standard clear (4/5)

    A cycle is "bad" if:
        - The average of its last 10 scores is negative AND there are 3+ consecutive negatives
        - OR there are 5+ consecutive negative scores
        - OR the score itself is very negative (< -0.02)
    """

    # ------------------------------------------------------------------
    # Step 1: If we have very little data, we cannot judge. Stay OK.
    # UPDATE: Reduced from 10 to 5 cycles.
    # Reason: Rolling features are only truly unstable for cycles 1-4.
    # After cycle 5 we can start judging with stricter thresholds.
    # ------------------------------------------------------------------
    n = len(scores_history)
    if n <= 5:
        return "OK"

    # ------------------------------------------------------------------
    # Step 2: Convert the list of scores into a NumPy array for easy math.
    # ------------------------------------------------------------------
    scores = np.array(scores_history)

    # ------------------------------------------------------------------
    # Step 3: Set thresholds based on how much data we have.
    # UPDATE: Confidence-based thresholds.
    # Old code: Always used trigger=5, clear=3.
    # Problem: With few cycles, the alert could get stuck because
    # clearing required 3 good cycles – too strict early on.
    # Fix: Early on (cycles 6-15), keep trigger strict (5/5) but make
    # clearing easier (2/5). After cycle 16, use standard 4/4.
    # ------------------------------------------------------------------
    if n <= 15:
        trigger_bad_needed = 5   # All 5 cycles must be bad to trigger
        clear_good_needed  = 2   # Only 2 good cycles to clear (avoid stuck alert)
    else:
        trigger_bad_needed = 4   # 4 out of 5 bad to trigger
        clear_good_needed  = 4   # 4 out of 5 good to clear

    # ------------------------------------------------------------------
    # Step 4: Count how many of the last 5 cycles are "bad" or "good".
    # ------------------------------------------------------------------
    bad_count = 0
    good_count = 0

    # Look at each of the last 5 cycles
    for i in range(max(5, n - 5), n):

        # ------------------------------------------------------------------
        # 4a. Average of the last 10 cycles (including this one).
        # UPDATE: Early cycle handling.
        # Old code: Always used scores[i-9:i+1].
        # Problem: For cycles 6-9, this gave wrong indices (e.g. scores[-4:7]).
        # Fix: Use all available data when fewer than 10 cycles exist.
        # ------------------------------------------------------------------
        if i < 10:
            avg_score = np.mean(scores[:i+1])      # All data so far
        else:
            avg_score = np.mean(scores[i-9:i+1])    # Last 10 cycles

        # ------------------------------------------------------------------
        # 4b. Count consecutive negative scores backwards from this cycle
        # ------------------------------------------------------------------
        consecutive_negatives = 0
        for j in range(i, -1, -1):   # go backwards from i to 0
            if scores[j] < 0:
                consecutive_negatives += 1
            else:
                break   # stop as soon as we hit a positive score

        # ------------------------------------------------------------------
        # 4c. Decide if this single cycle is "bad".
        # UPDATE: Stricter definition.
        # Old code: avg<0 OR cons>=3 OR score<-0.003
        # Problem: A single slightly negative score or a barely negative
        # average without persistence triggered false alerts.
        # Fix: Require BOTH negative trend AND persistence. Also raised
        # single-score threshold from -0.003 to -0.02.
        # ------------------------------------------------------------------
        is_bad = (
            (avg_score < 0.0 and consecutive_negatives >= 3) or   # Trend AND persistence
            consecutive_negatives >= 5 or                         # Strong persistence alone
            scores[i] < -0.02                                     # Clearly negative score
        )

        # ------------------------------------------------------------------
        # 4d. Update counters
        # ------------------------------------------------------------------
        if is_bad:
            bad_count += 1
        else:
            good_count += 1

    # ------------------------------------------------------------------
    # Step 5: Make the final decision, depending on current alert state.
    # Uses the adaptive thresholds from Step 3.
    # ------------------------------------------------------------------
    if current_alert == "OK":
        # We are currently OK. Need enough bad cycles to trigger alert.
        if bad_count >= trigger_bad_needed:
            return "ALERT"
        else:
            return "OK"

    elif current_alert == "ALERT":
        # We are already in ALERT. Need enough good cycles to clear it.
        # Early on (cycles 6-15): only 2 good needed (easy to clear).
        # Mature (cycles 16+): 4 good needed (confident recovery).
        if good_count >= clear_good_needed:
            return "OK"
        else:
            return "ALERT"

    # Fallback (should never reach here)
    return "OK"