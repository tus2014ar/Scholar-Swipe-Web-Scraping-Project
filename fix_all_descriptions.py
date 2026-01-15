import psycopg2
import os
import time
from scraper import get_scholarship_details

DB_PASSWORD = os.environ.get('DB_PASSWORD', '3JfalhJ719XbKYmw')
DB_HOST = "db.middbjbehbnmdhujcpkc.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PORT = "6543"

def fix_all():
    conn = None
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode='require'
        )
        cursor = conn.cursor()
        
        print("Fetching all scholarship URLs...")
        cursor.execute("SELECT id, detail_url, name FROM scholarships")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} scholarships to check/fix.")
        
        for row in rows:
            sid = row[0]
            url = row[1]
            name = row[2]
            
            print(f"Fixing {name}...")
            
            description, app_link = get_scholarship_details(url)
            
            if description and description != "No description found":
                cursor.execute("""
                    UPDATE scholarships 
                    SET description = %s, application_link = %s
                    WHERE id = %s
                """, (description, app_link, sid))
                conn.commit()
            else:
                print(f"  Skipping update for {name} - failed to extract details.")
                
            # Be nice to the server
            time.sleep(0.5)
            
        print("Finished updating all descriptions.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_all()
