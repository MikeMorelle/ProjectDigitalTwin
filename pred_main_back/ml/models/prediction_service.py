class PredictionService:
    def __init__(self, models):
        self.models = models

    def predict(self, engine, dataset_num):
        result = {}
        for m in self.models:
            try:
                prediction = m.predict(engine, dataset_num)

                if prediction: 
                    result.update(prediction)

            except Exception as e:
                print(f"{m.__class__.__name__} failed: {e}")
            
        return result
    
    def reset(self):
        for m in self.models:
            m.clear()