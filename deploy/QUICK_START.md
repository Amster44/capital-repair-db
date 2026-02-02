# Быстрое развертывание на сервере 62.113.36.101

## Шаг 1: Подключитесь к серверу и подготовьте окружение

Откройте PowerShell/CMD и выполните:

```bash
ssh root@62.113.36.101
# Введите пароль: j4eVZ-g@aPA2U6
```

После подключения выполните следующие команды на сервере:

```bash
# Установка необходимых пакетов
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git supervisor

# Установка Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Создание директории проекта
mkdir -p /opt/capital-repair-db
cd /opt/capital-repair-db

# Создание Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
pip install flask flask-cors psycopg2-binary pandas openpyxl gunicorn

# Настройка PostgreSQL
sudo -u postgres psql <<'EOF'
DROP DATABASE IF EXISTS capital_repair_db;
CREATE DATABASE capital_repair_db;
DROP USER IF EXISTS repair_user;
CREATE USER repair_user WITH PASSWORD 'repair_password_2026';
GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO repair_user;
\c capital_repair_db
GRANT ALL ON SCHEMA public TO repair_user;
EOF
```

Оставьте это окно открытым и откройте НОВОЕ окно PowerShell/CMD на вашем компьютере.

---

## Шаг 2: Загрузите файлы на сервер (из нового окна на вашем ПК)

```powershell
cd C:\Users\Usr146\Desktop\Capital_repair_db\capital-repair-db

# Загрузка основных файлов
scp -r scripts root@62.113.36.101:/opt/capital-repair-db/
scp -r app root@62.113.36.101:/opt/capital-repair-db/
scp -r frontend root@62.113.36.101:/opt/capital-repair-db/
scp -r deploy root@62.113.36.101:/opt/capital-repair-db/

# Загрузка конфигурации
scp deploy\config_production.py root@62.113.36.101:/opt/capital-repair-db/scripts/config.py
```

---

## Шаг 3: Разверните приложение (вернитесь в окно с сервером)

```bash
cd /opt/capital-repair-db
source venv/bin/activate

# Инициализация базы данных
python3 scripts/init_db.py

# Сборка фронтенда
cd frontend
npm install
npm run build
cd ..

# Настройка Nginx
cp deploy/nginx.conf /etc/nginx/sites-available/capital-repair-db
ln -sf /etc/nginx/sites-available/capital-repair-db /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Настройка Supervisor для API
cp deploy/supervisor.conf /etc/supervisor/conf.d/capital-repair-api.conf
supervisorctl reread
supervisorctl update
supervisorctl start capital-repair-api
```

---

## Шаг 4: Проверьте работу

```bash
# Проверка статуса
supervisorctl status capital-repair-api
systemctl status nginx

# Проверка логов
tail -f /var/log/capital-repair-api.out.log
```

Откройте браузер: **http://62.113.36.101**

---

## Шаг 5: Загрузка данных (опционально)

Если хотите загрузить данные на сервер для импорта:

### С вашего ПК (в PowerShell):
```powershell
cd C:\Users\Usr146\Desktop\Capital_repair_db\capital-repair-db

# Загрузка файлов данных
scp -r data\regions root@62.113.36.101:/opt/capital-repair-db/data/
scp -r data\ojf_data root@62.113.36.101:/opt/capital-repair-db/data/
scp "Реестр поставщиков информации от  2026-02-02.xlsx" root@62.113.36.101:/opt/capital-repair-db/
```

### На сервере:
```bash
cd /opt/capital-repair-db
source venv/bin/activate

# Импорт для Самарской области
python3 scripts/import_buildings.py --region 63
python3 scripts/import_from_registry.py --region 63
python3 scripts/import_ojf.py --region 63
```

---

## Полезные команды

### Перезапуск API
```bash
supervisorctl restart capital-repair-api
```

### Просмотр логов
```bash
tail -f /var/log/capital-repair-api.out.log
tail -f /var/log/capital-repair-api.err.log
```

### Проверка базы данных
```bash
sudo -u postgres psql capital_repair_db
\dt  # список таблиц
\q   # выход
```
