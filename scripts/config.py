"""
Конфигурация подключения к базе данных и общие настройки
"""

import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Директория с данными
DATA_DIR = BASE_DIR / 'data' / 'regions'

# Настройки подключения к PostgreSQL
# ВАЖНО: Измените эти параметры на ваши реальные данные!
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'capital_repair_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '123456')
}

# Маппинг кодов регионов на папки
REGION_MAPPING = {
    '02': {'code': '02', 'name': 'Республика Башкортостан', 'folder': '02_bashkortostan'},
    '12': {'code': '12', 'name': 'Республика Марий Эл', 'folder': '12_mariy-el'},
    '13': {'code': '13', 'name': 'Республика Мордовия', 'folder': '13_mordoviya'},
    '16': {'code': '16', 'name': 'Республика Татарстан', 'folder': '16_tatarstan'},
    '18': {'code': '18', 'name': 'Удмуртская Республика', 'folder': '18_udmurtiya'},
    '21': {'code': '21', 'name': 'Чувашская Республика', 'folder': '21_chuvashiya'},
    '43': {'code': '43', 'name': 'Кировская область', 'folder': '43_kirov'},
    '52': {'code': '52', 'name': 'Нижегородская область', 'folder': '52_nizhniy-novgorod'},
    '56': {'code': '56', 'name': 'Оренбургская область', 'folder': '56_orenburg'},
    '58': {'code': '58', 'name': 'Пензенская область', 'folder': '58_penza'},
    '59': {'code': '59', 'name': 'Пермский край', 'folder': '59_perm'},
    '63': {'code': '63', 'name': 'Самарская область', 'folder': '63_samara'},
    '64': {'code': '64', 'name': 'Саратовская область', 'folder': '64_saratov'},
    '73': {'code': '73', 'name': 'Ульяновская область', 'folder': '73_ulyanovsk'}
}

# Маппинг способов формирования фонда на коды
SPEC_ACCOUNT_MAPPING = {
    'Специальный счет, владельцем которого является управляющая компания': 'UK',
    'Специальный счет, владельцем которого является товарищество собственников жилья': 'TSJ',
    'Специальный счет, владельцем которого является жилищно-строительный кооператив': 'JSK',
    'Специальный счет, владельцем которого является региональный оператор': 'REGOP',
    'Счет регионального оператора': 'REGOP'
}

# Настройки логирования
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
