import pymupdf4llm
import logging_config


def parse_pdf(pdf_path, pages=None, max_tokens=500):
    """Extracts, formats, and merges text from a PDF while preserving page numbers."""
    logging_config.info(f"📄 Starting PDF processing: {pdf_path}")

    page_chunks = pymupdf4llm.to_markdown(pdf_path, pages=pages, page_chunks=True)
    
    # Merge pages while keeping page numbers inside the text
    merged_chunks = merge_chunks_with_pages(page_chunks, max_tokens)

    logging_config.info(f"🎯 Total merged chunks created: {len(merged_chunks)}")
    return merged_chunks