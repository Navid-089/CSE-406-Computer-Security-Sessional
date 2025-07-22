import json, requests

with open("dataset.json") as f:
    d = json.load(f)

r = requests.post("http://localhost:5000/predict", json={"trace": d[0]["trace_data"]})
print(r.json())