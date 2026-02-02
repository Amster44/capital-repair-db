"""
Скрипт импорта данных из CSV файлов в PostgreSQL

Использование:
    python import_csv.py --region 16                    # Импорт только Татарстана
    python import_csv.py --region all                   # Импорт всех регионов
    python import_csv.py --region 16 --clean            # Очистка и импорт
    python import_csv.py --region 16 --kr 1.1           # Импорт только КР 1.1
"""

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2.extensions import connection as Connection

from config import DB_CONFIG, DATA_DIR, REGION_MAPPING, SPEC_ACCOUNT_MAPPING, LOG_FORMAT, LOG_LEVEL

# Настройка логирования
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class CSVImporter:
    """Класс для импорта CSV файлов в PostgreSQL"""

    def __init__(self, region_code: str, clean: bool = False):
        self.region_code = region_code
        self.clean = clean
        self.conn: Optional[Connection] = None
        self.region_id: Optional[int] = None

        if region_code not in REGION_MAPPING:
            raise ValueError(f"Неизвестный код региона: {region_code}")

        self.region_info = REGION_MAPPING[region_code]
        self.region_folder = DATA_DIR / self.region_info['folder']

        if not self.region_folder.exists():
            raise FileNotFoundError(f"Папка региона не найдена: {self.region_folder}")

    def connect(self):
        """Подключение к PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            logger.info(f"Подключение к БД успешно: {DB_CONFIG['database']}")
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    def disconnect(self):
        """Отключение от БД"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с БД закрыто")

    def get_region_id(self) -> int:
        """Получить ID региона из БД"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM regions WHERE region_code = %s", (self.region_code,))
            result = cur.fetchone()
            if not result:
                raise ValueError(f"Регион {self.region_code} не найден в БД. Выполните миграции!")
            return result[0]

    def find_csv_files(self) -> Dict[str, Optional[Path]]:
        """Найти CSV файлы в папке региона"""
        files = {
            'kr1_1': None,
            'kr1_2': None,
            'kr1_3': None
        }

        for file in self.region_folder.glob('*.csv'):
            filename = file.name.lower()
            if 'kr1_1' in filename or 'kr1-1' in filename:
                files['kr1_1'] = file
            elif 'kr1_2' in filename or 'kr1-2' in filename:
                files['kr1_2'] = file
            elif 'kr1_3' in filename or 'kr1-3' in filename:
                files['kr1_3'] = file

        return files

    def clean_data(self, kr_type: Optional[str] = None):
        """Очистка данных региона перед импортом"""
        with self.conn.cursor() as cur:
            if kr_type is None or kr_type == '1.1':
                logger.info(f"Удаление домов региона {self.region_code}...")
                cur.execute("DELETE FROM buildings WHERE region_id = %s", (self.region_id,))
                logger.info(f"Удалено {cur.rowcount} домов")

            if kr_type is None or kr_type == '1.2':
                logger.info(f"Удаление конструктивных элементов...")
                cur.execute("""
                    DELETE FROM construction_elements WHERE building_id IN (
                        SELECT id FROM buildings WHERE region_id = %s
                    )
                """, (self.region_id,))
                logger.info(f"Удалено {cur.rowcount} элементов")

                cur.execute("""
                    DELETE FROM lifts WHERE building_id IN (
                        SELECT id FROM buildings WHERE region_id = %s
                    )
                """, (self.region_id,))
                logger.info(f"Удалено {cur.rowcount} лифтов")

            if kr_type is None or kr_type == '1.3':
                logger.info(f"Удаление услуг...")
                cur.execute("""
                    DELETE FROM services WHERE building_id IN (
                        SELECT id FROM buildings WHERE region_id = %s
                    )
                """, (self.region_id,))
                logger.info(f"Удалено {cur.rowcount} услуг")

            self.conn.commit()

    def parse_decimal(self, value: str) -> Optional[float]:
        """Парсинг decimal значений (запятая → точка, убираем пробелы)"""
        if not value or value.strip() == '':
            return None
        try:
            # Убираем пробелы (разделители тысяч) и заменяем запятую на точку
            cleaned = value.replace(' ', '').replace(',', '.').strip()
            return float(cleaned)
        except ValueError:
            return None

    def parse_int(self, value: str) -> Optional[int]:
        """Парсинг integer значений"""
        if not value or value.strip() == '':
            return None
        try:
            return int(float(value.replace(',', '.')))
        except ValueError:
            return None

    def parse_date(self, value: str) -> Optional[str]:
        """Парсинг дат"""
        if not value or value.strip() == '':
            return None
        try:
            # Пробуем разные форматы
            for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%Y']:
                try:
                    dt = datetime.strptime(value.strip(), fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def parse_uuid(self, value: str) -> Optional[str]:
        """Парсинг UUID"""
        if not value or value.strip() == '':
            return None
        value = value.strip()
        if len(value) == 36:  # UUID формат
            return value
        return None

    def get_municipality_id(self, oktmo_code: str, name: str) -> Optional[int]:
        """Получить или создать муниципалитет"""
        if not oktmo_code and not name:
            return None

        with self.conn.cursor() as cur:
            # Сначала пробуем найти по ОКТМО
            if oktmo_code:
                cur.execute(
                    "SELECT id FROM municipalities WHERE oktmo_code = %s AND region_id = %s",
                    (oktmo_code, self.region_id)
                )
                result = cur.fetchone()
                if result:
                    return result[0]

            # Если не нашли, создаем новый
            cur.execute(
                """
                INSERT INTO municipalities (region_id, oktmo_code, name)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (self.region_id, oktmo_code or None, name or 'Не указано')
            )
            result = cur.fetchone()
            if result:
                return result[0]

            # Если был конфликт, пытаемся найти по имени
            cur.execute(
                "SELECT id FROM municipalities WHERE name = %s AND region_id = %s",
                (name, self.region_id)
            )
            result = cur.fetchone()
            return result[0] if result else None

    def import_kr1_1(self, file_path: Path) -> int:
        """Импорт КР 1.1 - Многоквартирные дома"""
        logger.info(f"Импорт КР 1.1 из {file_path.name}")

        buildings_data = []
        municipalities_cache = {}

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Определяем тип спецсчета
                    money_way = row.get('money_collecting_way', '').strip()
                    spec_type = SPEC_ACCOUNT_MAPPING.get(money_way, 'REGOP' if 'регионального оператора' in money_way.lower() else None)

                    # Получаем municipality_id
                    oktmo = row.get('mun_obr_oktmo', '').strip()
                    mun_name = row.get('mun_obr', '').strip()
                    cache_key = f"{oktmo}_{mun_name}"

                    if cache_key not in municipalities_cache:
                        municipalities_cache[cache_key] = self.get_municipality_id(oktmo, mun_name)

                    municipality_id = municipalities_cache[cache_key]

                    building = (
                        self.region_id,                                              # 1
                        municipality_id,                                             # 2
                        row.get('mkd_code', '').strip() or None,                    # 3
                        self.parse_uuid(row.get('houseguid', '')),                  # 4
                        row.get('house_id', '').strip() or None,                    # 5
                        row.get('address', '').strip(),                             # 6
                        self.parse_int(row.get('commission_year', '')),             # 7
                        self.parse_decimal(row.get('total_sq', '')),                # 8
                        self.parse_int(row.get('total_rooms_amount', '')),          # 9
                        self.parse_int(row.get('living_rooms_amount', '')),         # 10
                        self.parse_decimal(row.get('total_rooms_sq', '')),          # 11
                        self.parse_decimal(row.get('living_rooms_sq', '')),         # 12
                        self.parse_int(row.get('total_ppl', '')),                   # 13
                        self.parse_int(row.get('number_floors_max', '')),           # 14
                        money_way or None,                                           # 15
                        spec_type,                                                   # 16
                        self.parse_decimal(row.get('money_ppl_collected', '')),     # 17
                        self.parse_decimal(row.get('money_ppl_collected_debts', '')),  # 18
                        self.parse_decimal(row.get('overhaul_funds_spent_all', '')),   # 19
                        self.parse_decimal(row.get('overhaul_funds_spent_subsidy', '')), # 20
                        self.parse_decimal(row.get('overhaul_fund_spent_other', '')),    # 21
                        self.parse_decimal(row.get('overhaul_funds_balance', '')),       # 22
                        self.parse_decimal(row.get('owners_payment', '')),               # 23
                        row.get('energy_efficiency', '').strip() or None,                # 24
                        row.get('architectural_monument_category', '').strip() or None,  # 25
                        self.parse_date(row.get('alarm_document_date', '')),             # 26
                        self.parse_date(row.get('exclude_date_from_program', '')),       # 27
                        self.parse_date(row.get('inclusion_date_to_program', '')),       # 28
                        row.get('comment', '').strip() or None,                          # 29
                        self.parse_date(row.get('update_date_of_information', '')),      # 30
                        self.parse_date(row.get('money_ppl_collected_date', '')),        # 31
                        self.parse_date(row.get('last_update', '')),                     # 32
                        self.region_info['name']                                         # 33 region (текстовое название)
                    )

                    buildings_data.append(building)

                    if len(buildings_data) >= 1000:
                        self._batch_insert_buildings(buildings_data)
                        buildings_data = []
                        logger.info(f"Обработано {row_num} строк...")

                except Exception as e:
                    logger.warning(f"Ошибка в строке {row_num}: {e}")
                    continue

        # Вставка оставшихся
        if buildings_data:
            self._batch_insert_buildings(buildings_data)

        self.conn.commit()
        logger.info(f"КР 1.1 импортирован: {row_num - 1} записей")
        return row_num - 1

    def _batch_insert_buildings(self, buildings_data: List[tuple]):
        """Пакетная вставка домов"""
        with self.conn.cursor() as cur:
            execute_batch(cur, """
                INSERT INTO buildings (
                    region_id, municipality_id, mkd_code, houseguid, house_id, address,
                    commission_year, total_sq, total_rooms_amount, living_rooms_amount,
                    total_rooms_sq, living_rooms_sq, total_ppl, number_floors_max,
                    money_collecting_way, spec_account_owner_type,
                    money_ppl_collected, money_ppl_collected_debts,
                    overhaul_funds_spent_all, overhaul_funds_spent_subsidy,
                    overhaul_fund_spent_other, overhaul_funds_balance, owners_payment,
                    energy_efficiency, architectural_monument_category,
                    alarm_document_date, exclude_date_from_program,
                    inclusion_date_to_program, comment,
                    update_date_of_information, money_ppl_collected_date, last_update,
                    region
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (region_id, mkd_code) DO UPDATE SET
                    houseguid = EXCLUDED.houseguid,
                    address = EXCLUDED.address,
                    overhaul_funds_balance = EXCLUDED.overhaul_funds_balance,
                    last_update = EXCLUDED.last_update,
                    region = EXCLUDED.region
            """, buildings_data)

    def import_kr1_2(self, file_path: Path) -> int:
        """Импорт КР 1.2 - Конструктивные элементы и лифты"""
        logger.info(f"Импорт КР 1.2 из {file_path.name}")

        # Создаем кэш building_id по mkd_code
        building_cache = {}
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT mkd_code, id FROM buildings
                WHERE region_id = %s AND mkd_code IS NOT NULL
            """, (self.region_id,))
            for mkd_code, building_id in cur.fetchall():
                building_cache[mkd_code] = building_id

        lifts_data = []
        elements_data = []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')

            for row_num, row in enumerate(reader, start=2):
                try:
                    mkd_code = row.get('mkd_code', '').strip()
                    building_id = building_cache.get(mkd_code)

                    if not building_id:
                        continue

                    element_type = row.get('construction_element_type', '').strip()

                    # Если это лифт
                    if 'лифт' in element_type.lower():
                        commissioning_date_str = self.parse_date(row.get('commissioning_date', ''))
                        decommissioning_date_str = row.get('decommissioning_date', '').strip()

                        # Если срок вывода пустой, рассчитываем его: срок ввода + 25 лет
                        if not decommissioning_date_str and commissioning_date_str:
                            try:
                                # Парсим дату ввода в эксплуатацию
                                comm_dt = datetime.strptime(commissioning_date_str, '%Y-%m-%d')
                                # Добавляем 25 лет
                                decomm_dt = comm_dt + timedelta(days=365*25)
                                # Конвертируем обратно в строку
                                decommissioning_date = decomm_dt.strftime('%Y-%m-%d')
                            except (ValueError, TypeError):
                                decommissioning_date = None
                        else:
                            decommissioning_date = self.parse_date(decommissioning_date_str)

                        lift = (
                            building_id,
                            row.get('construction_element_code', '').strip() or None,
                            row.get('lift_type', '').strip() or None,
                            self.parse_int(row.get('stops_count', '')),
                            commissioning_date_str,
                            decommissioning_date,
                            self.parse_date(row.get('last_update', ''))
                        )
                        lifts_data.append(lift)
                    else:
                        # Прочие конструктивные элементы
                        element = (
                            building_id,
                            row.get('construction_element_code', '').strip() or None,
                            element_type or None,
                            row.get('system_type', '').strip() or None,
                            row.get('roof_type', '').strip() or None,
                            self.parse_decimal(row.get('roofing_area', '')),
                            self.parse_decimal(row.get('basement_area', '')),
                            row.get('facade_type', '').strip() or None,
                            self.parse_decimal(row.get('facade_area', '')),
                            row.get('foundation_type', '').strip() or None,
                            row.get('wall_material', '').strip() or None,
                            row.get('comment', '').strip() or None,
                            self.parse_date(row.get('last_update', ''))
                        )
                        elements_data.append(element)

                    if len(lifts_data) + len(elements_data) >= 1000:
                        self._batch_insert_lifts_and_elements(lifts_data, elements_data)
                        lifts_data = []
                        elements_data = []
                        logger.info(f"Обработано {row_num} строк...")

                except Exception as e:
                    logger.warning(f"Ошибка в строке {row_num}: {e}")
                    continue

        # Вставка оставшихся
        if lifts_data or elements_data:
            self._batch_insert_lifts_and_elements(lifts_data, elements_data)

        self.conn.commit()
        logger.info(f"КР 1.2 импортирован: {row_num - 1} записей")
        return row_num - 1

    def _batch_insert_lifts_and_elements(self, lifts_data: List[tuple], elements_data: List[tuple]):
        """Пакетная вставка лифтов и элементов"""
        with self.conn.cursor() as cur:
            if lifts_data:
                execute_batch(cur, """
                    INSERT INTO lifts (
                        building_id, element_code, lift_type, stops_count,
                        commissioning_date, decommissioning_date, last_update
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (building_id, element_code) DO UPDATE SET
                        commissioning_date = EXCLUDED.commissioning_date,
                        decommissioning_date = EXCLUDED.decommissioning_date
                """, lifts_data)

            if elements_data:
                execute_batch(cur, """
                    INSERT INTO construction_elements (
                        building_id, element_code, element_type, system_type,
                        roof_type, roofing_area, basement_area,
                        facade_type, facade_area, foundation_type, wall_material,
                        comment, last_update
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, elements_data)

    def import_kr1_3(self, file_path: Path) -> int:
        """Импорт КР 1.3 - Услуги и работы"""
        logger.info(f"Импорт КР 1.3 из {file_path.name}")

        # Создаем кэш building_id по mkd_code
        building_cache = {}
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT mkd_code, id FROM buildings
                WHERE region_id = %s AND mkd_code IS NOT NULL
            """, (self.region_id,))
            for mkd_code, building_id in cur.fetchall():
                building_cache[mkd_code] = building_id

        services_data = []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')

            for row_num, row in enumerate(reader, start=2):
                try:
                    mkd_code = row.get('mkd_code', '').strip()
                    building_id = building_cache.get(mkd_code)

                    if not building_id:
                        continue

                    service = (
                        building_id,
                        row.get('construction_element_code', '').strip() or None,
                        row.get('service_code', '').strip() or None,
                        row.get('service_type', '').strip() or None,
                        row.get('event_type', '').strip() or None,
                        row.get('work_code', '').strip() or None,
                        self.parse_int(row.get('service_date', '')),
                        self.parse_int(row.get('service_date_by_plan', '')),
                        self.parse_date(row.get('date_contract_concluded', '')),
                        self.parse_date(row.get('contract_date_services_finished', '')),
                        self.parse_date(row.get('fact_date_services_finished', '')),
                        self.parse_decimal(row.get('plan_service_cost_kpkr', '')),
                        self.parse_decimal(row.get('plan_service_cost_conclusion_contract', '')),
                        self.parse_decimal(row.get('plan_service_cost_contract', '')),
                        row.get('measure', '').strip() or None,
                        self.parse_decimal(row.get('service_scope', '')),
                        self.parse_int(row.get('lifts_count', '')),
                        row.get('contractor_name', '').strip() or None,
                        row.get('contractor_inn', '').strip() or None,
                        self.parse_date(row.get('last_update', ''))
                    )
                    services_data.append(service)

                    if len(services_data) >= 1000:
                        self._batch_insert_services(services_data)
                        services_data = []
                        logger.info(f"Обработано {row_num} строк...")

                except Exception as e:
                    logger.warning(f"Ошибка в строке {row_num}: {e}")
                    continue

        # Вставка оставшихся
        if services_data:
            self._batch_insert_services(services_data)

        self.conn.commit()
        logger.info(f"КР 1.3 импортирован: {row_num - 1} записей")
        return row_num - 1

    def _batch_insert_services(self, services_data: List[tuple]):
        """Пакетная вставка услуг"""
        with self.conn.cursor() as cur:
            execute_batch(cur, """
                INSERT INTO services (
                    building_id, element_code, service_code, service_type, event_type,
                    work_code, service_date, service_date_by_plan,
                    date_contract_concluded, contract_date_services_finished,
                    fact_date_services_finished, plan_service_cost_kpkr,
                    plan_service_cost_conclusion_contract, plan_service_cost_contract,
                    measure, service_scope, lifts_count, contractor_name,
                    contractor_inn, last_update
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT DO NOTHING
            """, services_data)

    def run(self, kr_type: Optional[str] = None):
        """Запуск импорта"""
        try:
            self.connect()
            self.region_id = self.get_region_id()

            logger.info(f"=== Начало импорта региона: {self.region_info['name']} ===")

            # Очистка данных если нужно
            if self.clean:
                self.clean_data(kr_type)

            # Поиск файлов
            files = self.find_csv_files()

            # Импорт в зависимости от kr_type
            if kr_type is None or kr_type == '1.1':
                if files['kr1_1']:
                    self.import_kr1_1(files['kr1_1'])
                else:
                    logger.warning("Файл КР 1.1 не найден")

            if kr_type is None or kr_type == '1.2':
                if files['kr1_2']:
                    self.import_kr1_2(files['kr1_2'])
                else:
                    logger.warning("Файл КР 1.2 не найден")

            if kr_type is None or kr_type == '1.3':
                if files['kr1_3']:
                    self.import_kr1_3(files['kr1_3'])
                else:
                    logger.warning("Файл КР 1.3 не найден")

            logger.info(f"=== Импорт завершен успешно ===")

        except Exception as e:
            logger.error(f"Ошибка импорта: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Импорт данных из CSV в PostgreSQL')
    parser.add_argument('--region', required=True, help='Код региона (например, 16) или "all"')
    parser.add_argument('--clean', action='store_true', help='Очистить данные перед импортом')
    parser.add_argument('--kr', choices=['1.1', '1.2', '1.3'], help='Импортировать только конкретный отчет')

    args = parser.parse_args()

    if args.region == 'all':
        regions = list(REGION_MAPPING.keys())
    else:
        regions = [args.region]

    for region_code in regions:
        try:
            importer = CSVImporter(region_code, clean=args.clean)
            importer.run(kr_type=args.kr)
        except Exception as e:
            logger.error(f"Ошибка импорта региона {region_code}: {e}")
            continue


if __name__ == '__main__':
    main()
