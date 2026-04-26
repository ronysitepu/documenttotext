# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-04-26

### Added
- **No-OCR & Reliability Logic**: PDFs with less than 50 characters in the first 3 pages are now flagged as scans to avoid invalid extractions.
- **Deduplication & State Tracker**: The script now skips files that already have a corresponding JSON in the target directory and displays real-time processing statistics (Processed, Scans, Skipped).
- **Rclone Cloud Sync**: Integrated automated synchronization to Google Drive using `rclone`.
- **Batch Upload Logic**: Implemented a debounce mechanism that batches uploads after 10 seconds of inactivity to optimize network usage.

### Changed
- **Config Structure**: Updated `config.json` to include `rclone` settings and support specific `source` subdirectories.
- **Improved Lookback**: Enhanced the lookback phase to handle larger file counts (e.g., 500+ files) efficiently.
