from collections import Counter
import json

with open('dataset.json') as f:
    data = json.load(f)

labels = [sample["website"] for sample in data]
print(Counter(labels))
