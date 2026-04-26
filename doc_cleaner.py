import json
import os
import time
import pdfplumber
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import openpyxl

def process_pdf(file_path):
    data = {"text": "", "tables": []}
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    data["text"] += text + "\n"
                tables = page.extract_tables()
                if tables:
                    data["tables"].extend(tables)
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
    return data

def process_excel(file_path):
    data = {}
    try:
        # We rely on pandas to use the appropriate engine (openpyxl for .xlsx, xlrd for .xls)
        xls = pd.read_excel(file_path, sheet_name=None)
        for sheet_name, df in xls.items():
            # Replace NaNs with None to ensure valid JSON
            df = df.where(pd.notnull(df), None)
            data[sheet_name] = df.to_dict(orient='records')
    except Exception as e:
        print(f"Error processing Excel {file_path}: {e}")
    return data

def process_file(source_path, target_dir):
    filename = os.path.basename(source_path)
    ext = os.path.splitext(filename)[1].lower()
    
    print(f"Processing: {filename}")
    
    # Check if target already exists to prevent duplicate processing
    target_path = os.path.join(target_dir, f"{filename}.json")
    if os.path.exists(target_path):
        print(f"Skipping {filename}, already exists at {target_path}")
        return
        
    data = None
    if ext == ".pdf":
        data = process_pdf(source_path)
    elif ext in [".xls", ".xlsx"]:
        data = process_excel(source_path)
        
    if data is not None:
        os.makedirs(target_dir, exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully processed and saved: {target_path}")

class DocumentHandler(FileSystemEventHandler):
    def __init__(self, target_dir, file_types):
        self.target_dir = target_dir
        self.file_types = file_types

    def on_created(self, event):
        if not event.is_directory:
            self.handle_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.handle_file(event.dest_path)
            
    def handle_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.file_types:
            # Short sleep to allow the system to finish writing the file
            time.sleep(2)
            process_file(file_path, self.target_dir)

def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
        
    source_path = config.get('source_path')
    target_path = config.get('target_path')
    lookback_count = config.get('lookback_count', 50)
    file_types = config.get('file_types', ['.pdf', '.xls', '.xlsx'])
    
    # Ensure source and target directories exist
    os.makedirs(source_path, exist_ok=True)
    os.makedirs(target_path, exist_ok=True)
    
    print("--- Phase 1: The Lookback ---")
    files = []
    for f in os.listdir(source_path):
        ext = os.path.splitext(f)[1].lower()
        if ext in file_types:
            path = os.path.join(source_path, f)
            if os.path.isfile(path):
                files.append(path)
                
    # Sort by 'date modified' (newest first)
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    to_process = []
    for f in files:
        if len(to_process) >= lookback_count:
            break
        original_name = os.path.basename(f)
        out_path = os.path.join(target_path, f"{original_name}.json")
        if not os.path.exists(out_path):
            to_process.append(f)
            
    print(f"Found {len(to_process)} new files to process out of top {lookback_count} newest.")
    for f in to_process:
        process_file(f, target_path)
        
    print("\n--- Phase 2: The Listener ---")
    event_handler = DocumentHandler(target_path, file_types)
    observer = Observer()
    observer.schedule(event_handler, source_path, recursive=False)
    observer.start()
    print(f"Started monitoring '{source_path}' for new documents...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
