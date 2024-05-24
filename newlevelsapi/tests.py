import json

with open('06-jobs-api.products.json') as f:
    data = json.load(f)

    for item in data:
        
        print(item)
