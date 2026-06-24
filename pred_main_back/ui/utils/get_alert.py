from collections import defaultdict, deque
import math

#saves alarm history and sum of alarms per engine for 5 cycles
history = defaultdict(lambda: deque(maxlen=5))
vote_sum = defaultdict(int)

#current alert state
alert_state = defaultdict(bool)

def update_alert(engine_id, is_anomaly):

    if is_anomaly is None or is_anomaly not in (0,1) or math.isnan(is_anomaly):
        raise ValueError("is_anomaly false value format")
    
    q = history[engine_id]

    #delete first entry, if history window full
    if len(q) == q.maxlen:
        vote_sum[engine_id] -= q[0]

    q.append(is_anomaly)
    vote_sum[engine_id] += is_anomaly

    #not enough in history yet, so standard = no alarm
    if len(q) < q.maxlen:
        return False
    
    anomalies = vote_sum[engine_id]

    #alarm on
    if not alert_state[engine_id]:
        if anomalies >= 3:
            alert_state[engine_id] = True

    #deactivate alert
    else:
        if anomalies == 0:
            alert_state[engine_id] = False
    
    return alert_state[engine_id]

def reset_state():
    history.clear()
    vote_sum.clear()
    alert_state.clear()