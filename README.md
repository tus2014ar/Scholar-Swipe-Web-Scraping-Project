# Scholarship Scraper

A Python automated scraping tool designed to extract scholarship opportunities from [StudentScholarships.org](https://studentscholarships.org) and aggregate them into a centralized PostgreSQL database (Supabase).

## Features

- **Automated Scraping**: Crawls scholarship listings to extract key details.
- **Smart Parsing**: accurately extracts:
  - Scholarship Name
  - Value / Amount
  - Deadline
  - Detailed Description (with automated summarization)
  - Application Links
- **Database Integration**: Directly saves and updates records in a PostgreSQL database.
- **Duplicate Management**: Uses `upsert` strategies to update existing scholarships without creating duplicates.
- **Robust Error Handling**: Handles network errors and missing data fields gracefully.

## Tech Stack

- **Language**: Python 3.x
- **Scraping**: `requests`, `BeautifulSoup4`
- **Database**: PostgreSQL (via `psycopg2`)

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd scholarship_scraper
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration:**
    The scraper requires database credentials. You can set them as environment variables or edit the configuration section in `scraper.py`.
    
    *Recommended: Set `DB_PASSWORD` environment variable.*
    ```bash
    export DB_PASSWORD='supabase_password'
    ```

## Usage

Run the main scraper script:

```bash
python scraper.py
```

The script will:
1. Initialize the database table (`scholarships`) if it doesn't exist.
2. Fetch the latest scholarship listings.
3. Process each item and insert/update the database.
4. Print progress logs to the console.

## Project Structure

- `scraper.py`: Main entry point containing scraping logic and database operations.
- `requirements.txt`: Python package dependencies.
- `fix_all_descriptions.py`: Utility script to re-process and clean existing description entries in the database.
- `verify_db.py`: Helper script to check database connectivity and row counts.
