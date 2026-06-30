#https://medium.com/@mihaitimoficiuc/predicting-jet-engine-failures-with-nasas-c-mapss-dataset-and-lstm-a-practical-guide-to-85b9513ea9ed

UNSCHEDULED_MAINTENANCE_COST = 5000 #emergency repair
SCHEDULED_MAINTENANCE_COST = 1000 #planned
THRESHOLD = 50 

def calc_predictive_costs(actual_rul_list, predicted_rul_list, threshold=THRESHOLD):
    total_cost = 0
    scheduled = 0
    unscheduled = 0

    for actual, predicted in zip(actual_rul_list, predicted_rul_list):
        if predicted < threshold:
            total_cost += SCHEDULED_MAINTENANCE_COST
            scheduled +=1
        else:
            if actual < threshold:
                total_cost += UNSCHEDULED_MAINTENANCE_COST
                unscheduled += 1

    return total_cost, scheduled, unscheduled
