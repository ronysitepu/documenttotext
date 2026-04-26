import json
import os
import time
import subprocess
import pdfplumber
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import openpyxl

stats = {"processed": 0, "scans": 0, "skipped": 0}
pending_sync = False
last_processed_time = 0
def process_pdf(file_path):
    data = {"text": "", "tables": []}
    is_scan = False
    try:
        with pdfplumber.open(file_path) as pdf:
            total_chars = 0
            for page in pdf.pages[:3]:
                text = page.extract_text()
                if text:
                    total_chars += len(text)
            
            if total_chars < 50:
                return {"status": "manual_review_required", "reason": "scanned_document_detected"}, True
                
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    data["text"] += text + "\n"
                tables = page.extract_tables()
                if tables:
                    data["tables"].extend(tables)
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
    return data, is_scan

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
    global stats
    filename = os.path.basename(source_path)
    ext = os.path.splitext(filename)[1].lower()
    
    target_path = os.path.join(target_dir, f"{filename}.json")
    if os.path.exists(target_path):
        stats["skipped"] += 1
        print(f"Processed: {stats['processed']} | Scans: {stats['scans']} | Skipped: {stats['skipped']}")
        return False
        
    print(f"Processing: {filename}")
    
    data = None
    is_scan = False
    if ext == ".pdf":
        data, is_scan = process_pdf(source_path)
    elif ext in [".xls", ".xlsx"]:
        data = process_excel(source_path)
        
    if data is not None:
        os.makedirs(target_dir, exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if is_scan:
            stats["scans"] += 1
        else:
            stats["processed"] += 1
            
        print(f"Processed: {stats['processed']} | Scans: {stats['scans']} | Skipped: {stats['skipped']}")
        return True
    return False

def run_rclone(config):
    if config.get("rclone_enabled"):
        target_path = config.get("target_path")
        rclone_target = config.get("rclone_target")
        if target_path and rclone_target:
            try:
                subprocess.run(
                    ["rclone", "copy", target_path, rclone_target, "--include", "*.json"],
                    check=False,
                    capture_output=True
                )
            except Exception as e:
                print(f"Rclone sync failed: {e}")

class DocumentHandler(FileSystemEventHandler):
    def __init__(self, target_dir, file_types, config):
        self.target_dir = target_dir
        self.file_types = file_types
        self.config = config

    def on_created(self, event):
        if not event.is_directory:
            self.handle_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.handle_file(event.dest_path)
            
    def handle_file(self, file_path):
        global pending_sync, last_processed_time
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.file_types:
            time.sleep(2)
            if process_file(file_path, self.target_dir):
                pending_sync = True
                last_processed_time = time.time()

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
    
    to_process = files[:lookback_count]
            
    print(f"Found {len(to_process)} newest files to evaluate.")
    processed_any = False
    for f in to_process:
        if process_file(f, target_path):
            processed_any = True
            
    if processed_any:
        run_rclone(config)
        
    print("\n--- Phase 2: The Listener ---")
    event_handler = DocumentHandler(target_path, file_types, config)
    observer = Observer()
    observer.schedule(event_handler, source_path, recursive=False)
    observer.start()
    print(f"Started monitoring '{source_path}' for new documents...")
    
    global pending_sync, last_processed_time
    try:
        while True:
            time.sleep(1)
            # Batch sync logic: if pending and 10 seconds of inactivity detected
            if pending_sync and (time.time() - last_processed_time > 10):
                print("\n--- Batch Sync Triggered (Inactivity) ---")
                run_rclone(config)
                pending_sync = False
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
