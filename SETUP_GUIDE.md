# Руководство по настройке проекта Capital Repair DB

## Быстрый старт на новом ПК

### 1. Клонирование репозитория

```bash
git clone https://github.com/Amster44/capital-repair-db.git
cd capital-repair-db
```

### 2. Установка PostgreSQL

**Windows:**
- Скачайте PostgreSQL 16+ с https://www.postgresql.org/download/windows/
- Установите с паролем для пользователя postgres
- Запомните путь установки (обычно `C:\Program Files\PostgreSQL\18`)

**Linux/Ubuntu:**
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

### 3. Создание базы данных

**Windows:**
```cmd
cd database
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "CREATE DATABASE capital_repair_db;"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d capital_repair_db -f 001_initial_schema.sql
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d capital_repair_db -f 002_views_and_data.sql
```

**Linux:**
```bash
sudo -u postgres psql -c "CREATE DATABASE capital_repair;"
sudo -u postgres psql -d capital_repair < database/001_initial_schema.sql
sudo -u postgres psql -d capital_repair < database/002_views_and_data.sql
```

### 4. Установка Python зависимостей

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Настройка конфигурации

Создайте файл `scripts/.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_repair_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль
```

### 6. Импорт данных

**Вариант A: Загрузка дампа (быстро)**

1. Скачайте дамп БД с сервера или от коллеги
2. Восстановите:

```bash
# Windows
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d capital_repair_db < capital_repair_dump.sql

# Linux
psql -U postgres -d capital_repair < capital_repair_dump.sql
```

**Вариант B: Импорт из CSV (долго, но с нуля)**

1. Загрузите CSV файлы в `data/regions/{код_региона}/`
2. Запустите импорт:

```bash
# Все регионы ПФО
cd scripts
python import_csv.py --region 02  # Башкортостан
python import_csv.py --region 12  # Марий Эл
python import_csv.py --region 13  # Мордовия
python import_csv.py --region 16  # Татарстан
python import_csv.py --region 18  # Удмуртия
python import_csv.py --region 21  # Чувашия
python import_csv.py --region 43  # Киров
python import_csv.py --region 52  # Нижний Новгород
python import_csv.py --region 56  # Оренбург
python import_csv.py --region 58  # Пенза
python import_csv.py --region 59  # Пермь
python import_csv.py --region 63  # Самара
python import_csv.py --region 64  # Саратов
python import_csv.py --region 73  # Ульяновск

# Импорт OJF (связи дом-УК)
python import_ojf.py --all

# Импорт контактов УК
python import_registry.py
```

### 7. Запуск веб-приложения

**Backend API:**
```bash
cd backend
python api.py
# API доступен на http://localhost:5000
```

**Frontend (разработка):**
```bash
cd frontend
npm install
npm start
# Откроется на http://localhost:3000
```

**Frontend (production):**
```bash
cd frontend
npm run build
# Раздавайте через nginx из папки frontend/build/
```

## Развертывание на сервере

### Подготовка сервера

```bash
# Подключение
ssh root@your-server-ip

# Установка ПО
apt update && apt upgrade -y
apt install -y postgresql nginx nodejs npm python3 python3-pip python3-venv git

# Клонирование
cd /opt
git clone https://github.com/Amster44/capital-repair-db.git capital_repair
```

### Настройка PostgreSQL

```bash
sudo -u postgres createdb capital_repair
sudo -u postgres psql -d capital_repair < /opt/capital_repair/database/001_initial_schema.sql
sudo -u postgres psql -d capital_repair < /opt/capital_repair/database/002_views_and_data.sql

# Восстановление из дампа
sudo -u postgres psql -d capital_repair < capital_repair_dump.sql
```

### Настройка Backend

```bash
cd /opt/capital_repair
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Создать .env
cat > scripts/.env << 'EOF'
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_repair
DB_USER=postgres
DB_PASSWORD=ваш_пароль
EOF

# Systemd service
cat > /etc/systemd/system/capital-repair-api.service << 'EOF'
[Unit]
Description=Capital Repair Flask API
After=network.target

[Service]
User=root
WorkingDirectory=/opt/capital_repair/backend
Environment="PATH=/opt/capital_repair/venv/bin:/usr/bin"
Environment="PYTHONPATH=/opt/capital_repair"
ExecStart=/opt/capital_repair/venv/bin/python3 /opt/capital_repair/backend/api.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable capital-repair-api
systemctl start capital-repair-api
```

### Настройка Frontend

```bash
cd /opt/capital_repair/frontend
npm install
npm run build
```

### Настройка Nginx

```bash
cat > /etc/nginx/sites-available/capital-repair << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        root /opt/capital_repair/frontend/build;
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/capital-repair /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

## Полезные команды

### Проверка статуса БД

```bash
cd scripts
python -c "
from config import DB_CONFIG
import psycopg2

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM buildings')
print(f'Buildings: {cur.fetchone()[0]:,}')

cur.execute('SELECT COUNT(*) FROM management_companies')
print(f'Companies: {cur.fetchone()[0]:,}')

cur.execute('SELECT COUNT(*) FROM buildings_management')
print(f'Links: {cur.fetchone()[0]:,}')

cur.close()
conn.close()
"
```

### Создание дампа БД

```bash
# Windows
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d capital_repair_db > dump.sql

# Linux
pg_dump -U postgres capital_repair > dump.sql
```

### Обновление кода с GitHub

```bash
git pull origin main
systemctl restart capital-repair-api  # если на сервере
```

## Структура проекта

```
capital-repair-db/
├── backend/              # Flask REST API
│   ├── api.py           # Основной API файл
│   └── requirements.txt # Python зависимости
├── frontend/            # React приложение
│   ├── src/
│   │   ├── App.js
│   │   └── components/
│   ├── public/
│   └── package.json
├── scripts/             # Скрипты импорта
│   ├── import_csv.py
│   ├── import_ojf.py
│   ├── import_registry.py
│   └── config.py
├── database/            # SQL миграции
│   ├── 001_initial_schema.sql
│   └── 002_views_and_data.sql
└── data/               # Данные (не в Git)
    ├── regions/
    ├── ojf_data/
    └── uk_data/
```

## Troubleshooting

**Ошибка подключения к БД:**
- Проверьте что PostgreSQL запущен: `pg_isready`
- Проверьте пароль в `scripts/.env`
- Проверьте что БД создана: `psql -U postgres -l`

**Frontend не собирается:**
- Удалите `node_modules` и `package-lock.json`
- Запустите `npm install` заново

**API не отвечает:**
- Проверьте логи: `journalctl -u capital-repair-api -n 50`
- Проверьте что порт 5000 свободен: `netstat -an | grep 5000`

## Контакты

Репозиторий: https://github.com/Amster44/capital-repair-db
Сервер production: http://62.113.36.101
