# Развертывание проекта на Timeweb Cloud

## Информация о сервере
- **IP**: 62.113.36.101
- **ОС**: Ubuntu/Debian (рекомендуется)
- **Требования**: PostgreSQL 14+, Python 3.10+

## Шаг 1: Подключение к серверу

```bash
ssh root@62.113.36.101
```

## Шаг 2: Установка необходимого ПО

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка PostgreSQL
apt install -y postgresql postgresql-contrib

# Установка Python и pip
apt install -y python3 python3-pip python3-venv

# Установка git (если нужно)
apt install -y git
```

## Шаг 3: Настройка PostgreSQL

```bash
# Переключение на пользователя postgres
sudo -u postgres psql

# Создание базы данных и пользователя
CREATE DATABASE capital_repair;
CREATE USER cr_user WITH PASSWORD 'ваш_пароль_здесь';
GRANT ALL PRIVILEGES ON DATABASE capital_repair TO cr_user;
\q
```

Настройка доступа в `/etc/postgresql/*/main/pg_hba.conf`:
```
# Добавить строку для локального доступа
local   capital_repair    cr_user                                 md5
host    capital_repair    cr_user    127.0.0.1/32                 md5
```

Перезапуск PostgreSQL:
```bash
systemctl restart postgresql
```

## Шаг 4: Загрузка файлов проекта

### Вариант A: Через SCP (с локального ПК)

```bash
# Создать архив проекта (без больших данных)
cd c:\Users\makar\Desktop\Region_parsing
tar -czf project_core.tar.gz database/ scripts/ requirements.txt

# Загрузить на сервер
scp project_core.tar.gz root@62.113.36.101:/opt/

# На сервере распаковать
ssh root@62.113.36.101
cd /opt
tar -xzf project_core.tar.gz
mv Region_parsing capital_repair
```

### Вариант B: Загрузка данных отдельно

Данные CSV/Excel слишком большие для прямой загрузки. Рекомендуется:

1. **Малый набор (только Татарстан)** - для тестирования:
```bash
# Создать архив только с данными Татарстана
tar -czf tatarstan_data.tar.gz \
  data/regions/16_tatarstan/ \
  "Реестр поставщиков информации от  2026-02-01.xlsx"

# Загрузить на сервер
scp tatarstan_data.tar.gz root@62.113.36.101:/opt/capital_repair/
```

2. **Полный набор (все регионы)** - для production:
```bash
# Загрузить полный архив данных
scp "Сведения_об_объектах_жилищного_фонда_на_25-01-2026.tar.gz" \
    root@62.113.36.101:/opt/capital_repair/data/

# Загрузить OJF данные
tar -czf ojf_full.tar.gz data/ojf_data/
scp ojf_full.tar.gz root@62.113.36.101:/opt/capital_repair/data/
```

## Шаг 5: Настройка проекта на сервере

```bash
cd /opt/capital_repair

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать конфигурационный файл
cat > scripts/.env <<EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_repair
DB_USER=cr_user
DB_PASSWORD=ваш_пароль_здесь
EOF

# Обновить config.py для чтения из .env
```

## Шаг 6: Создание схемы БД

```bash
# Выполнить миграции
cd /opt/capital_repair
export PGPASSWORD='ваш_пароль_здесь'

psql -h localhost -U cr_user -d capital_repair < database/001_initial_schema.sql
psql -h localhost -U cr_user -d capital_repair < database/002_views_and_data.sql

unset PGPASSWORD
```

## Шаг 7: Импорт данных

### Быстрый тест (только Татарстан)

```bash
cd /opt/capital_repair
source venv/bin/activate

# Импорт CSV данных (КР 1.1, 1.2, 1.3)
cd scripts
python import_csv.py --region 16

# Импорт OJF (связь дом-УК)
python import_ojf.py --file "../data/ojf_data/Сведения по ОЖФ Татарстан Респ на 25-01-2026_1.csv"
python import_ojf.py --file "../data/ojf_data/Сведения по ОЖФ Татарстан Респ на 25-01-2026_2.csv"

# Импорт контактов УК
python import_registry.py --file "../Реестр поставщиков информации от  2026-02-01.xlsx"
```

### Полный импорт (все регионы ПФО)

```bash
# Импорт всех регионов
for region in 02 12 13 16 18 21 43 52 56 58 59 63 64 73; do
    echo "Importing region $region..."
    python import_csv.py --region $region
done

# Импорт всех OJF файлов
find ../data/ojf_data -name "*.csv" -exec python import_ojf.py --file {} \;

# Импорт Registry
python import_registry.py
```

## Шаг 8: Проверка данных

```bash
cd /opt/capital_repair/scripts
python -c "
import psycopg2
from config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM buildings')
print(f'Buildings: {cur.fetchone()[0]:,}')

cur.execute('SELECT COUNT(*) FROM management_companies')
print(f'Management companies: {cur.fetchone()[0]:,}')

cur.execute('SELECT COUNT(*) FROM management_companies WHERE phone IS NOT NULL')
print(f'With contacts: {cur.fetchone()[0]:,}')

cur.close()
conn.close()
"
```

## Шаг 9: Настройка автоматического обновления (опционально)

Создать cron job для ежедневного обновления:

```bash
crontab -e

# Добавить строку для обновления в 3:00 AM каждый день
0 3 * * * cd /opt/capital_repair/scripts && /opt/capital_repair/venv/bin/python import_registry.py >> /var/log/cr_update.log 2>&1
```

## Шаг 10: Настройка доступа к БД извне (если нужно)

Для доступа к PostgreSQL с других серверов:

1. Редактировать `/etc/postgresql/*/main/postgresql.conf`:
```
listen_addresses = '*'
```

2. Редактировать `/etc/postgresql/*/main/pg_hba.conf`:
```
# Добавить IP адрес клиента
host    capital_repair    cr_user    ВАШ_IP/32    md5
```

3. Перезапустить PostgreSQL:
```bash
systemctl restart postgresql
```

4. Открыть порт в firewall:
```bash
ufw allow 5432/tcp
```

## Безопасность

1. **Изменить пароль PostgreSQL** на сложный
2. **Настроить firewall** (ufw) для доступа только с нужных IP
3. **Создать бэкапы**:
```bash
# Ежедневный бэкап БД
pg_dump -U cr_user -h localhost capital_repair | gzip > /backups/cr_$(date +%Y%m%d).sql.gz
```

## Производительность

Для больших объемов данных:

```bash
# Настройка PostgreSQL в /etc/postgresql/*/main/postgresql.conf
shared_buffers = 2GB
work_mem = 64MB
maintenance_work_mem = 512MB
effective_cache_size = 6GB
```

## Мониторинг

```bash
# Проверка статуса PostgreSQL
systemctl status postgresql

# Проверка размера БД
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('capital_repair'));"

# Проверка активных подключений
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='capital_repair';"
```

## Следующие шаги

После успешного развертывания:
1. Разработать веб-интерфейс (Flask/Django)
2. Настроить REST API для доступа к данным
3. Создать дашборды для аналитики
4. Интегрировать с CRM системой
