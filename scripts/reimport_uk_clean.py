# -*- coding: utf-8 -*-
"""
Полный переимпорт УК с очисткой старых данных
"""
import glob
import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.config import DB_CONFIG
from scripts.import_uk_from_ojf import import_uk_from_ojf
from scripts.import_contacts_from_registry import import_contacts

def main():
    """Переимпорт УК с нуля"""

    print("="*80)
    print("ПОЛНЫЙ ПЕРЕИМПОРТ УК И СВЯЗЕЙ")
    print("="*80)

    # Шаг 1: Очистка старых данных УК
    print("\n[1/3] Очистка старых данных УК и связей...")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Удаляем только УК и связи (дома и лифты оставляем!)
    cur.execute("DELETE FROM buildings_management")
    print("   [OK] Удалены связи дом-УК")

    cur.execute("DELETE FROM management_companies")
    print("   [OK] Удалены УК")

    conn.commit()
    cur.close()
    conn.close()

    # Шаг 2: Импорт УК из ojf_data
    print("\n[2/3] Импорт УК из файлов ОЖФ...")

    # Находим все файлы ОЖФ
    ojf_files = sorted(glob.glob('data/ojf_data/*.csv'))

    if not ojf_files:
        print("   [WARNING] Файлы ОЖФ не найдены в data/ojf_data/")
        return

    print(f"   Найдено файлов: {len(ojf_files)}")

    # Группируем по регионам для отображения
    current_region = None

    for ojf_file in ojf_files:
        filename = ojf_file.split('\\')[-1] if '\\' in ojf_file else ojf_file.split('/')[-1]
        region_name = filename.split(' на ')[0].replace('Сведения по ОЖФ ', '')

        if region_name != current_region:
            print(f"\n   [REGION] {region_name}")
            current_region = region_name

        try:
            # Краткий вывод
            file_num = filename.split('_')[-1].replace('.csv', '') if '_' in filename else '1'
            print(f"      Файл {file_num}...", end=' ')

            # Импорт
            import_uk_from_ojf(ojf_file)
            print("OK")

        except Exception as e:
            print(f"ERROR: {e}")

    # Шаг 3: Импорт контактов
    print("\n[3/3] Импорт контактов из реестра...")

    try:
        import_contacts()
    except Exception as e:
        print(f"   [WARNING] Ошибка импорта контактов: {e}")

    # Финальная статистика
    print("\n" + "="*80)
    print("ФИНАЛЬНАЯ СТАТИСТИКА")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Основные показатели
    cur.execute("SELECT COUNT(*) FROM buildings")
    buildings_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM management_companies")
    companies_count = cur.fetchone()[0]

    cur.execute("""
        SELECT
            COUNT(DISTINCT building_id) as buildings_with_uk,
            COUNT(*) as total_links
        FROM buildings_management
    """)
    links = cur.fetchone()
    buildings_with_uk = links[0]
    total_links = links[1]

    cur.execute("""
        SELECT
            COUNT(phone) as with_phone,
            COUNT(email) as with_email
        FROM management_companies
    """)
    contacts = cur.fetchone()

    coverage = buildings_with_uk * 100 / buildings_count if buildings_count > 0 else 0

    print(f"\n[OK] Дома:          {buildings_count:,}")
    print(f"[OK] УК:            {companies_count:,}")
    print(f"[OK] Связей дом-УК: {total_links:,}")
    print(f"[OK] Домов с УК:    {buildings_with_uk:,} ({coverage:.1f}%)")
    print(f"[OK] УК с телефон:  {contacts[0]:,} ({contacts[0]*100/companies_count:.1f}%)")
    print(f"[OK] УК с email:    {contacts[1]:,} ({contacts[1]*100/companies_count:.1f}%)")

    cur.close()
    conn.close()

    print("\n" + "="*80)
    print("[OK] ПЕРЕИМПОРТ ЗАВЕРШЕН")
    print("="*80)
    print("\nОбновите страницу в браузере (F5)")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
