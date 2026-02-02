"""Search for specific address in all Samara OJF files"""
import csv
from pathlib import Path

ojf_dir = Path(r"c:\Users\Usr146\Desktop\Capital_repair_db\capital-repair-db\data\ojf_data")
ojf_files = list(ojf_dir.glob("*Самарская обл*.csv"))

print("=" * 80)
print("SEARCHING FOR: Тольятти, Южное шоссе, д. 23")
print("=" * 80)

found = False

for ojf_file in ojf_files:
    print(f"\nChecking {ojf_file.name}...")

    with open(ojf_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')

        for row in reader:
            address = row.get('Адрес ОЖФ', '')

            if 'Тольятти' in address and 'Южное' in address and ', д. 23' in address:
                found = True
                print(f"\nFOUND in {ojf_file.name}!")
                print(f"Address: {address}")
                print(f"Management type: {row.get('Способ управления', '')}")
                print(f"Company: {row.get('Наименование организации, осуществляющей управление домом', '')}")
                print(f"OGRN: {row.get('ОГРН организации, осуществляющей управление домом', '')}")
                print(f"Houseguid: {row.get('Глобальный уникальный идентификатор дома по ФИАС', '')}")
                break

if not found:
    print("\n" + "=" * 80)
    print("NOT FOUND in any OJF file")
    print("=" * 80)

    # Try to find similar addresses
    print("\nSearching for similar addresses (Тольятти, Южное)...")
    for ojf_file in ojf_files[:1]:  # Check first file only
        with open(ojf_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            count = 0
            for row in reader:
                address = row.get('Адрес ОЖФ', '')
                if 'Тольятти' in address and 'Южное' in address:
                    print(f"  {address}")
                    count += 1
                    if count >= 5:
                        break
