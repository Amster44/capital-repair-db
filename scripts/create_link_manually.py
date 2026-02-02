"""Create link manually for testing"""
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

building_id = 31938
company_id = 187529

print(f"Creating link: Building {building_id} -> Company {company_id}")

try:
    cur.execute("""
        INSERT INTO buildings_management (building_id, company_id, contract_start_date)
        VALUES (%s, %s, CURRENT_DATE)
        ON CONFLICT (building_id, company_id, contract_start_date) DO NOTHING
    """, (building_id, company_id))

    conn.commit()
    print(f"Link created successfully!")

    # Verify
    cur.execute("""
        SELECT b.address, mc.name
        FROM buildings_management bm
        JOIN buildings b ON bm.building_id = b.id
        JOIN management_companies mc ON bm.company_id = mc.id
        WHERE bm.building_id = %s AND bm.company_id = %s
    """, (building_id, company_id))

    result = cur.fetchone()
    if result:
        print(f"\nVerification successful:")
        print(f"  Building: {result[0]}")
        print(f"  Company: {result[1]}")
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")

cur.close()
conn.close()
