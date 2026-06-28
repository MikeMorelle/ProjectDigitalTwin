import math

def sanitize_sensors(sensors):
    cleaned = {}

    for k,v in sensors.items():
        if v is None:
            print(f"Changed None value to 0.0", flush=True)
            cleaned[k] = 0.0

        if isinstance(v,float) and math.isnan(v):
            print(f"Replacing {k} NaN with 0", flush=True)
            cleaned[k] = 0.0
        else:
            cleaned[k] = v
    return cleaned