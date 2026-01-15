import psycopg2
import os

DB_PASSWORD = os.environ.get('DB_PASSWORD', '3JfalhJ719XbKYmw')
DB_HOST = "db.middbjbehbnmdhujcpkc.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PORT = "6543"

def verify_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode='require'
        )
        cursor = conn.cursor()
        
        print("Fetching 'Be Bold Scholarship'...")
        cursor.execute("SELECT name, description FROM scholarships WHERE name LIKE '%Be Bold%' LIMIT 1")
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"Name: {row[0]}")
            print(f"Description (first 200 chars): {row[1][:200]}")
            print("-" * 40)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_data()
