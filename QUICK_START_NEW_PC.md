# БЫСТРЫЙ СТАРТ НА НОВОМ ПК (5 минут)

## 1. Клонируйте проект
```bash
git clone https://github.com/Amster44/capital-repair-db.git
cd capital-repair-db
```

## 2. Установите PostgreSQL
- Скачайте: https://www.postgresql.org/download/
- Установите с паролем `123456` (или любым другим)

## 3. Восстановите БД из дампа

### Вариант A: Дамп уже есть в проекте
```bash
psql -U postgres -c "CREATE DATABASE capital_repair_db;"
psql -U postgres -d capital_repair_db < capital_repair_full.sql
```

### Вариант B: Скачайте дамп с Google Drive
```bash
# Дамп будет в вашем Google Drive
# Скачайте и восстановите:
psql -U postgres -c "CREATE DATABASE capital_repair_db;"
psql -U postgres -d capital_repair_db < путь_к_дампу.sql
```

## 4. Настройте Python
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 5. Создайте .env файл
```bash
cat > scripts/.env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_repair_db
DB_USER=postgres
DB_PASSWORD=123456
EOF
```

## 6. Запустите веб-приложение

### Backend:
```bash
cd backend
python api.py
```
Откроется на http://localhost:5000

### Frontend:
```bash
cd frontend
npm install
npm start
```
Откроется на http://localhost:3000

## ГОТОВО!

**GitHub**: https://github.com/Amster44/capital-repair-db
**Production сервер**: http://62.113.36.101

### Текущие данные в БД:
- 78,312 зданий
- 11,055 управляющих компаний (99% с контактами)
- 57,897 лифтов
- 633,355 конструктивных элементов

### Что уже развернуто:
- ✅ PostgreSQL БД на сервере
- ✅ React фронтенд (Material-UI)
- ✅ Flask REST API
- ✅ Nginx настроен
- ✅ Все данные импортированы

### Если нужно загрузить дамп на сервер:
```bash
# 1. Загрузите дамп
scp capital_repair_full.sql root@62.113.36.101:/tmp/

# 2. Подключитесь к серверу
ssh root@62.113.36.101

# 3. Восстановите БД
sudo -u postgres psql -d capital_repair < /tmp/capital_repair_full.sql

# 4. Перезапустите API
systemctl restart capital-repair-api
```

Готово! Веб-интерфейс на http://62.113.36.101
