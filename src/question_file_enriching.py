import json

# # Read JSON data from files
# with open("output/company_mapping.json", "r") as f:
#     companies = json.load(f)

# with open("examples/questions.json", "r") as f:
#     questions = json.load(f)

# # Create a mapping of company names to file names
# company_file_map = {company["company_name"]: company["file_name"] for company in companies}

# # Process questions and add file_name
# for question in questions:
#     company_name = next((name for name in company_file_map.keys() if name in question["text"]), None)
#     if company_name:
#         question["file_name"] = company_file_map[company_name]
#     else:
#         question["file_name"] = None  # If no matching company found

# # Save the modified questions JSON back to file
# with open("updated_questions.json", "w") as f:
#     json.dump(questions, f, indent=2)

# print("Updated questions saved to updated_questions.json")


import json
from collections import Counter

# Load JSON data from a file
with open('updated_questions.json', 'r') as file:
    data = json.load(file)

# Extract file names
file_names = [entry["file_name"] for entry in data]

# Count occurrences of each unique file name
file_name_counts = Counter(file_names)

print(file_name_counts)