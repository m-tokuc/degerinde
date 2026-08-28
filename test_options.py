import json
from fastapi.testclient import TestClient
from main import app

with TestClient(app) as client:
    req = {"Marka": "Toyota"}
    response = client.post("/api/dynamic_options", json=req)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
