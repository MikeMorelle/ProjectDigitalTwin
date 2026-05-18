from collections import defaultdict

class DataStore:
    def __init__(self):
        self.data = defaultdict(list)

    def add(self, values):
        sensor = values["sensor"]
        self.data[sensor].append(values)

store = DataStore()