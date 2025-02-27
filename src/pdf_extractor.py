from pydantic import BaseModel
from typing import Optional
from enum import Enum
import pymupdf4llm
import tiktoken
import logging
import re
import json
import os
from litellm import completion

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Metric(str, Enum):
    rad_expenses = "research and development expenses"
    risk_management_spending = "risk management spending"
    return_on_assets = "Return on Assets (ROA)"
    customer_acquisition_spending = "customer acquisition spending"
    operating_margin = "operating margin"
    market_capitalization = "market capitalization"
    sustainability_initiatives_spending = "sustainability initiatives spending"
    gross_profit_margin = "gross profit margin"
    net_profit_margin = "net profit margin"
    total_liabilities = "total liabilities"
    total_assets = "total assets"
    intangible_assets = "intangible assets"
    marketing_spending = "marketing spending"
    free_cash_flow = "free cash flow"
    earnings_per_share = "earnings per share (EPS)"
    accounts_receivable = "accounts_receivable"
    acquisition_costs = "acquisition costs"
    shareholders_equity = "shareholders' equity"
    operating_cash_flow = "operating cash flow"
    quick_ratio = "Quick Ratio"
    net_income = "net income"
    inventory = "inventory"
    total_revenue = "total revenue"

class Currency(str, Enum):
    euro = "EUR"
    us_dollar = "USD"
    great_britain_pound = "GBP"
    australian_dollar = "AUD"
    other = "OTHER"

class Industry(str, Enum):
    technology = "Technology", 
    financial_services = "Financial Services", 
    healthcare = "Healthcare", 
    automotive = "Automotive",
    retail = "Retail", 
    energy_and_utilities = "Energy and Utilities", 
    hospitality = "Hospitality",
    telecommunications = "Telecommunications",
    media_entertainment = "Media & Entertainment", 
    pharmaceuticals = "Pharmaceuticals", 
    aerospace_defense = "Aerospace & Defense",
    transport_logistics = "Transport & Logistics",
    food_beverage = "Food & Beverage"

class DocumentDataPoint(BaseModel):
    metric_type: Metric
    value: float
    currency: Optional[Currency]
    point_in_time_as_iso_date: str
    src_pdf_page: int


class DocumentContent(BaseModel):
    data_points: list[DocumentDataPoint]


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

        # Format text with page number
        page_header = f"\n\n### src_pdf_page {page_number}\n{text}"
        print('src_pdf_page', page_number)
        page_header_length = count_tokens(page_header)

        if current_length + page_header_length > max_tokens:
            # Save current chunk and start a new one
            merged_chunks.append(current_chunk)
            current_chunk = {"pages": [], "text": "", "tables": []}
            current_length = 0

        # Add the new page with its number in the text
        current_chunk["pages"].append(page_number)
        current_chunk["text"] += page_header  # Append formatted text
        current_chunk["tables"].extend(tables)
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

    logging.info(f"🎯 Total merged chunks created: {len(merged_chunks)}")
    return merged_chunks





def extract_document_content(text):
    system_prompt = ("You are an assistant with the task of extracting precise information from long documents. "
                     "You will be prompted with the contents of a document. Your task is to extract various metrics "
#                     "as well as company role assignments "
                     "from this document. With each metric, supply the point in "
                     "time when the metric was measured according to the document,"
                     "as well as the currency (if applicable). "
                     "If the metric is an amount, extract the exact amount (e.g. "
                     "if the amount in the document is given as '100 (in thousands)' "
                     "or '100k', extract the value '100000')."
                     "on every page you can find src_pdf_page as int, extract it"
#                     "With each role assignment, supply when the role assignment started and ended, if possible."
                     "\n\n"
                     "Do your best to include as many metrics for as many points in time as possible!")                     
    
    

    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
      ]
    
    response = completion(
        model='gpt-4o-mini', #"ollama_chat/deepseek-r1:8b",
        messages=messages,
        response_format=DocumentContent,
        #api_base="https://ollama-euw1.bwt-chatbwt-l3ke.avossuite.dev/"
        )

    response_dict = json.loads(response.choices[0].message.content)
    return response_dict



 # Set tokenizer model (e.g., "gpt-4" or "gpt-3.5-turbo")
TOKENIZER = tiktoken.encoding_for_model("gpt-4o-mini")
name='0a61a353b1ea9fd9b8f63b60239634ca3007d58f'

pdf_path = f"examples/pdfs/{name}.pdf"

# Parse PDF
pdf_parsed_texts = parse_pdf(pdf_path, max_tokens=100_000)

# Extract structured data
structured_datas = []
for pdf_text in pdf_parsed_texts:
    extracted = extract_document_content(pdf_text['text'])
    structured_datas.append(extracted)

merged_data_points = []

# Iterate through structured_datas and merge the 'data_points'
for data in structured_datas:
    merged_data_points.extend(data['data_points'])

final_output = {
    'company_name': name,
    'data_points': merged_data_points
}

# Print the final output
print(final_output)

# Define the output folder
output_folder = "output"

# Ensure the output folder exists, create it if it doesn't
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Define the output file path with the company name as the filename
output_file_path = os.path.join(output_folder, f"{name}.json")

# Write final_output to the file in JSON format
with open(output_file_path, 'w') as json_file:
    json.dump(final_output, json_file, indent=4)

print(f"File saved to {output_file_path}")