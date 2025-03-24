Here's a suggested README.md for your repository:

```markdown:README.md
# Enterprise RAG Challenge Solution

This repository contains a solution for the Enterprise RAG (Retrieval-Augmented Generation) Challenge, which focuses on extracting and analyzing information from company financial reports and answering questions about them with proper source references.

## Overview

The system processes PDF documents through several stages:
1. PDF extraction and labeling
2. Question analysis and context retrieval 
3. Answer generation with source references

## Key Components

- `src/pdf_extractor.py` - Handles PDF parsing and initial data extraction
- `src/models.py` - Contains data models for different industry metrics and events
- `src/answer_questions.py` - Processes questions and generates answers with references
- `src/read_src_data.py` - Utility for reading source data files

## Features

- Industry-specific metric extraction (Financial Services, Technology, Healthcare, etc.)
- Event detection in financial reports
- Financial metric analysis
- Source page reference tracking
- Token usage monitoring
- Support for comparative questions across multiple companies

## Setup

1. Clone the repository
2. Set up the development container (requires Docker):
```bash
code .
# Open in container when prompted
```

Or install dependencies manually:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.devcontainer/.env`

## Usage

1. Place PDF files in `examples/pdfs/` directory

2. Run the PDF extraction and labeling:
```bash
python src/pdf_extractor.py
```

3. Process questions and generate answers:
```bash
python src/answer_questions.py
```

The system will generate:
- Labeled data in `output/labels/`
- Answers with references in `output/answers.json`
- Token usage statistics in `token_statistics.csv`

## Data Models

The system supports various industry-specific metrics including:
- Financial Services
- Technology
- Healthcare
- Automotive
- Retail
- Energy and Utilities
- And more...

Each industry has its own set of relevant metrics defined in `models.py`.

## Output Format

The answer output follows this structure:
```json
{
    "team_email": "example@domain.com",
    "submission_name": "submission_1",
    "answers": [
        {
            "question_text": "...",
            "kind": "number|name|boolean|names",
            "value": "answer_value",
            "references": [
                {
                    "page_index": 1,
                    "pdf_sha1": "..."
                }
            ]
        }
    ]
}
```README.md

## Token Usage Monitoring

The system tracks token usage across different stages:
- Labeling
- Filter labels
- Answer generation

Statistics are saved to `token_statistics.csv` for analysis.

## Development

The project uses a dev container configuration for consistent development environments. Required VS Code extensions are automatically installed when opening in the container.

## Requirements

- Python 3.12+
- Docker (for dev container)
- VS Code (recommended)

See `requirements.txt` for Python package dependencies.
```
