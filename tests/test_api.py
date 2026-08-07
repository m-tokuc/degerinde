"""
Değerinde API — integration tests (TestClient).
Requires: local Postgres with araclar + predictions, car_price_model.pkl
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

# Import app after env is available
from main import app, is_model_loaded

client = TestClient(app)

FULL_PAYLOAD = {
    "Kilometre": 120000,
    "Yil": 2018,
    "Marka": "Renault",
    "Seri": "Clio",
    "Model": "1.5 dCi Expression",
    "Yakit_Tipi": "Dizel",
    "Vites_Tipi": "Manuel",
    "Kasa_Tipi": "Hatchback/3",
    "Cekis": "Önden Çekiş",
    "Renk": "Beyaz",
    "Kimden": "Galeriden",
    "Garanti_Durumu": "Garantisi Yok",
    "Silindir_Sayisi": "4",
    "Koltuk_Sayisi": "5",
    "Motor_Hacmi_cc": 1461,
    "Motor_Gucu_hp": 90,
    "Tramer_TL": 0,
    "Boya_Degisen": "Belirsiz",
}


def test_health_check():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"]
    assert "model_loaded" in body
    assert body.get("version")
    assert "startup_validation" in body


@pytest.mark.skipif(not is_model_loaded, reason="ML model not loaded")
def test_predict_endpoint():
    req_id = f"pytest-{uuid.uuid4()}"
    payload = {**FULL_PAYLOAD, "request_id": req_id}
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    price = body["predicted_price"]
    assert isinstance(price, (int, float))
    assert price > 0
    assert body.get("currency") == "TRY"
    assert body.get("features_used") >= 18
    assert "confidence_low" in body and "confidence_high" in body
    assert body["confidence_low"] <= price <= body["confidence_high"]
    assert body.get("request_id") == req_id


@pytest.mark.skipif(not is_model_loaded, reason="ML model not loaded")
def test_history_endpoint():
    req_id = f"pytest-hist-{uuid.uuid4()}"
    payload = {**FULL_PAYLOAD, "request_id": req_id}
    pred = client.post("/api/predict", json=payload)
    assert pred.status_code == 200

    r = client.get("/api/predictions/history", params={"limit": 50})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    assert isinstance(body["data"], list)
    assert body["total"] >= 1
    ids = {row.get("request_id") for row in body["data"]}
    assert req_id in ids, f"Expected {req_id} in history; got {ids}"


def test_dynamic_options_basic():
    r = client.post("/api/dynamic_options", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["total_matches"] > 0
    assert isinstance(body["Marka"], list)
    assert len(body["Marka"]) >= 1
