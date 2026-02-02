# Руководство по развертыванию системы

## Локальное развертывание (для разработки и тестирования)

### 1. Установка PostgreSQL

**Windows:**
1. Скачайте PostgreSQL с https://www.postgresql.org/download/windows/
2. Установите PostgreSQL 14 или выше
3. Запомните пароль для пользователя `postgres`

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### 2. Создание базы данных

```bash
# Подключитесь к PostgreSQL
psql -U postgres

# В консоли PostgreSQL выполните:
CREATE DATABASE capital_repair_db ENCODING 'UTF8';
\q
```

### 3. Установка Python зависимостей

```bash
# Создайте виртуальное окружение (рекомендуется)
python -m venv venv

# Активируйте его
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 4. Настройка подключения к БД

Создайте файл `.env` из примера:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваш пароль:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_repair_db
DB_USER=postgres
DB_PASSWORD=ВАШ_ПАРОЛЬ
```

### 5. Применение миграций

```bash
psql -U postgres -d capital_repair_db -f database/001_initial_schema.sql
psql -U postgres -d capital_repair_db -f database/002_views_and_data.sql
```

Проверка:
```bash
psql -U postgres -d capital_repair_db -c "\dt"
```

Вы должны увидеть список из 19 таблиц.

### 6. Импорт данных

```bash
cd scripts
python import_csv.py --region 16
```

### 7. Проверка данных

```bash
psql -U postgres -d capital_repair_db

SELECT COUNT(*) as buildings FROM buildings;
SELECT COUNT(*) as lifts FROM lifts;
SELECT * FROM v_target_buildings LIMIT 5;
\q
```

---

## Развертывание на Timeweb Cloud

### 1. Создание сервера

1. Зайдите на https://timeweb.cloud/
2. Создайте новый сервер:
   - **ОС:** Ubuntu 22.04
   - **Конфигурация:** 2 CPU, 4 GB RAM, 40 GB SSD (минимум)
   - **Регион:** Москва

### 2. Подключение к серверу

```bash
ssh root@YOUR_SERVER_IP
```

### 3. Установка PostgreSQL на сервере

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Проверка статуса
sudo systemctl status postgresql

# Настройка PostgreSQL для удаленного доступа (если нужно)
sudo nano /etc/postgresql/14/main/postgresql.conf
# Найдите и измените: listen_addresses = '*'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Добавьте: host all all 0.0.0.0/0 md5

# Перезапуск PostgreSQL
sudo systemctl restart postgresql
```

### 4. Создание БД и пользователя

```bash
sudo -u postgres psql

CREATE DATABASE capital_repair_db ENCODING 'UTF8';
CREATE USER app_user WITH PASSWORD 'SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO app_user;
\q
```

### 5. Установка Python и зависимостей

```bash
# Python 3 обычно уже установлен
python3 --version

# Установка pip и venv
sudo apt install python3-pip python3-venv -y

# Создание директории проекта
mkdir -p /var/www/capital_repair
cd /var/www/capital_repair

# Загрузка проекта (вариант 1: через git)
git clone YOUR_REPO_URL .

# Загрузка проекта (вариант 2: загрузка файлов через scp)
# На локальной машине:
# scp -r Region_parsing/* root@YOUR_SERVER_IP:/var/www/capital_repair/

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 6. Настройка .env файла

```bash
nano .env
```

Содержимое:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_repair_db
DB_USER=app_user
DB_PASSWORD=SECURE_PASSWORD_HERE
```

### 7. Применение миграций

```bash
psql -h localhost -U app_user -d capital_repair_db -f database/001_initial_schema.sql
psql -h localhost -U app_user -d capital_repair_db -f database/002_views_and_data.sql
```

### 8. Импорт данных

```bash
cd scripts
python import_csv.py --region 16
# ... импортируйте другие регионы при необходимости
```

### 9. Настройка веб-интерфейса (FastAPI)

**Будет создано позже**, но вот примерная структура:

```bash
# Установка Gunicorn для продакшена
pip install gunicorn

# Создание systemd сервиса
sudo nano /etc/systemd/system/capital_repair.service
```

Содержимое сервиса:
```ini
[Unit]
Description=Capital Repair Management System
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/capital_repair
Environment="PATH=/var/www/capital_repair/venv/bin"
ExecStart=/var/www/capital_repair/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app

[Install]
WantedBy=multi-user.target
```

```bash
# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl start capital_repair
sudo systemctl enable capital_repair
```

### 10. Настройка Nginx (обратный прокси)

```bash
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/capital_repair
```

Содержимое:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/capital_repair/static;
    }
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/capital_repair /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 11. Настройка SSL (HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d YOUR_DOMAIN
```

### 12. Настройка автоматических бэкапов

```bash
# Создание скрипта бэкапа
sudo nano /usr/local/bin/backup_db.sh
```

Содержимое:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/capital_repair"
mkdir -p $BACKUP_DIR

pg_dump -U app_user -d capital_repair_db > $BACKUP_DIR/backup_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
```

```bash
# Делаем скрипт исполняемым
sudo chmod +x /usr/local/bin/backup_db.sh

# Добавляем в cron (ежедневно в 3:00)
sudo crontab -e
# Добавьте строку:
0 3 * * * /usr/local/bin/backup_db.sh
```

---

## Мониторинг и обслуживание

### Проверка статуса сервисов

```bash
# PostgreSQL
sudo systemctl status postgresql

# Приложение
sudo systemctl status capital_repair

# Nginx
sudo systemctl status nginx
```

### Просмотр логов

```bash
# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Логи приложения
sudo journalctl -u capital_repair -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Обновление данных

```bash
cd /var/www/capital_repair/scripts
source ../venv/bin/activate

# Обновление данных региона
python import_csv.py --region 16 --clean
```

### Оптимизация PostgreSQL

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Рекомендуемые настройки для сервера 4GB RAM:
```
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 5MB
min_wal_size = 1GB
max_wal_size = 4GB
```

```bash
sudo systemctl restart postgresql
```

---

## Безопасность

### 1. Настройка фаервола

```bash
# Разрешить SSH, HTTP, HTTPS
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# Включить фаервол
sudo ufw enable
```

### 2. Ограничение доступа к PostgreSQL

```bash
# Редактирование pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Разрешить подключения только с localhost
# Закомментируйте строку: host all all 0.0.0.0/0 md5
```

### 3. Смена паролей

```bash
# Пароль PostgreSQL
sudo -u postgres psql
ALTER USER app_user WITH PASSWORD 'NEW_SECURE_PASSWORD';
\q

# Обновите .env файл
```

### 4. Регулярные обновления

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Обновление Python пакетов
cd /var/www/capital_repair
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## Решение проблем

### PostgreSQL не запускается

```bash
sudo journalctl -u postgresql -n 50
sudo systemctl restart postgresql
```

### Ошибки импорта данных

```bash
# Проверка подключения
psql -h localhost -U app_user -d capital_repair_db -c "SELECT 1;"

# Проверка логов Python
python import_csv.py --region 16 2>&1 | tee import.log
```

### Высокая нагрузка на БД

```bash
# Проверка активных запросов
psql -U app_user -d capital_repair_db -c "SELECT * FROM pg_stat_activity;"

# VACUUM и ANALYZE
psql -U app_user -d capital_repair_db -c "VACUUM ANALYZE;"
```

---

## Контрольный чеклист развертывания

- [ ] PostgreSQL установлен и работает
- [ ] База данных создана
- [ ] Миграции применены успешно
- [ ] Python зависимости установлены
- [ ] Данные импортированы
- [ ] Веб-интерфейс запущен (после создания)
- [ ] Nginx настроен
- [ ] SSL сертификат установлен
- [ ] Бэкапы настроены
- [ ] Мониторинг работает
- [ ] Документация актуальна
