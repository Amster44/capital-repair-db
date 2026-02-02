# Скрипты для работы с базой данных

## Установка зависимостей

```bash
pip install -r ../requirements.txt
```

## Настройка подключения к БД

### Вариант 1: Переменные окружения

Создайте файл `.env` в корне проекта:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_repair_db
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### Вариант 2: Редактирование config.py

Откройте [config.py](config.py) и измените параметры `DB_CONFIG`.

---

## 1. Инициализация базы данных

### Создание БД в PostgreSQL

```bash
# Подключитесь к PostgreSQL
psql -U postgres

# Создайте базу данных
CREATE DATABASE capital_repair_db ENCODING 'UTF8';

# Выйдите
\q
```

### Выполнение миграций

```bash
# Выполните SQL скрипты миграций
psql -U postgres -d capital_repair_db -f ../database/001_initial_schema.sql
psql -U postgres -d capital_repair_db -f ../database/002_views_and_data.sql
```

После выполнения миграций у вас будет:
- ✅ Все таблицы созданы
- ✅ Индексы настроены
- ✅ Представления (views) работают
- ✅ Справочники заполнены (регионы, типы организаций, статусы)

---

## 2. Импорт данных из CSV

### 2.1. Импорт данных Татарстана (уже есть файлы)

```bash
# Импорт всех отчетов КР 1.1, 1.2, 1.3
python import_csv.py --region 16

# С очисткой старых данных
python import_csv.py --region 16 --clean

# Импорт только конкретного отчета
python import_csv.py --region 16 --kr 1.1   # Только дома
python import_csv.py --region 16 --kr 1.2   # Только лифты и элементы
python import_csv.py --region 16 --kr 1.3   # Только услуги
```

### 2.2. Импорт других регионов

Сначала скачайте CSV файлы для региона с https://фонд-кр.рф/opendata и поместите их в соответствующую папку:

```bash
# Например, для Башкортостана (код 02)
# 1. Скачайте файлы:
#    - export-kr1_1-02-YYYYMMDD.csv
#    - export-kr1_2-02-YYYYMMDD.csv
#    - export-kr1_3-02-YYYYMMDD.csv
#
# 2. Поместите в папку: data/regions/02_bashkortostan/
#
# 3. Запустите импорт:
python import_csv.py --region 02
```

### 2.3. Импорт всех регионов

```bash
# ВНИМАНИЕ: Это займет много времени!
# Убедитесь что все CSV файлы загружены в папки регионов
python import_csv.py --region all
```

### Примеры использования

```bash
# 1. Первый импорт Татарстана
python import_csv.py --region 16 --clean

# 2. Обновление только домов (КР 1.1)
python import_csv.py --region 16 --kr 1.1 --clean

# 3. Импорт нескольких регионов
python import_csv.py --region 16
python import_csv.py --region 63  # Самарская область
python import_csv.py --region 52  # Нижегородская область
```

### Логи импорта

Скрипт выводит подробные логи:
```
INFO - Подключение к БД успешно: capital_repair_db
INFO - === Начало импорта региона: Республика Татарстан ===
INFO - Импорт КР 1.1 из export-kr1_1-16-20260201.csv
INFO - Обработано 1000 строк...
INFO - Обработано 2000 строк...
...
INFO - КР 1.1 импортирован: 17941 записей
INFO - Импорт КР 1.2 из export-kr1_2-16-20260201.csv
INFO - КР 1.2 импортирован: 198060 записей
INFO - Импорт КР 1.3 из export-kr1_3-16-20260201.csv
INFO - КР 1.3 импортирован: 182158 записей
INFO - === Импорт завершен успешно ===
```

---

## 3. Проверка импортированных данных

### SQL запросы для проверки

```sql
-- Количество домов по регионам
SELECT r.region_name, COUNT(b.id) as buildings_count
FROM regions r
LEFT JOIN buildings b ON r.id = b.region_id
GROUP BY r.region_name
ORDER BY buildings_count DESC;

-- Дома со спецсчетами и лифтами
SELECT
    COUNT(DISTINCT b.id) as buildings_with_spec_account,
    COUNT(l.id) as total_lifts,
    SUM(b.overhaul_funds_balance) as total_balance
FROM buildings b
LEFT JOIN lifts l ON b.id = l.building_id
WHERE b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK');

-- Топ-10 домов с максимальным балансом
SELECT
    address,
    overhaul_funds_balance,
    spec_account_owner_type,
    COUNT(l.id) as lifts_count
FROM buildings b
LEFT JOIN lifts l ON b.id = l.building_id
WHERE spec_account_owner_type IN ('UK', 'TSJ', 'JSK')
GROUP BY b.id, b.address, b.overhaul_funds_balance, b.spec_account_owner_type
ORDER BY overhaul_funds_balance DESC
LIMIT 10;

-- Целевые дома (через view)
SELECT * FROM v_target_buildings
WHERE priority = 'HIGH'
LIMIT 20;
```

---

## 4. Парсинг данных об УК/ТСЖ (будет создан далее)

```bash
# Парсинг контактов УК для Татарстана
python parse_uk.py --region 16

# Парсинг для всех регионов
python parse_uk.py --region all
```

---

## Решение проблем

### Ошибка подключения к БД

```
psycopg2.OperationalError: FATAL: password authentication failed
```

**Решение:** Проверьте параметры подключения в `config.py` или `.env`

### Файлы CSV не найдены

```
FileNotFoundError: Папка региона не найдена
```

**Решение:** Убедитесь что CSV файлы находятся в правильной папке:
- `data/regions/16_tatarstan/` для Татарстана
- `data/regions/02_bashkortostan/` для Башкортостана
- и т.д.

### Ошибки в данных CSV

```
WARNING - Ошибка в строке 1234: ...
```

**Это нормально!** Скрипт пропускает некорректные строки и продолжает импорт.

### Дубликаты данных

Скрипт использует `ON CONFLICT` для обработки дубликатов:
- При повторном импорте данные **обновляются**
- Используйте `--clean` для полной очистки перед импортом

---

## Полезные команды PostgreSQL

```bash
# Подключение к БД
psql -U postgres -d capital_repair_db

# Список таблиц
\dt

# Количество записей в таблице
SELECT COUNT(*) FROM buildings;

# Размер БД
SELECT pg_size_pretty(pg_database_size('capital_repair_db'));

# Бэкап БД
pg_dump -U postgres -d capital_repair_db > backup.sql

# Восстановление из бэкапа
psql -U postgres -d capital_repair_db < backup.sql
```

---

## Следующие шаги

1. ✅ Импортируйте данные Татарстана
2. ⏳ Проверьте данные через SQL запросы
3. ⏳ Запустите парсер УК для получения контактов
4. ⏳ Настройте веб-интерфейс для работы команды

---

## Структура скриптов

```
scripts/
├── config.py           # Конфигурация БД и общие настройки
├── import_csv.py       # Импорт данных из CSV
├── parse_uk.py         # Парсинг данных об УК (будет создан)
└── README.md           # Эта инструкция
```
