import joblib
model = joblib.load("car_price_model.pkl")
if hasattr(model, 'feature_names_in_'):
    print(model.feature_names_in_)
elif hasattr(model, 'get_booster'):
    print(model.get_booster().feature_names)
else:
    print("Cannot find feature names directly.")
