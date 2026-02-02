# Развертывание на сервере

## Быстрый старт

### 1. Подключитесь к серверу
```bash
ssh root@62.113.36.101
# Пароль: j4eVZ-g@aPA2U6
```

### 2. Установите необходимые пакеты
```bash
# Скачайте setup_server.sh и запустите
wget https://raw.githubusercontent.com/.../setup_server.sh
chmod +x setup_server.sh
./setup_server.sh
```

Или вручную:
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git supervisor
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
```

### 3. Создайте директорию проекта
```bash
mkdir -p /opt/capital-repair-db
cd /opt/capital-repair-db
```

### 4. Загрузите файлы проекта

#### Вариант A: Через SCP (с вашего компьютера)
```bash
cd c:\Users\Usr146\Desktop\Capital_repair_db\capital-repair-db
scp -r scripts app frontend deploy root@62.113.36.101:/opt/capital-repair-db/
```

#### Вариант B: Через Git (если есть репозиторий)
```bash
git clone <your-repo-url> /opt/capital-repair-db
```

### 5. Настройте Python окружение
```bash
cd /opt/capital-repair-db
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors psycopg2-binary pandas openpyxl gunicorn
```

### 6. Настройте PostgreSQL
```bash
sudo -u postgres psql <<EOF
CREATE DATABASE capital_repair_db;
CREATE USER repair_user WITH PASSWORD 'repair_password_2026';
GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO repair_user;
\c capital_repair_db
GRANT ALL ON SCHEMA public TO repair_user;
EOF
```

### 7. Скопируйте production конфигурацию
```bash
cp deploy/config_production.py scripts/config.py
```

### 8. Инициализируйте базу данных
```bash
source venv/bin/activate
python3 scripts/init_db.py
```

### 9. Импортируйте данные
```bash
# Импорт из реестра (если есть файл)
python3 scripts/import_from_registry.py --region 63

# Импорт из ОЖФ (если есть файлы)
python3 scripts/import_ojf.py --region 63

# Импорт зданий из КР (если есть файлы)
python3 scripts/import_buildings.py --region 63
```

### 10. Соберите фронтенд
```bash
cd frontend
npm install
npm run build
cd ..
```

### 11. Настройте Nginx
```bash
cp deploy/nginx.conf /etc/nginx/sites-available/capital-repair-db
ln -s /etc/nginx/sites-available/capital-repair-db /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### 12. Настройте Supervisor для API
```bash
cp deploy/supervisor.conf /etc/supervisor/conf.d/capital-repair-api.conf
supervisorctl reread
supervisorctl update
supervisorctl start capital-repair-api
```

### 13. Проверьте статус
```bash
# Проверка API
supervisorctl status capital-repair-api

# Проверка Nginx
systemctl status nginx

# Проверка логов
tail -f /var/log/capital-repair-api.out.log
```

## Доступ к приложению

После развертывания приложение доступно по адресу:
- **Frontend**: http://62.113.36.101
- **API**: http://62.113.36.101/api

## Структура файлов на сервере

```
/opt/capital-repair-db/
├── venv/                    # Python virtual environment
├── scripts/                 # Скрипты импорта данных
│   ├── init_db.py
│   ├── import_ojf.py
│   ├── import_from_registry.py
│   └── config.py
├── app/                     # Flask API
│   └── api.py
├── frontend/                # React приложение
│   ├── build/              # Собранная версия
│   └── src/
├── deploy/                  # Deployment скрипты
│   ├── nginx.conf
│   ├── supervisor.conf
│   └── deploy.sh
└── data/                    # Данные (не загружается на сервер)
```

## Управление сервисами

### Restart API
```bash
supervisorctl restart capital-repair-api
```

### Restart Nginx
```bash
systemctl restart nginx
```

### Просмотр логов
```bash
# API logs
tail -f /var/log/capital-repair-api.out.log
tail -f /var/log/capital-repair-api.err.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Обновление приложения

```bash
cd /opt/capital-repair-db
source venv/bin/activate

# Обновить код
git pull  # или scp новые файлы

# Пересобрать фронтенд
cd frontend
npm install
npm run build
cd ..

# Перезапустить API
supervisorctl restart capital-repair-api

# Перезапустить Nginx
systemctl restart nginx
```

## Импорт данных

### Загрузка файлов данных на сервер
```bash
# С вашего компьютера
scp -r data/regions root@62.113.36.101:/opt/capital-repair-db/data/
scp -r data/ojf_data root@62.113.36.101:/opt/capital-repair-db/data/
scp "Реестр поставщиков информации от 2026-02-02.xlsx" root@62.113.36.101:/opt/capital-repair-db/
```

### Запуск импорта на сервере
```bash
ssh root@62.113.36.101
cd /opt/capital-repair-db
source venv/bin/activate

# Импорт для Самарской области
python3 scripts/import_buildings.py --region 63
python3 scripts/import_from_registry.py --region 63
python3 scripts/import_ojf.py --region 63

# Или для всех регионов ПФО
python3 scripts/import_ojf.py --all-pfo
```

## Troubleshooting

### API не запускается
```bash
# Проверить логи
tail -f /var/log/capital-repair-api.err.log

# Проверить статус
supervisorctl status capital-repair-api

# Перезапустить
supervisorctl restart capital-repair-api
```

### База данных недоступна
```bash
# Проверить PostgreSQL
systemctl status postgresql

# Проверить подключение
psql -U repair_user -d capital_repair_db -h localhost
```

### Frontend не загружается
```bash
# Проверить Nginx
nginx -t
systemctl status nginx

# Проверить файлы
ls -la /opt/capital-repair-db/frontend/build/
```
