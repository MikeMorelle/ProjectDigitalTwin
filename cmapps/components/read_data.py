import pandas as pd

def prepare():
    df = pd.read_csv("data/train_FD001.txt", sep=r"\s+", header=None)
    df.columns = (
    ['unit_num', 'cycle']
    + [f'op_setting{i}' for i in range(1,4)]
    + [f'sensor{i}' for i in range(1,22)]
    )
    return df

def prepare_all():
    index_names = ['unit_num', 'time_cycles']
    setting_names = ['setting1', 'setting2', 'setting3']
    sensor_names = ['sensor{}'.format(i) for i in range(1, 22)]
    col_names = index_names + setting_names + sensor_names

    train = pd.read_csv('data/train_FD001.txt', sep=r'\s+', header=None, names=col_names)
    test = pd.read_csv('data/test_FD001.txt', sep=r'\s+', header=None, names=col_names)
    y_test = pd.read_csv('data/RUL_FD001.txt', sep=r'\s+', header=None, names=["RUL"])

    na = train.isna().empty
    ne = test.isna().empty
    ny = y_test.isna().empty

    if na:
        train = train.fillna(method="ffill")
        print("Filled missing data in train")
    elif ne:
        test = test.fillna(method="ffill")
        print("Filled missing data in test")
    elif ny:
        y_test = y_test.fillna(method="ffill")
        print("Filled missing data in test")
    else:
        print("No missing data. Continue")

    return train, test, y_test
