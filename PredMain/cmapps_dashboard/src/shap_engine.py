import shap
import numpy as np
import pandas as pd

class ShapEngine:

    def __init__(self, model):
        """Initialize the SHAP engine with a trained model."""
        self.explainer = shap.TreeExplainer(model)

    def explain(self, X_live):
        """Generate SHAP values for the latest sensor data and return the top features."""
        shap_values = self.explainer.shap_values(X_live)
        top = pd.Series(np.abs(shap_values[0]), index=X_live.columns).sort_values(ascending=False).head(10)
        return top