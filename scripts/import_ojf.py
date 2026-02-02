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
import re

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


def normalize_address(address: str) -> str:
    """
    Maximum normalization for address matching
    Handles all variants of street types (abbreviated and full forms)
    Extracts only key components: city, street name, house number
    """
    if not address:
        return ""

    # Convert to lowercase first
    address = address.lower()

    # Remove postal code (6 digits at start)
    address = re.sub(r'^\d{6},?\s*', '', address)

    # Remove region prefixes (обл, Респ, край, АО, etc.)
    address = re.sub(r'^[^,]+\s+(обл|респ|край|ао|автономный округ)[,\s]*', '', address)

    # Normalize common abbreviations before processing
    address = address.replace(' г.', ' г ').replace(' г,', ' г ')
    address = address.replace(' д.', ' д ').replace(' д,', ' д ')
    address = address.replace(' корп.', ' к ').replace(' корп,', ' к ')
    address = address.replace(' стр.', ' с ').replace(' стр,', ' с ')
    address = address.replace(' кв.', ' кв ').replace(' кв,', ' кв ')

    # Define all street type variants (abbreviated and full forms)
    street_types = {
        # Шоссе variants
        r'\bш\.': 'шоссе',
        r'\bш\b': 'шоссе',
        r'\bшоссе\b': 'шоссе',
        # Переулок variants
        r'\bпер\.': 'переулок',
        r'\bпер\b': 'переулок',
        r'\bпереулок\b': 'переулок',
        # Улица variants
        r'\bул\.': 'улица',
        r'\bул\b': 'улица',
        r'\bулица\b': 'улица',
        # Проспект variants
        r'\bпр-кт\b': 'проспект',
        r'\bпр\.': 'проспект',
        r'\bпр\b': 'проспект',
        r'\bпросп\.': 'проспект',
        r'\bпроспект\b': 'проспект',
        # Бульвар variants
        r'\bб-р\.': 'бульвар',
        r'\bб-р\b': 'бульвар',
        r'\bбул\.': 'бульвар',
        r'\bбульвар\b': 'бульвар',
        # Набережная variants
        r'\bнаб\.': 'набережная',
        r'\bнабережная\b': 'набережная',
        # Площадь variants
        r'\bпл\.': 'площадь',
        r'\bплощадь\b': 'площадь',
        # Тупик variants
        r'\bтуп\.': 'тупик',
        r'\bтупик\b': 'тупик',
        # Проезд variants
        r'\bпр-д\b': 'проезд',
        r'\bпроезд\b': 'проезд',
    }

    # Unify all street type variants to standard forms
    for pattern, replacement in street_types.items():
        address = re.sub(pattern, replacement, address)

    # Fix street type order: "тип название" -> "название"
    # Match: comma/space + street_type + space + word(s)
    street_type_list = ['шоссе', 'переулок', 'улица', 'проспект', 'бульвар', 'набережная', 'площадь', 'тупик', 'проезд']

    for stype in street_type_list:
        # Match pattern: , тип Название (multi-word)
        # Capture street name and move it before type
        pattern = r',\s*' + stype + r'\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s\-]*?)(?=\s*[,д]|\s*$)'
        address = re.sub(pattern, r', \1', address)

    # Also handle "название тип" -> "название" (remove type that comes after)
    for stype in street_type_list:
        address = re.sub(r'\b' + stype + r'\b', '', address)

    # Remove city prefix "г"
    address = re.sub(r'\bг\s+', '', address)

    # Normalize house/building number markers
    address = re.sub(r'\bд\s+', 'д', address)
    address = re.sub(r'\bк\s+', 'к', address)
    address = re.sub(r'\bс\s+', 'с', address)

    # Normalize house litera (letter): remove space between number and letter
    # "303 А" -> "303а", "123 Б" -> "123б"
    address = re.sub(r'(\d+)\s+([а-яёА-ЯЁ])\b', r'\1\2', address)

    # Remove extra spaces and commas
    address = re.sub(r'\s+', ' ', address)
    address = re.sub(r'\s*,\s*', ',', address)  # Clean spaces around commas
    address = re.sub(r',+', ',', address)
    address = address.strip(' ,')

    return address


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

    # Dictionary to store unique houses: houseguid → (address, ogrn, uk_name, management_type)
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

                    address = row.get('Адрес ОЖФ', '').strip()
                    oktmo = row.get('Код ОКТМО', '').strip()
                    ogrn = row.get('ОГРН организации, осуществляющей управление домом', '').strip()
                    uk_name = row.get('Наименование организации, осуществляющей управление домом', '').strip()
                    management_type = row.get('Способ управления', '').strip()

                    # Normalize OKTMO to 8 digits (municipality level)
                    oktmo_short = oktmo[:8] if oktmo and len(oktmo) >= 8 else None

                    # Skip if no houseguid/address/oktmo or no management company
                    if (not houseguid and not address and not oktmo_short) or not ogrn:
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

                    # Store house data with all identifiers
                    # Use a composite key: houseguid + "|" + oktmo + "|" + address
                    key = f"{houseguid}|{oktmo_short}|{address}"
                    if key not in houses:
                        houses[key] = (houseguid, oktmo_short, address, ogrn, uk_name, mgmt_code)

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

            # Get all buildings in region with their municipality OKTMO codes
            cur.execute("""
                SELECT b.id, b.houseguid, b.address, m.oktmo_code
                FROM buildings b
                LEFT JOIN municipalities m ON b.municipality_id = m.id
                WHERE b.region_id = %s
            """, (region_id,))

            # Create lookup dictionaries
            houseguid_to_building = {}
            oktmo_address_to_building = {}
            address_to_building = {}

            for row in cur.fetchall():
                building_id = row[0]
                houseguid = str(row[1]) if row[1] else None
                address = row[2]
                oktmo = row[3]

                if houseguid:
                    houseguid_to_building[houseguid] = building_id

                if address:
                    normalized = normalize_address(address)
                    address_to_building[normalized] = building_id

                    # Create OKTMO+address lookup (municipality level - 8 digits)
                    if oktmo:
                        oktmo_short = oktmo[:8] if len(oktmo) >= 8 else oktmo
                        oktmo_key = f"{oktmo_short}|{normalized}"
                        oktmo_address_to_building[oktmo_key] = building_id

            # Match houses to buildings
            link_records = []
            matched_by_houseguid = 0
            matched_by_oktmo = 0
            matched_by_address = 0

            for key, (houseguid, oktmo_short, address, ogrn, uk_name, mgmt_code) in houses.items():
                mc_id = ogrn_to_id.get(ogrn)
                if not mc_id:
                    continue

                building_id = None

                # Try houseguid first
                if houseguid and houseguid in houseguid_to_building:
                    building_id = houseguid_to_building[houseguid]
                    matched_by_houseguid += 1

                # If not found by houseguid, try OKTMO + address
                if not building_id and oktmo_short and address:
                    normalized = normalize_address(address)
                    oktmo_key = f"{oktmo_short}|{normalized}"
                    if oktmo_key in oktmo_address_to_building:
                        building_id = oktmo_address_to_building[oktmo_key]
                        matched_by_oktmo += 1

                # If still not found, try address only
                if not building_id and address:
                    normalized = normalize_address(address)
                    if normalized in address_to_building:
                        building_id = address_to_building[normalized]
                        matched_by_address += 1

                if building_id:
                    link_records.append((building_id, mc_id))

            logger.info(f"Matched {matched_by_houseguid} buildings by houseguid, {matched_by_oktmo} by OKTMO+address, {matched_by_address} by address only")

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
