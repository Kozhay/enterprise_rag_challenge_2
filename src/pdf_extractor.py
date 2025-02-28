
import pymupdf4llm
import tiktoken
import logging
import re
import json
import os
from litellm import completion
import models

from pydantic import BaseModel, field_validator
from typing import Optional, Union, Literal
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def count_tokens(text):
    """Counts the number of tokens in a given text."""
    return len(TOKENIZER.encode(text))

def merge_chunks_with_pages(page_chunks, max_tokens=500):
    """Merges pages into large chunks while embedding page numbers in text."""
    merged_chunks = []
    current_chunk = {"pages": [], "text": "", "tables": []}
    current_length = 0

    for chunk in page_chunks:
        page_number = chunk['metadata']['page']
        text = chunk['text'] or ""
        tables = chunk['tables'] or []
        chunk_length = count_tokens(text)

        
        
        page_header = f"\n\n### pdf_page {page_number}\n{text}\n###data_table {tables}"
        page_header_length = count_tokens(page_header)

        if current_length + page_header_length > max_tokens:
            # Save current chunk and start a new one
            merged_chunks.append(current_chunk)
            current_chunk = {"pages": [], "text": ""}
            current_length = 0

        # Add the new page with its number and tables in the text
        current_chunk["pages"].append(page_number)
        current_chunk["text"] += page_header
        current_length += page_header_length

    # Append the last chunk
    if current_chunk["pages"]:
        merged_chunks.append(current_chunk)

    return merged_chunks
    

def parse_pdf(pdf_path, pages=None, max_tokens=500):
    """Extracts, formats, and merges text from a PDF while preserving page numbers."""
    logging.info(f"📄 Starting PDF processing: {pdf_path}")

    page_chunks = pymupdf4llm.to_markdown(pdf_path, pages=pages, page_chunks=True)
    
    # Merge pages while keeping page numbers inside the text
    merged_chunks = merge_chunks_with_pages(page_chunks, max_tokens)
    print(merged_chunks)

    logging.info(f"🎯 Total merged chunks created: {len(merged_chunks)}")
    return merged_chunks





import json

def extract_document_content(text, industry_type='financial_services'):
    system_prompt = f"""
        You are an assistant with access to a long document and a list of searchable items.
        You are analyzing a document from the {industry_type} industry.
        There are two types of searchable information:
        - Metrics related to the industry.
        - Events that occurred during the year.
        Your task is to identify the relevant pages for each category:
        - metrics_src_pdf_page for metrics-related information.
        - events_src_pdf_page for event-related information.
        Each item may correspond to multiple pages, and pages may be duplicated across different items.
        If uncertain, err on the side of inclusion rather than exclusion.
        You will receive a $100 bonus for accurately completing your task.
        """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    
    industry_to_metrics = {
            "Financial Services": models.FinancialServicesMetrics,
            "Technology": models.TechnologyMetrics,
            "Healthcare": models.HealthcareMetrics,
            "Automotive": models.AutomotiveMetrics,
            "Retail": models.RetailMetrics,
            "Energy and Utilities": models.EnergyAndUtilitiesMetrics,
            "Hospitality": models.HospitalityMetrics,
            "Telecommunications": models.TelecommunicationsMetrics,
            "Media & Entertainment": models.MediaAndEntertainmentMetrics,
            "Pharmaceuticals": models.PharmaceuticalsMetrics,
            "Aerospace & Defense": models.AerospaceAndDefenseMetrics,
            "Transport & Logistics": models.TransportAndLogisticsMetrics,
            "Food & Beverage": models.FoodAndBeverageMetrics
        }
    
    datamodel = industry_to_metrics[industry_type]
    logging.info(f"Will search according to {industry_type} and model {datamodel}")
    class DocumentDataPoint(BaseModel):
        company_name: str
        industry: str
        metric_type: datamodel
        metric_src_pdf_page: list[int]


    class DocumentContent(BaseModel):
        data_points: list[DocumentDataPoint]
        events: list[models.AnnualEvents]
    
    
    response = completion(
        model='gpt-4o-mini',  #groq/llama-3.3-70b-versatile
        messages=messages,
        response_format=DocumentContent
    )

    # Extract token usage details
    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens
    #cached_tokens = usage.prompt_tokens_details.cached_tokens  # Extract cached tokens

    logging.info(f"🔹 Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")

    # Parse response content
    response_dict = json.loads(response.choices[0].message.content)
    return response_dict

    # return {
    #     "data": response_dict,
    #     "token_usage": {
    #         "prompt_tokens": prompt_tokens,
    #         "completion_tokens": completion_tokens,
    #         "total_tokens": total_tokens,
    #         "cached_tokens": cached_tokens  # Include cached tokens in return
    #     }
    # }




 # Set tokenizer model (e.g., "gpt-4" or "gpt-3.5-turbo")
TOKENIZER = tiktoken.encoding_for_model("gpt-4o-mini")
file_name='0279901b645e568591ad95dac2c2bf939ef0c00d'
company_name = "ACRES Commercial Realty Corp"
major_industry = "Financial Services"



pdf_path = f"examples/pdfs/{file_name}.pdf"

# Parse PDF
# Generate list of pages to parse from 14 to 15
pages_to_parse = list(range(0, 5))  # End number is exclusive

pdf_parsed_texts = parse_pdf(pdf_path, pages=pages_to_parse, max_tokens=100_000)

# Extract structured data
structured_datas = []
for pdf_text in pdf_parsed_texts:
    pass
    extracted = extract_document_content(pdf_text['text'], industry_type=major_industry)
    structured_datas.append(extracted)

merged_data_points = []
merged_events = []

# Iterate through structured_datas and merge the 'data_points'
for data in structured_datas:
    merged_data_points.extend(data['data_points'])
    merged_events.extend(data['events'])

final_output = {
    'company_name': file_name,
    'data_points': merged_data_points,
    'events': merged_events
}

# Print the final output
print(final_output)

# Define the output folder
output_folder = "output/labels"

# Ensure the output folder exists, create it if it doesn't
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Define the output file path with the company name as the filename
output_file_path = os.path.join(output_folder, f"{file_name}.json")

# Write final_output to the file in JSON format
with open(output_file_path, 'w') as json_file:
    json.dump(final_output, json_file, indent=4)

print(f"File saved to {output_file_path}")