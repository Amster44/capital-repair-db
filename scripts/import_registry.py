"""
Import Registry of Information Providers (Реестр поставщиков информации)
Updates management_companies table with contact information
"""

import logging
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from config import DB_CONFIG, BASE_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_phone(phone):
    """Clean and format phone number"""
    if pd.isna(phone) or not phone:
        return None

    # Remove all non-digit characters
    phone = str(phone).strip()
    # Keep only digits, plus, and parentheses
    phone = ''.join(c for c in phone if c.isdigit() or c in '+()-')

    if not phone or phone == '':
        return None

    return phone


def clean_email(email):
    """Clean email address"""
    if pd.isna(email) or not email:
        return None

    email = str(email).strip().lower()

    if not email or '@' not in email:
        return None

    return email


def clean_ogrn(ogrn):
    """Clean OGRN number"""
    if pd.isna(ogrn) or not ogrn:
        return None

    ogrn = str(ogrn).strip()

    # Remove non-digits
    ogrn = ''.join(c for c in ogrn if c.isdigit())

    # OGRN should be 13 or 15 digits
    if len(ogrn) not in [13, 15]:
        return None

    return ogrn


def import_registry(file_path: Path):
    """Import Registry Excel file"""

    if not file_path.exists():
        logger.error(f"Registry file not found: {file_path}")
        return

    logger.info(f"Reading Excel file: {file_path}")

    try:
        # Read Excel file (header is in row 3, rows 0-1 are title)
        df = pd.read_excel(file_path, sheet_name=0, header=2)

        logger.info(f"Loaded {len(df)} records from Excel")
        logger.info(f"Columns: {df.columns.tolist()}")

        # Try to identify column names (they might vary)
        # Common patterns for column names
        ogrn_col = None
        name_col = None
        phone_col = None
        email_col = None
        director_col = None
        address_col = None

        for col in df.columns:
            col_lower = str(col).lower()

            if 'огрн' in col_lower and not ogrn_col:
                ogrn_col = col
            elif ('наименование' in col_lower or 'название' in col_lower or 'организац' in col_lower) and not name_col:
                name_col = col
            elif ('телефон' in col_lower or 'тел.' in col_lower or 'phone' in col_lower) and not phone_col:
                phone_col = col
            elif ('email' in col_lower or 'e-mail' in col_lower or 'почт' in col_lower) and not email_col:
                email_col = col
            elif ('руководител' in col_lower or 'директор' in col_lower or 'фио' in col_lower) and not director_col:
                director_col = col
            elif ('адрес' in col_lower or 'address' in col_lower) and not address_col:
                address_col = col

        logger.info(f"Identified columns:")
        logger.info(f"  OGRN: {ogrn_col}")
        logger.info(f"  Name: {name_col}")
        logger.info(f"  Phone: {phone_col}")
        logger.info(f"  Email: {email_col}")
        logger.info(f"  Director: {director_col}")
        logger.info(f"  Address: {address_col}")

        if not ogrn_col:
            logger.error("Cannot find OGRN column in Excel file")
            return

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get all management companies from database
        cur.execute("SELECT id, ogrn FROM management_companies WHERE ogrn IS NOT NULL")
        db_companies = {row[1]: row[0] for row in cur.fetchall()}

        logger.info(f"Found {len(db_companies)} management companies in database")

        # Prepare update records
        updates = []
        matched = 0
        with_phone = 0
        with_email = 0
        with_director = 0

        for idx, row in df.iterrows():
            try:
                ogrn = clean_ogrn(row.get(ogrn_col))

                if not ogrn or ogrn not in db_companies:
                    continue

                matched += 1
                mc_id = db_companies[ogrn]

                # Extract contact info
                phone = clean_phone(row.get(phone_col)) if phone_col else None
                email = clean_email(row.get(email_col)) if email_col else None
                director = str(row.get(director_col)).strip() if director_col and pd.notna(row.get(director_col)) else None
                address = str(row.get(address_col)).strip() if address_col and pd.notna(row.get(address_col)) else None
                name = str(row.get(name_col)).strip() if name_col and pd.notna(row.get(name_col)) else None

                # Count statistics
                if phone:
                    with_phone += 1
                if email:
                    with_email += 1
                if director:
                    with_director += 1

                updates.append((
                    name,
                    phone,
                    email,
                    director,
                    address,
                    mc_id
                ))

            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                continue

        logger.info(f"Matched {matched} companies from Registry with database")
        logger.info(f"  With phone: {with_phone} ({with_phone*100//max(matched,1)}%)")
        logger.info(f"  With email: {with_email} ({with_email*100//max(matched,1)}%)")
        logger.info(f"  With director: {with_director} ({with_director*100//max(matched,1)}%)")

        # Execute updates
        if updates:
            execute_batch(
                cur,
                """
                UPDATE management_companies SET
                    name = COALESCE(NULLIF(%s, ''), name),
                    phone = COALESCE(NULLIF(%s, ''), phone),
                    email = COALESCE(NULLIF(%s, ''), email),
                    director_name = COALESCE(NULLIF(%s, ''), director_name),
                    legal_address = COALESCE(NULLIF(%s, ''), legal_address),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                updates,
                page_size=1000
            )

            conn.commit()
            logger.info(f"Updated {len(updates)} management companies with contact information")

        cur.close()
        conn.close()

        logger.info("=" * 60)
        logger.info("Registry import completed!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error importing registry: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Import Registry of Information Providers')
    parser.add_argument('--file', type=str,
                       default='Реестр поставщиков информации от  2026-02-01.xlsx',
                       help='Path to Registry Excel file')

    args = parser.parse_args()

    # Determine file path
    if Path(args.file).is_absolute():
        file_path = Path(args.file)
    else:
        # Try in base directory first
        file_path = BASE_DIR / args.file
        if not file_path.exists():
            # Try in data directory
            file_path = BASE_DIR / 'data' / args.file

    if not file_path.exists():
        logger.error(f"Registry file not found: {file_path}")
        logger.error("Please provide correct path with --file parameter")
        exit(1)

    logger.info(f"Importing Registry from: {file_path}")
    import_registry(file_path)
