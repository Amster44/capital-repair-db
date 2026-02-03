# Локальная настройка (MySQL)

## 1. Установка MySQL

### Windows:
```bash
# Скачать с https://dev.mysql.com/downloads/installer/
# Или через Chocolatey:
choco install mysql

# Запустить MySQL
net start mysql
```

### Linux:
```bash
sudo apt install mysql-server
sudo systemctl start mysql
```

## 2. Создание базы

```bash
mysql -u root -p

# В MySQL консоли:
CREATE DATABASE capital_repair_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'repair_user'@'localhost' IDENTIFIED BY 'repair_pass';
GRANT ALL PRIVILEGES ON capital_repair_db.* TO 'repair_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 3. Применение схемы

```bash
mysql -u repair_user -p capital_repair_db < database/mysql_schema.sql
```

## 4. Настройка Python окружения

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux

pip install pandas mysql-connector-python
```

## 5. Настройка подключения

Создайте `scripts/config_local.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'repair_user',
    'password': 'repair_pass',
    'database': 'capital_repair_db',
    'charset': 'utf8mb4'
}
```

## 6. Схлопывание ОЖФ данных

Если у вас есть данные ОЖФ локально:

```bash
python scripts/collapse_ozhf_houses.py \
  --ozhf_dir "data/ojf_data" \
  --out "data/ozhf_collapsed.csv"
```

Это создаст файл с домами (1 дом = 1 строка с ОГРН).

## 7. Импорт данных

Создайте скрипты импорта, которые будут:

1. Импортировать регионы
2. Импортировать дома из CSV
3. Импортировать лифты из CSV
4. Связать дома с УК через схлопнутый ОЖФ (по houseguid + ogrn)
5. Обогатить УК из реестра (по ОГРН)

## Структура импорта:

```
CSV домов (houseguid, адрес, баланс)
         ↓
     buildings
         ↓
ОЖФ схлопнутый (houseguid → ogrn_uo)
         ↓
  buildings.ogrn_uo заполнен
         ↓
Реестр УК (ogrn → контакты)
         ↓
  management_companies
         ↓
  buildings.management_company_id
```

## Проверка:

```sql
-- Количество домов
SELECT COUNT(*) FROM buildings;

-- Дома с ОГРН
SELECT COUNT(*) FROM buildings WHERE ogrn_uo IS NOT NULL;

-- Дома со связанными УК
SELECT COUNT(*) FROM buildings WHERE management_company_id IS NOT NULL;

-- УК с контактами
SELECT COUNT(*) FROM management_companies WHERE phone IS NOT NULL;
```
