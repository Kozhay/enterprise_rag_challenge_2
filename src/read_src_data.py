import json

with open('examples/subset.json', "r") as f:
    data = json.load(f)
    output_data = []
    for company in data:
        file_name = company['sha1']
        company_name = company['company_name']
        output_data.append({"file_name": file_name, "company_name": company_name})
    
    # Write the output data to a JSON file
    with open('output/company_mapping.json', 'w', encoding='utf-8') as output_file:
        json.dump(output_data, output_file, ensure_ascii=False, indent=4)