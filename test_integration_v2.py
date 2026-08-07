"""
Değerinde — Integration & Load Test for v2 API
Verifies valid requests, OOD handling, and PostgreSQL audit logging.
"""

import time
from fastapi.testclient import TestClient
from sqlalchemy import text
from main import app
from app_db import get_db

client = TestClient(app)

def test_valid_vehicle_prediction():
    print("--- Test 1: Valid Vehicle Prediction ---")
    payload = {
        "brand": "Renault",
        "model": "Clio",
        "trim": "1.5 dCi Touch",
        "year": 2021,
        "km": 60000,
        "fuel_type": "Dizel",
        "gear_type": "Yarı Otomatik",
        "body_type": "Hatchback",
        "color": "Beyaz",
        "tramer_tl": 5000,
        "boya_durumu": "Boyalı"
    }

    response = client.post("/api/v2/predict_v2", json=payload)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] is True
    assert "prediction" in data
    assert "explanation" in data
    assert "request_id" in data
    
    # Check SHAP dictionary structure
    exp = data["explanation"]
    assert "base_price" in exp
    assert "brand_model_impact" in exp
    assert "final_price" in exp
    
    # Check UI Formatter structure
    assert "ui_formatted" in data
    ui_data = data["ui_formatted"]
    assert "formatted_price" in ui_data
    assert "price_range" in ui_data
    assert "min" in ui_data["price_range"]
    assert "value_adders" in ui_data
    assert "value_reducers" in ui_data
    assert isinstance(ui_data["value_adders"], list)
    
    print(f"✅ Prediction Successful: {data['prediction']} TL")
    print(f"   Formatted UI Price: {ui_data['formatted_price']}")
    print(f"   Recommended Range: {ui_data['price_range']['formatted_min']} - {ui_data['price_range']['formatted_max']}")
    print(f"   Top Value Adder: {ui_data['value_adders'][0]['label'] if ui_data['value_adders'] else 'None'} ({ui_data['value_adders'][0]['display_value'] if ui_data['value_adders'] else 'None'})")
    print(f"   Request ID: {data['request_id']}")
    return data["request_id"]

def test_ood_handling():
    print("\\n--- Test 2: Out-of-Distribution (OOD) Handling ---")
    payload = {
        "brand": "BilinmeyenMarka",
        "model": "ModelX",
        "trim": "1.0",
        "year": 2021,
        "km": 60000
    }

    response = client.post("/api/v2/predict_v2", json=payload)
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    data = response.json()
    assert "BilinmeyenMarka" in data["detail"]
    print(f"✅ OOD Handling Successful: {data['detail']}")

def test_database_audit_check(request_id):
    print("\\n--- Test 3: Database Audit Check ---")
    
    # Background tasks might take a fraction of a second, so let's sleep briefly
    time.sleep(1)
    
    db = next(get_db())
    try:
        # Check if the row exists in predictions table
        query = text("SELECT request_id, predicted_price, shap_explanation FROM predictions WHERE request_id = :req_id")
        result = db.execute(query, {"req_id": request_id}).fetchone()
        
        assert result is not None, f"Request ID {request_id} not found in DB!"
        
        db_req_id, db_price, db_shap = result
        print(f"✅ Log found in DB! Request ID: {db_req_id}")
        print(f"   Logged Price: {db_price}")
        
        assert db_shap is not None, "SHAP explanation was not saved as JSON!"
        assert "base_price" in db_shap, "SHAP JSON does not contain base_price!"
        
        print(f"✅ SHAP Explanation Logged: {list(db_shap.keys())}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting Integration Tests for /api/v2/predict_v2...")
    req_id = test_valid_vehicle_prediction()
    test_ood_handling()
    test_database_audit_check(req_id)
    print("\\n🎉 All tests passed successfully!")
