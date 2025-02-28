import tiktoken
import logging
import json
from litellm import completion
import csv
from datetime import datetime
from pdf_extractor import parse_pdf
from pydantic import BaseModel, Field
from typing import Union, Literal, List


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_pdf_pages_for_answer(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data



def check_labels(question, labels, file_name):
    system_prompt = f"""
        #ROLE: InvestGuru: Expert in Analyzing Public Company Reports
        You are InvestGuru, a financial expert specializing in analyzing and answering questions based on public company reports.
        Your assistant has already reviewed the reports and labeled the relevant pages.
        #Main Task: Read the user’s QUESTION and the LABELS in the document.
        Identify the specific pages that need to be reviewed again to accurately answer the question and commment why.
        If you cannot answer the question based on the available data, return null to indicate this clearly.
        #Critical Consideration
        Your answer directly influences financial decisions, potentially leading to significant gains or losses for the user.
        If uncertain, err on the side of inclusion rather than exclusion.
        Accuracy is paramount—a mistake can have serious consequences.
        """

    prompt = ("QUESTION\n\n"
              f"{question}\n\n"
              "KNOWLEDGE DATABASE\n\n"
              f"{labels}")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    
    class PagesForReview(BaseModel):
        pages: list[int]
        comment: str
    
    response = completion(
        model='gpt-4o-mini',  #groq/llama-3.3-70b-versatile
        messages=messages,
        response_format=PagesForReview
    )

    # Extract token usage details
    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens
    cached_tokens = usage.prompt_tokens_details.cached_tokens
    
    # Prepare data for CSV
    stage = "filter_labels"
    timestamps = datetime.now().isoformat()  # Assuming you want the current timestamp
    file_name = file_name  # Assuming file_name is defined in the outer scope

    # Write to CSV
    with open('token_statistics.csv', mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        # Write header column names if the file is empty
        if csv_file.tell() == 0:
            writer.writerow(['Stage', 'Timestamp', 'File Name', 'Prompt Tokens', 'Completion Tokens', 'Total Tokens', 'Cached Tokens'])
        writer.writerow([stage, timestamps, file_name, prompt_tokens, completion_tokens, total_tokens, cached_tokens])  # Extract cached tokens

    logging.info(f"🔹 Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")

    # Parse response content
    response_dict = json.loads(response.choices[0].message.content)
    return response_dict


def answer_the_question(text, question, comment, file_name, kind):
    print(f'PRRRRRRR {question}')
    system_prompt = f"""
        ROLE: InvestGuru – Expert in Analyzing Public Company Reports
        You are InvestGuru, a financial expert specializing in analyzing and answering questions based on public company reports.
        #Main Task
        You already know which pages of the report are likely to contain the answer to the user’s question.
        Answer the user’s QUESTION using only the text from the DOCUMENT.
        Additionally, you can refer to your own COMMENTS if they help in forming a precise answer.
        If the available data does not allow you to answer the question, return null to indicate this clearly.
        If answer is found return the Physical page number in the PDF file that that is answer referencing to overwise null.
        #Critical Considerations
        Your answer directly influences financial decisions, with potential significant gains or losses for the user.
        Accuracy is paramount—errors can have serious consequences.
        #Strict Rules: 
        If the metric is an amount, extract the exact amount (e.g. if the amount in the document is given as '100 (in thousands)' or '100k', extract the value '100000'
        You will be PENALIZED for wrong answers.
        NEVER HALLUCINATE—base your response strictly on available data.
        DO NOT overlook critical context.
        """

    prompt = f"""
        QUESTION\n\n{question} with Kind of the question {kind}\n\n
        DOCUMENT named pdf_sha1={file_name}\n\n{text}\n\n
        COMMENT\n\n{comment}
        """
    

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    
    class SourceReference(BaseModel):
        page_index: int = Field(..., description="Physical page number in the PDF file")
        pdf_sha1: str = Field(..., description="SHA1 hash of the PDF file")
    
    class Answer(BaseModel):
        question_text: str = Field(..., description="Text of the question")
        kind: Literal["number", "name", "boolean", "names"] = Field(..., description="Kind of the question")
        value: Union[float, str, bool, List[str], Literal["N/A"]] = Field(..., description="Answer to the question, according to the question schema")
        references: List[SourceReference]

    
    response = completion(
        model='gpt-4o-mini',  #groq/llama-3.3-70b-versatile
        messages=messages,
        response_format=Answer
    )

    # Extract token usage details
    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens
    cached_tokens = usage.prompt_tokens_details.cached_tokens
    
    # Prepare data for CSV
    stage = "answer_question"
    timestamps = datetime.now().isoformat()  # Assuming you want the current timestamp
    file_name = file_name  # Assuming file_name is defined in the outer scope

    # Write to CSV
    with open('token_statistics.csv', mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        # Write header column names if the file is empty
        if csv_file.tell() == 0:
            writer.writerow(['Stage', 'Timestamp', 'File Name', 'Prompt Tokens', 'Completion Tokens', 'Total Tokens', 'Cached Tokens'])
        writer.writerow([stage, timestamps, file_name, prompt_tokens, completion_tokens, total_tokens, cached_tokens])  # Extract cached tokens

    logging.info(f"🔹 Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")


    # Parse response content
    response_dict = json.loads(response.choices[0].message.content)
    return response_dict



TOKENIZER = tiktoken.encoding_for_model("gpt-4o-mini")

import time
with open("updated_questions.json", "r") as f:
    questions = json.load(f)

# Initialize answers list
answers_list = []

for question in questions:
    file_name = question['file_name']
    question_text = question['text']
    question_kind = question['kind']
    
    logging.info(f'Start answer: {question_text}')

    lables_json_file_path = f"output/labels/{file_name}.json"  # Replace with your actual JSON file path
    labeled_pages_list = extract_pdf_pages_for_answer(lables_json_file_path)
    labels_for_the_questions = check_labels(question=question_text, labels=labeled_pages_list, file_name=file_name)
    pages = labels_for_the_questions['pages']
    comment = labels_for_the_questions['comment']
    logging.info(f'Pages for context: {pages}. Comment - {comment}')
    
    logging.info(f'Answering: {question_text}')
    
    pdf_path = f"examples/pdfs/{file_name}.pdf"
    pdf_parsed_texts = parse_pdf(pdf_path=pdf_path, pages=pages, max_tokens=100_000)
    answer = answer_the_question(text=pdf_parsed_texts, question=question_text, comment=comment, kind=question_kind, file_name=file_name)
    print(answer)
    answer['question_text'] = question_text
    answers_list.append(answer)

    output_data = {
            "team_email": 'g@ff',
            "submission_name": '1',
            "answers": answers_list
        }
    with open('output/answers.json', "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)