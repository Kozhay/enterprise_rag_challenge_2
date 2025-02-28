import json

with open('examples/subset.json', "r") as f:
    data = json.load(f)
    for company in data:
        file_name = company['sha1']
        company_name = company['company_name']
        major_industry = company['major_industry']