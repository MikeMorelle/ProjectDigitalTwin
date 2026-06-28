def apply_faulty_sensors(engine_id, sensors, fault_config):
    if not fault_config:
        return sensors
    
    eid = str(engine_id)

    if eid not in fault_config:
        return sensors
    
    cfg = fault_config[eid]

    new_sensors = sensors.copy()

    for sensor, rule in cfg.items():
        if sensor not in new_sensors:
            continue

        if rule["type"] == "offset":
            new_sensors[sensor] += rule["value"]
            print(f"BEFORE: {sensors[sensor]} | AFTER BIAS: {new_sensors[sensor]}", flush=True)

        if rule["type"] == "nan":
            new_sensors[sensor] = float("nan")
            print(f"BEFORE: {sensors[sensor]} | AFTER BIAS: {new_sensors[sensor]}", flush=True)

    return new_sensors