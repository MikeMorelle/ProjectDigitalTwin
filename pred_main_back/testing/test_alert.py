from ui.utils.get_alert import *
import pytest
import numpy as np

#this is just an exercise to train pytest for Advanced Testing Methods exam

def alert_on_3_of_5():
    reset_state()

    values = [1,1,1,0,0]

    result = None

    for v in values:
        result = update_alert("e", v)

    assert result is True

def no_alert_at_2_of_5():
    reset_state()

    values = [1,1,0,0,0]

    result = None

    for v in values:
        result = update_alert("e", v)

    assert result is False

def alert_remains():
    reset_state()

    for v in [1,1,1,0,0]:
        update_alert("e", v)
    
    assert alert_state["e"] is True

    #one remaining anomaly
    for _ in range(2):
        update_alert("e", 0)


    assert alert_state["e"] is True

def alert_reset():
    reset_state()

    for v in [1,1,1,0,0]:
        update_alert("e", v)

    for _ in range(5):
        update_alert("e", 0)
    
    assert alert_state["e"] is False

def alert_for_window_size():
    reset_state()

    #6 entries, but only last 5 should get counted
    values = [1,1,1,0,0,0]

    for v in values: 
        update_alert("e",v)

    assert vote_sum["e"] == 2

def alert_for_isolated_engines():
    reset_state()

    for v in [1,1,1,0,0]:
        update_alert("e1", v)
    
    for v in [0,0,0,0,0]:
        update_alert("e2", v)

    assert alert_state["e1"] is True
    assert alert_state["e2"] is False

def invalid_values_rejected():
    reset_state()

    with pytest.raises(ValueError):
        update_alert("e", np.nan)
    
    with pytest.raises(ValueError):
        update_alert("e", "1")