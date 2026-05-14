# Doc Verify

Document verification web app for uploaded identity and academic documents.

## Setup

1. Copy `config.example.php` to `config.php`.
2. Update database, Python, Tesseract, and optional Smile ID settings in `config.php`.
3. Import `database.sql` into MySQL.
4. Create a Python virtual environment and install the required packages for the scripts in `python/`.
5. Make sure `models/Gov_Docs_Model.pt` exists before using trained-model detection.

## Notes

- `config.php`, uploaded documents, local datasets, logs, and virtual environments are intentionally ignored by Git.
- The upload form supports optional candidates and document types including national ID, driving license, certificate, transcript, and other documents.
