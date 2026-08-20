import requests
res = requests.post("http://0.0.0.0:8000/api/admin/reload-model")
print(res.status_code, res.text)
