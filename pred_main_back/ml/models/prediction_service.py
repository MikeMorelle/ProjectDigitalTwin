import traceback
import sys

#prediction service that takes a list of models and calls their predict method for each engine in the dataset -> easily scalable
class PredictionService:
    def __init__(self, models):
        self.models = models

    def predict(self, engine, dataset_num):
        result = {}
        for m in self.models:
            try:
                #call the predict method of each model and update the result dictionary with the prediction
                prediction = m.predict(engine, dataset_num)

                if prediction: 
                    result.update(prediction)

            except:
                #more detailed error logging for debugging, otherwise only the last exception is printed -> big issue during dev
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                raise

        return result
    
    #reset the state of all models -> used when starting a new run to avoid contamination from previous runs
    def reset(self):
        for m in self.models:
            m.clear()