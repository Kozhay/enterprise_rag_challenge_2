import json

with open('output/answers.json', 'r') as f:
    data = json.load(f)
    print(len(data['answers']))