# Automated Document-to-JSON Pipeline setup

The automated pipeline for converting IDX downloaded PDFs and Excel files into JSON format has been successfully created and started!

## Changes Made

1. **Environment Setup**: 
   - Created the pipeline directory at `/home/ronysitepu/vibecoding/documenttotext/`.
   - Initialized a Python virtual environment (`venv`).
   - Installed the required libraries (`pdfplumber`, `pandas`, `openpyxl`, `watchdog`, and `xlrd` for `.xls` compatibility).

2. **Configuration (`config.json`)**:
   - Created `config.json` defining the `source_path`, `target_path`, `lookback_count` (50), and `file_types` (`.pdf`, `.xls`, `.xlsx`).

3. **Pipeline Script (`doc_cleaner.py`)**:
   - **Phase 1 (The Lookback)**: Automatically scans the source directory, sorts by newest modified, grabs up to 50 eligible files not yet present in `clean_docs`, and processes them.
   - **Phase 2 (The Listener)**: Uses `watchdog` to continuously monitor the source directory for any newly created or moved files, instantly triggering conversion.
   - **Conversion Logic**: PDFs have their text and tables extracted using `pdfplumber`, and Excel files are parsed using `pandas`. All files are saved to `clean_docs` as `[original_filename].json`.

4. **Runner Script (`run_cleaner.sh`)**:
   - Created and made executable a bash wrapper script that activates the virtual environment and runs the pipeline.

## Current Status

> [!NOTE]
> The initial script execution has been triggered in the background. It successfully found the top 50 newest documents and is currently processing them. 
> Extracting text and tables from large PDFs (like Annual Reports) using `pdfplumber` is a CPU-intensive operation and will take some time to complete the initial batch. Once Phase 1 finishes, it will automatically enter Phase 2 and listen for new downloads.

You can monitor its activity by checking the `clean_docs` directory for the newly generated `.json` files!
