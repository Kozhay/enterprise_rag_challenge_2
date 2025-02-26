# TASK
Question generator for the second round of RAG challenge is published!

Find it on Github in main.py. It uses an extended dataset of all PDFs in our database to generate better questions. This entire file is also published in the repository (dataset.json) so you can generate question lists locally.

During the competition we will pick a random subset of PDFs from this entire dataset and share them for the ingestion. Afterwards we will generate and share questions for that subset.

For now, you can find a few samples of PDFs in samples and (round1/pdf)

### Note: you need not only to extract the answers, but also reference pages from which they were extracted. This is the same work with references, sources and quotes that the enterprise segment likes for explainability.

Next week we'll publish the submission API details and will do an optional dry run on Thursday.

# DRY RUN

Quick summary for the dry run:

(1) Data (questions, subset and PDFs) is available here: https://rag.timetoact.at/data/r2.0-test/
(2) Challenge data next week will be places in exactly the same format in this folder: https://rag.timetoact.at/data/r2.0/ (but it will have more PDFs and data from the different seed)
(3) You can already try running your RAG agents to answer the questions and upload them to the submission UI/API (preview): https://rag.timetoact.at/
(4) Source code for the question generator is located here: https://github.com/trustbit/enterprise-rag-challenge You can study it and use it.

Next week run will be similar, but much slower, since we'll wait for the proper random seed from some block chain. Plus we'll have an awesome keynote!

Huge thanks to everybody who came to the dry run today, asked questions and provided feedback!