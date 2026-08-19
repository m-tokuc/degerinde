import requests
res = requests.post("http://0.0.0.0:8000/api/dynamic_options", json={"Yil": ""})
print(res.status_code, res.text)
