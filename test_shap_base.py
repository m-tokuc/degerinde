import joblib
from explainability import PriceExplainer

exp = PriceExplainer()
print("Expected Value (Global Mean):", exp.explainer.expected_value)
