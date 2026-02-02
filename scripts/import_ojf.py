"""
Import OJF (Objects of Housing Fund) data to establish house→UK relationships
Processes CSV files from data/ojf_data/ and links buildings to management companies
"""

import csv
import logging
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch
from config import DB_CONFIG, BASE_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Mapping of region names in OJF files to region codes
OJF_REGION_MAPPING = {
    'Татарстан Респ': '16',
    'Башкортостан Респ': '02',
    'Марий Эл Респ': '12',
    'Мордовия Респ': '13',
    'Удмуртская Респ': '18',
    'Чувашская Республика': '21',
    'Кировская обл': '43',
    'Нижегородская обл': '52',
    'Оренбургская обл': '56',
    'Пензенская обл': '58',
    'Пермский край': '59',
    'Самарская обл': '63',
    'Саратовская обл': '64',
    'Ульяновская обл': '73'
}


def get_region_code_from_filename(filename: str) -> str:
    """Extract region code from OJF filename"""
    for region_name, code in OJF_REGION_MAPPING.items():
        if region_name in filename:
            return code
    return None


def import_ojf_file(filepath: Path, conn):
    """Import single OJF CSV file"""
    filename = filepath.name
    region_code = get_region_code_from_filename(filename)

    if not region_code:
        logger.warning(f"Cannot determine region for file: {filename}")
        return 0, 0

    logger.info(f"Processing {filename} (region {region_code})...")

    # Get region_id from database
    cur = conn.cursor()
    cur.execute("SELECT id FROM regions WHERE region_code = %s", (region_code,))
    result = cur.fetchone()

    if not result:
        logger.warning(f"Region {region_code} not found in database")
        cur.close()
        return 0, 0

    region_id = result[0]

    # Dictionary to store unique houses: houseguid → (ogrn, uk_name, management_type)
    houses = {}
    uk_data = {}  # ogrn → (name, management_type)

    processed = 0
    errors = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Use pipe delimiter
            reader = csv.DictReader(f, delimiter='|')

            for row in reader:
                processed += 1

                try:
                    houseguid = row.get('Глобальный уникальный идентификатор дома по ФИАС', '').strip()
                    # If multiple UUIDs (separated by ;), take only the first one
                    if ';' in houseguid:
                        houseguid = houseguid.split(';')[0].strip()

                    ogrn = row.get('ОГРН организации, осуществляющей управление домом', '').strip()
                    uk_name = row.get('Наименование организации, осуществляющей управление домом', '').strip()
                    management_type = row.get('Способ управления', '').strip()

                    # Skip if no houseguid or no management company
                    if not houseguid or not ogrn:
                        continue

                    # Convert management type to our codes
                    mgmt_code = None
                    if management_type == 'УО':  # Управляющая организация
                        mgmt_code = 'UK'
                    elif management_type == 'ТСЖ':
                        mgmt_code = 'TSJ'
                    elif management_type == 'ЖСК':
                        mgmt_code = 'JSK'

                    if not mgmt_code:
                        continue  # Skip regional operators and others

                    # Store house data
                    if houseguid not in houses:
                        houses[houseguid] = (ogrn, uk_name, mgmt_code)

                    # Store UK data
                    if ogrn not in uk_data:
                        uk_data[ogrn] = (uk_name, mgmt_code)

                except Exception as e:
                    errors += 1
                    if errors <= 10:  # Log only first 10 errors
                        logger.warning(f"Error processing row {processed}: {e}")
                    continue

        logger.info(f"Parsed {len(houses)} unique houses with {len(uk_data)} management companies")

        # Step 1: Import management companies
        if uk_data:
            uk_records = []
            for ogrn, (name, mgmt_type) in uk_data.items():
                uk_records.append((
                    ogrn,
                    name,
                    mgmt_type,
                    region_id
                ))

            # Get organization type IDs
            cur.execute("SELECT id, code FROM organization_types")
            org_type_map = {row[1]: row[0] for row in cur.fetchall()}

            # Update records with type_id
            uk_records_with_type = []
            for ogrn, name, mgmt_type, region_id in uk_records:
                type_id = org_type_map.get(mgmt_type)
                uk_records_with_type.append((ogrn, name, type_id, region_id))

            # Insert/update management companies
            execute_batch(
                cur,
                """
                INSERT INTO management_companies (ogrn, name, type_id, region_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (ogrn, region_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    type_id = EXCLUDED.type_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                uk_records_with_type,
                page_size=1000
            )

            logger.info(f"Imported {len(uk_records)} management companies")

        # Step 2: Link houses to management companies via buildings_management table
        if houses:
            # Get management_company IDs
            cur.execute("SELECT id, ogrn FROM management_companies WHERE ogrn = ANY(%s)",
                       (list(uk_data.keys()),))
            ogrn_to_id = {row[1]: row[0] for row in cur.fetchall()}

            # Get building IDs by houseguid (cast to UUID[])
            cur.execute(
                "SELECT id, houseguid FROM buildings WHERE houseguid = ANY(%s::uuid[]) AND region_id = %s",
                (list(houses.keys()), region_id)
            )
            houseguid_to_building = {row[1]: row[0] for row in cur.fetchall()}

            link_records = []
            for houseguid, (ogrn, uk_name, mgmt_code) in houses.items():
                mc_id = ogrn_to_id.get(ogrn)
                building_id = houseguid_to_building.get(houseguid)

                if mc_id and building_id:
                    link_records.append((building_id, mc_id))

            # Insert into buildings_management table
            if link_records:
                execute_batch(
                    cur,
                    """
                    INSERT INTO buildings_management (building_id, company_id, contract_start_date)
                    VALUES (%s, %s, CURRENT_DATE)
                    ON CONFLICT (building_id, company_id, contract_start_date) DO NOTHING
                    """,
                    link_records,
                    page_size=1000
                )

                logger.info(f"Linked {len(link_records)} buildings to management companies")

        conn.commit()
        cur.close()

        return len(houses), len(uk_data)

    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")
        conn.rollback()
        return 0, 0


def import_all_ojf_files(region_codes=None):
    """Import all OJF files for specified regions (or all PFO regions if None)"""
    ojf_dir = BASE_DIR / 'data' / 'ojf_data'

    if not ojf_dir.exists():
        logger.error(f"OJF data directory not found: {ojf_dir}")
        return

    # Get all OJF CSV files
    ojf_files = list(ojf_dir.glob('*.csv'))

    if not ojf_files:
        logger.error(f"No OJF CSV files found in {ojf_dir}")
        return

    logger.info(f"Found {len(ojf_files)} OJF files")

    # Filter for specified regions if provided
    if region_codes:
        region_names = [name for name, code in OJF_REGION_MAPPING.items() if code in region_codes]
        ojf_files = [f for f in ojf_files if any(name in f.name for name in region_names)]
        logger.info(f"Filtered to {len(ojf_files)} files for regions: {region_codes}")
    else:
        # Only process PFO region files
        pfo_names = list(OJF_REGION_MAPPING.keys())
        ojf_files = [f for f in ojf_files if any(name in f.name for name in pfo_names)]
        logger.info(f"Processing {len(ojf_files)} PFO region files")

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to database")

        total_houses = 0
        total_uk = 0

        for ojf_file in sorted(ojf_files):
            houses, uk = import_ojf_file(ojf_file, conn)
            total_houses += houses
            total_uk += uk

        logger.info("=" * 60)
        logger.info(f"OJF Import completed!")
        logger.info(f"Total unique houses: {total_houses}")
        logger.info(f"Total management companies: {total_uk}")
        logger.info("=" * 60)

        conn.close()

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Import OJF data')
    parser.add_argument('--region', type=str, help='Import only specific region (e.g., 16 for Tatarstan)')
    parser.add_argument('--all', action='store_true', help='Import all PFO regions')

    args = parser.parse_args()

    if args.region:
        logger.info(f"Importing OJF data for region {args.region}")
        import_all_ojf_files([args.region])
    elif args.all:
        logger.info("Importing OJF data for all PFO regions")
        import_all_ojf_files()
    else:
        # Default: all PFO regions
        logger.info("Importing OJF data for all PFO regions (use --region XX for specific region)")
        import_all_ojf_files()
