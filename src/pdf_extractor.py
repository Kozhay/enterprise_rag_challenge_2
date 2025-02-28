from pydantic import BaseModel
from typing import Optional, Union, Literal
from enum import Enum
import pymupdf4llm
import tiktoken
import logging
import re
import json
import os
from litellm import completion
import litellm
from pydantic import validator


#litellm._turn_on_debug()
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class IndustryMetrics:
    """Base class for industry-specific metrics"""
    pass

class FinancialServicesMetrics(IndustryMetrics, str, Enum):
    """Metrics specific to the financial services industry"""
    total_assets = "Total assets on balance sheet at year-end"
    total_deposits = "Total deposits at year-end"
    loans_outstanding = "Loans outstanding at year-end"
    assets_under_management = "Assets under management (AUM)"
    non_performing_loan_ratio = "Non-performing loan ratio (NPL) at year-end"
    tier1_capital_ratio = "Tier 1 capital ratio at year-end"
    customer_accounts = "Number of customer accounts at year-end"
    branch_count = "Branch count at year-end"
    net_interest_margin = "End-of-year net interest margin (NIM)"
    return_on_equity = "Return on equity (ROE) at year-end"

class TechnologyMetrics(IndustryMetrics, str, Enum):
    """Metrics specific to the technology industry"""
    r_and_d_spending = "Research and Development spending"
    patent_count = "Number of patents"
    software_revenue = "Software revenue"
    # ... other tech metrics ...

class HealthcareMetrics(IndustryMetrics, str, Enum):
    """Metrics specific to the healthcare industry"""
    patient_count = "Number of patients"
    bed_capacity = "Hospital bed capacity"
    clinical_trials = "Number of clinical trials"
    # ... other healthcare metrics ...

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


class DocumentDataPoint(BaseModel):
    industry: Literal["financial_services", "technology", "healthcare"]  # Add more industries as needed
    metric_type: Union[
        FinancialServicesMetrics,
        TechnologyMetrics,
        HealthcareMetrics,
        Metric  # Keep the general metrics as fallback
    ]
    src_pdf_page: list[int]

    # Validate that metrics match the industry
    @validator('metric_type')
    def validate_metric_type(cls, v, values):
        industry_to_metrics = {
            "financial_services": FinancialServicesMetrics,
            "technology": TechnologyMetrics,
            "healthcare": HealthcareMetrics
        }
        
        if 'industry' in values:
            expected_metric_class = industry_to_metrics.get(values['industry'])
            if expected_metric_class and not isinstance(v, (expected_metric_class, Metric)):
                raise ValueError(f"Metric type must be from {expected_metric_class.__name__} for {values['industry']} industry")
        return v


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





import json

def extract_document_content(text, industry_type='financial_services'):
    system_prompt = f"""
        You are an assistant with access to a long document and a list of searchable items.
        You are analyzing a document from the {industry_type} industry.
        Your task is to identify the relevant pages in the document that potentially contain answers to the given queries (src_pdf_page).
        Each item may correspond to multiple pages, and pages may be duplicated across different items.
        If uncertain, err on the side of inclusion rather than exclusion.
        You will receive a $100 bonus for accurately completing your task.
        """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    response = completion(
        model='groq/llama-3.3-70b-versatile', #'gpt-4o-mini',
        messages=messages,
        response_format=DocumentContent,
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
name='0279901b645e568591ad95dac2c2bf939ef0c00d' #0279901b645e568591ad95dac2c2bf939ef0c00d ACRES Commercial Realty Corp. Financial Services

pdf_path = f"examples/pdfs/{name}.pdf"

# Parse PDF
# Generate list of pages to parse from 14 to 15
pages_to_parse = list(range(0, 11))  # End number is exclusive

pdf_parsed_texts = parse_pdf(pdf_path, pages_to_parse, max_tokens=100_000)

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