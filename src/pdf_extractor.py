pdf_path = "examples/pdfs/0a9e39e1d2e176f3a766a0e86af82772f1654a6e.pdf"
OPENAI_MODEL = "gpt-4o-mini"

import pdfplumber
import json
import pandas as pd

def extract_text_with_coordinates(pdf_path):
    document_structure = []
    
    page_limit = 11  # Debug: only process first 3 pages
    with pdfplumber.open(pdf_path) as pdf:
        
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()
            print(f"Processing page {page_num}")
            
            document_structure.append(page.extract_text())
        
    full_text = "\n".join(document_structure)
    return split_rec(full_text)


def split_rec(full_text):
    import tiktoken
    # Initialize tiktoken encoding for the specified model
    encoding = tiktoken.encoding_for_model(OPENAI_MODEL)    
    # Count the number of tokens in the extracted text
    num_tokens = len(encoding.encode(full_text))
    
    # Check if the number of tokens exceeds the limit (128K)
    # or the number of characters 
    if num_tokens <= 100000 and len(full_text) <= 900000:
        return [full_text]
        
    print("splitting")
    # Split the text into two roughly equal parts
    mid_point = len(full_text) // 2
    
    # Recursively split both halves and combine results
    return split_rec(full_text[:mid_point]) + split_rec(full_text[mid_point:])



extract_text_with_coordinates(pdf_path)