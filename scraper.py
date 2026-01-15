import requests
from bs4 import BeautifulSoup
import psycopg2
import time
import re
import os

# --- Configuration ---
# User provided: postgresql://postgres:[YOUR-PASSWORD]@db.middbjbehbnmdhujcpkc.supabase.co:5432/postgres
# PLEASE REPLACE [YOUR-PASSWORD] with your actual password below or set DB_PASSWORD env var
DB_PASSWORD = os.environ.get('DB_PASSWORD', '3JfalhJ719XbKYmw')
DB_HOST = "db.middbjbehbnmdhujcpkc.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PORT = "6543"

BASE_URL = 'https://studentscholarships.org'
LIST_URL = 'https://studentscholarships.org/scholarships'

def get_db_connection():
    try:
        print(f"Connecting to {DB_HOST} as {DB_USER}...")
        print(f"Password length: {len(DB_PASSWORD)}")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Detailed error:", e)
        print("Please verify your password is correct in the script.")
        return None

def setup_database():
    """Creates the table if it doesn't exist."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    # PostgreSQL syntax
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scholarships (
            id SERIAL PRIMARY KEY,
            name TEXT,
            scholarship_group TEXT,
            amount TEXT,
            deadline TEXT,
            description TEXT,
            application_link TEXT,
            detail_url TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()
    print("Database setup complete.")

def get_scholarship_details(detail_url):
    """Fetches description and application link from the detail page."""
    try:
        response = requests.get(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return None, None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        description = "No description found"
        
        # Attempt to find the main content block
        # The content is typically in an <article> tag
        article = soup.find('article')
        
        if article:
            # Create a copy to avoid modifying the original soup if we were reusing it (not here, but good practice)
            # Remove metadata we don't want in the description
            # social-left contains Value, Awards Available, Deadline
            # social-right contains share buttons
            for div in article.find_all('div', id=['social-left', 'social-right']):
                div.decompose()
            
            # Remove other clutter
            for element in article.find_all(class_=['sharethis-inline-share-buttons', 'google-ad']):
                element.decompose()
                
            # Remove script and style tags just in case
            for script in article(["script", "style"]):
                script.decompose()
                
            # Extract text with separators for readability
            full_text = article.get_text(separator=' ', strip=True)
            description = extract_summary(full_text)
            
        else:
             # Fallback if no article tag - try 'main' or specific ID
             main_content = soup.find('main', class_='left-column')
             if main_content:
                 full_text = main_content.get_text(separator=' ', strip=True)
                 description = extract_summary(full_text)
             else:
                 # Last resort fallback, but try to avoid the whole page
                 # Look for the first substantial paragraph
                 first_p = soup.find('p')
                 if first_p:
                     description = extract_summary(first_p.get_text(strip=True))
                 else:
                    description = "Could not extract description."

        # Application Link
        app_link = "Not found"
        # Look for "GO TO SCHOLARSHIP APPLICATION"
        # Often it is a button with specific text
        app_btn = soup.find(lambda tag: tag.name == 'a' and 'GO TO SCHOLARSHIP APPLICATION' in tag.get_text(strip=True).upper())
        if app_btn:
            app_link = app_btn.get('href')

        return description, app_link

    except Exception as e:
        print(f"Error fetching details for {detail_url}: {e}")
        return None, None

def extract_summary(text):
    """
    Extracts the first sentence or a reasonable summary from the text.
    Handles basic abbreviation cases like 'U.S.' or 'Dr.' to avoid bad splits.
    """
    if not text:
        return "No description found"
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Simple heuristic: split by '. ' but try to respect abbreviations
    # We look for a period followed by a space, where the preceding word isn't a known abbreviation
    # This is a basic implementation.
    
    # Known abbreviations that usually don't end a sentence
    abbrevs = {'u.s.', 'st.', 'mr.', 'mrs.', 'dr.', 'inc.', 'co.', 'e.g.', 'i.e.'}
    
    words = text.split(' ')
    summary_words = []
    
    for i, word in enumerate(words):
        summary_words.append(word)
        if word.endswith('.') or word.endswith('!') or word.endswith('?'):
            # Check if it is an abbreviation
            if word.lower() in abbrevs:
                continue
            
            # Check for single letters like "A. Smith" unless it's "I." or "A." as a sentence? 
            # Usually single uppercase letter followed by dot is an initial.
            if len(word) == 2 and word[0].isupper() and word[0] != 'I': # I. is rarely an initial at end of word, but 'I' is a word. 'I.' is unlikely.
                 continue
                 
            # If we are here, we likely found the end of a sentence.
            # However, if the description is VERY short (e.g. "Value: $500."), maybe take more?
            # User wants first sentence.
            
            # Additional check: if the next word starts with lowercase, it might not be a sentence end (though typically scrape text has correct casing)
            if i + 1 < len(words):
                 next_word = words[i+1]
                 if next_word and next_word[0].islower():
                     continue
            
            break
    
    summary = " ".join(summary_words)
    return summary

def scrape_scholarships():
    """Main scraping function."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    print(f"Fetching list from {LIST_URL}...")
    response = requests.get(LIST_URL, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')

    titles = soup.find_all('h5')
    print(f"Found {len(titles)} potential scholarships.")

    for i, title_tag in enumerate(titles):
        # Limit for testing
        # Limit removed to scrape all
        # if i >= 10: 
        #    break
            
        name = title_tag.get_text(strip=True)
        # Find link
        detail_rel_url = None
        parent_a = title_tag.find_parent('a')
        if parent_a:
            detail_rel_url = parent_a['href']
        else:
            child_a = title_tag.find('a')
            if child_a:
                detail_rel_url = child_a['href']
        
        if not detail_rel_url:
            continue

        if not detail_rel_url.startswith('http'):
            detail_full_url = BASE_URL + detail_rel_url
        else:
            detail_full_url = detail_rel_url

        # Amount - usually in the same row
        row = title_tag.find_parent('div', class_='row')
        if not row:
             row = title_tag.find_parent('div')
        
        amount = "Unknown"
        if row:
            amount_tag = row.find(class_='money')
            if amount_tag:
                 amount = amount_tag.get_text(strip=True)
        
        # Deadline
        deadline = "Unknown"
        if row:
            # Look for the text "Deadline"
            deadline_label = row.find(string=re.compile("Deadline", re.I))
            if deadline_label:
                # Structure seen: <span ...>Deadline</span>: <strong>DATE</strong>
                # Or just text.
                # Let's try to get the Next Element Sibling which might be the strong tag with the date
                next_el = deadline_label.find_next("strong")
                if next_el:
                    deadline = next_el.get_text(strip=True)
                else:
                    # Fallback: traverse siblings
                    parent = deadline_label.parent # the span
                    if parent:
                        siblings = list(parent.next_siblings)
                        text_content = "".join([s.get_text(strip=True) if hasattr(s, 'get_text') else str(s) for s in siblings])
                        # text_content might be ": 02/01/2026"
                        # Clean it
                        deadline = text_content.replace(":","").strip()

        group = "Recently Added"

        print(f"Processing: {name}")
        description, app_link = get_scholarship_details(detail_full_url)
        
        # Insert into DB
        try:
            cursor.execute('''
                INSERT INTO scholarships (name, scholarship_group, amount, deadline, description, application_link, detail_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (detail_url) DO UPDATE SET
                    deadline = EXCLUDED.deadline,
                    amount = EXCLUDED.amount,
                    application_link = EXCLUDED.application_link,
                    description = EXCLUDED.description
            ''', (name, group, amount, deadline, description, app_link, detail_full_url))
            conn.commit()
        except Exception as e:
            print(f"Error inserting {name}: {e}")
            conn.rollback()
        
        time.sleep(1) 

    conn.close()
    print("Scraping finished.")

if __name__ == "__main__":
    setup_database()
    scrape_scholarships()
