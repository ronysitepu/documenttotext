# Automated Document-to-JSON Pipeline

An automated pipeline designed to monitor a directory for financial documents (PDFs, Excel files) and convert them into structured JSON format for easy analysis.

## Features

- **Phase 1 (The Lookback)**: Scans the source folder on startup and processes the most recent documents (up to 50 by default) that haven't been cleaned yet.
- **Phase 2 (The Listener)**: Uses the `watchdog` library to monitor the source folder in real-time. New files are processed immediately upon detection.
- **Robust Extraction**:
  - **PDFs**: Extracts both plain text and structured tables using `pdfplumber`.
  - **Excel**: Converts all sheets into JSON records using `pandas`.
- **Configurable**: Easily adjust source/target paths and file types via `config.json`.

## Setup

1.  **Dependencies**:
    - Python 3.x
    - `pdfplumber`, `pandas`, `openpyxl`, `watchdog`, `xlrd`
2.  **Configuration**: Edit `config.json` to set your `source_path` and `target_path`.
3.  **Run**:
    ```bash
    ./run_cleaner.sh
    ```

## Project Structure

- `doc_cleaner.py`: The core logic for processing and monitoring.
- `config.json`: Configuration settings.
- `run_cleaner.sh`: Bash script to activate the virtual environment and start the cleaner.
- `walkthrough.md`: Detailed walkthrough of the implementation.

## Implementation Details

For a deep dive into how this was built, see [walkthrough.md](./walkthrough.md).
