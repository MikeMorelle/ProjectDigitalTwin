import traceback
import sys

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

            except:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                raise

        return result
    
    def reset(self):
        for m in self.models:
            m.clear()