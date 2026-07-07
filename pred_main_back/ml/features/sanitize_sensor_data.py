import math

def sanitize_sensors(sensors):
    cleaned = {}

    #replace None, non-float, NaN values with 0.0 to avoid issues during ML inference
    #also prints a message to the console for each replacement to inform the user
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