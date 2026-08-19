import requests
payload = {"Marka": "Renault"}
res = requests.post("http://0.0.0.0:8000/api/dynamic_options", json=payload)
print(res.status_code, res.text)
