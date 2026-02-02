# 🚀 Деплой на Timeweb Cloud

## 📋 Информация о сервере

**IP:** 62.113.36.101
**SSH:** `ssh root@62.113.36.101`
**Панель:** https://timeweb.cloud/my/servers/6532487/access

---

## 🎯 Стратегия деплоя

### Что идёт в GitHub:
- ✅ Весь код (Python скрипты, SQL миграции)
- ✅ Документация (.md файлы)
- ✅ Конфигурационные шаблоны
- ✅ requirements.txt
- ✅ .gitignore

### Что НЕ идёт в GitHub (загружаем отдельно):
- ❌ CSV файлы (~2 ГБ)
- ❌ OJF файлы (~500 МБ)
- ❌ Реестр .xlsx (~25 МБ)
- ❌ Пароли и credentials

---

## 📦 Шаг 1: Подготовка репозитория GitHub

### На локальной машине:

```bash
cd c:\Users\makar\Desktop\Region_parsing

# Инициализация Git
git init

# Создать .gitkeep файлы для пустых папок
type nul > data\regions\.gitkeep
type nul > data\ojf_data\.gitkeep
type nul > data\uk_data\.gitkeep

# Добавить файлы
git add .

# Первый коммит
git commit -m "Initial commit: Capital Repair Database System"

# Создать репозиторий на GitHub и подключить
git remote add origin https://github.com/ВАШ_USERNAME/capital-repair-db.git
git branch -M main
git push -u origin main
```

---

## 🖥️ Шаг 2: Подключение к серверу

```bash
ssh root@62.113.36.101
# Пароль: j4eVZ-g@aPA2U6
```

### Первичная настройка сервера:

```bash
# Обновить систему
apt update && apt upgrade -y

# Установить необходимые пакеты
apt install -y git python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# Создать пользователя для приложения (безопасность!)
adduser capitalrepair
usermod -aG sudo capitalrepair

# Переключиться на нового пользователя
su - capitalrepair
```

---

## 🗄️ Шаг 3: Установка PostgreSQL

```bash
# PostgreSQL уже установлен, настроим его
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создать пользователя БД
sudo -u postgres psql -c "CREATE USER repairuser WITH PASSWORD 'YOUR_STRONG_PASSWORD_HERE';"
sudo -u postgres psql -c "CREATE DATABASE capital_repair_db OWNER repairuser;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE capital_repair_db TO repairuser;"

# Разрешить удаленное подключение (опционально)
# sudo nano /etc/postgresql/14/main/postgresql.conf
# Раскомментировать: listen_addresses = '*'
# sudo nano /etc/postgresql/14/main/pg_hba.conf
# Добавить: host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql
```

---

## 📥 Шаг 4: Клонирование проекта

```bash
# Перейти в домашнюю директорию
cd ~

# Клонировать репозиторий
git clone https://github.com/ВАШ_USERNAME/capital-repair-db.git
cd capital-repair-db

# Создать виртуальное окружение Python
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать конфигурацию
cp scripts/config.py.template scripts/config.py
nano scripts/config.py
# Заполнить DB_PASSWORD
```

---

## 📊 Шаг 5: Загрузка данных на сервер

### С локальной машины (Windows PowerShell):

```powershell
# Установить и использовать rsync или WinSCP
# Вариант 1: rsync через WSL
wsl rsync -avz --progress "c:\Users\makar\Desktop\Region_parsing\data\regions\" root@62.113.36.101:/home/capitalrepair/capital-repair-db/data/regions/

wsl rsync -avz --progress "c:\Users\makar\Desktop\Region_parsing\data\ojf_data\" root@62.113.36.101:/home/capitalrepair/capital-repair-db/data/ojf_data/

wsl rsync -avz --progress "c:\Users\makar\Desktop\Region_parsing\Реестр поставщиков информации от  2026-02-01.xlsx" root@62.113.36.101:/home/capitalrepair/capital-repair-db/

# Вариант 2: SCP (если много файлов, сначала заархивировать)
# Заархивировать локально:
tar -czf data_regions.tar.gz data/regions/
tar -czf data_ojf.tar.gz data/ojf_data/

# Загрузить на сервер
scp data_regions.tar.gz root@62.113.36.101:/home/capitalrepair/capital-repair-db/
scp data_ojf.tar.gz root@62.113.36.101:/home/capitalrepair/capital-repair-db/
scp "Реестр поставщиков информации от  2026-02-01.xlsx" root@62.113.36.101:/home/capitalrepair/capital-repair-db/
```

### На сервере (разархивировать):

```bash
cd ~/capital-repair-db
tar -xzf data_regions.tar.gz
tar -xzf data_ojf.tar.gz
rm *.tar.gz  # Удалить архивы
```

---

## 🚀 Шаг 6: Создание БД и импорт данных

```bash
cd ~/capital-repair-db

# Применить миграции
PGPASSWORD='YOUR_DB_PASSWORD' psql -U repairuser -h localhost -d capital_repair_db -f database/001_initial_schema.sql
PGPASSWORD='YOUR_DB_PASSWORD' psql -U repairuser -h localhost -d capital_repair_db -f database/002_views_and_data.sql

# Импорт данных (активировать venv если не активен)
source venv/bin/activate

# Импорт Татарстана для теста
cd scripts
python import_csv.py --region 16

# Проверка
PGPASSWORD='YOUR_DB_PASSWORD' psql -U repairuser -h localhost -d capital_repair_db -c "SELECT COUNT(*) FROM buildings;"

# Если OK - импорт всех регионов
for region in 02 12 13 16 18 21 43 52 56 58 59 63 64 73; do
    echo "Importing region $region..."
    python import_csv.py --region $region
done

# Импорт OJF
python import_ojf.py --all

# Импорт Registry
python import_registry.py

# Финальная проверка
PGPASSWORD='YOUR_DB_PASSWORD' psql -U repairuser -h localhost -d capital_repair_db -c "SELECT * FROM v_regional_stats;"
```

---

## 🔒 Шаг 7: Безопасность

```bash
# Настроить файрвол
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5432/tcp  # Только если нужен внешний доступ к БД
sudo ufw enable

# Запретить root SSH логин (после создания sudo пользователя)
sudo nano /etc/ssh/sshd_config
# Изменить: PermitRootLogin no
sudo systemctl restart sshd

# Настроить fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 🌐 Шаг 8: Веб-интерфейс (следующий этап)

После успешного импорта данных можно создать веб-интерфейс:

```bash
# FastAPI backend будет слушать на localhost:8000
# Nginx будет прокси на 80/443 порту

# Пример запуска FastAPI (когда будет готов)
cd ~/capital-repair-db
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📊 Шаг 9: Автоматизация и обслуживание

### Создать systemd сервис для автозапуска:

```bash
sudo nano /etc/systemd/system/capital-repair.service
```

```ini
[Unit]
Description=Capital Repair Database API
After=network.target postgresql.service

[Service]
Type=simple
User=capitalrepair
WorkingDirectory=/home/capitalrepair/capital-repair-db
Environment="PATH=/home/capitalrepair/capital-repair-db/venv/bin"
ExecStart=/home/capitalrepair/capital-repair-db/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable capital-repair
sudo systemctl start capital-repair
```

---

## 🔄 Обновление проекта

### На сервере:

```bash
cd ~/capital-repair-db
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart capital-repair
```

---

## ✅ Контрольный список деплоя

**Локально:**
- [ ] Протестировать импорт на Татарстане
- [ ] Создать .gitignore
- [ ] Создать репозиторий на GitHub
- [ ] Запушить код

**На сервере:**
- [ ] Подключиться по SSH
- [ ] Установить PostgreSQL
- [ ] Создать БД и пользователя
- [ ] Клонировать репозиторий
- [ ] Загрузить данные (rsync/scp)
- [ ] Применить миграции
- [ ] Импортировать данные
- [ ] Настроить файрвол
- [ ] Настроить автозапуск

---

## 💡 Полезные команды

```bash
# Проверка размера БД
PGPASSWORD='pwd' psql -U repairuser -h localhost -d capital_repair_db -c "SELECT pg_size_pretty(pg_database_size('capital_repair_db'));"

# Бэкап БД
pg_dump -U repairuser -h localhost capital_repair_db > backup_$(date +%Y%m%d).sql

# Восстановление БД
psql -U repairuser -h localhost capital_repair_db < backup_20260202.sql

# Мониторинг импорта
tail -f logs/import.log

# Проверка статуса PostgreSQL
sudo systemctl status postgresql

# Рестарт PostgreSQL
sudo systemctl restart postgresql
```

---

## 📞 Если что-то пошло не так

1. Проверить логи PostgreSQL: `sudo tail -f /var/log/postgresql/postgresql-14-main.log`
2. Проверить логи импорта: `cat logs/import.log`
3. Проверить подключение к БД: `psql -U repairuser -h localhost -d capital_repair_db`
4. Проверить доступное место: `df -h`
5. Проверить память: `free -h`

---

## 🎯 Рекомендуемая последовательность

1. ✅ **Сначала протестировать локально** (Татарстан)
2. ✅ Создать GitHub репозиторий
3. ✅ Настроить сервер (PostgreSQL, пользователи)
4. ✅ Клонировать код
5. ✅ Загрузить данные
6. ✅ Импортировать Татарстан на сервере (тест)
7. ✅ Импортировать все регионы
8. ✅ Разработать веб-интерфейс
9. ✅ Настроить Nginx + SSL
10. ✅ Автозапуск и мониторинг
