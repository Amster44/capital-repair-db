# Инструкция по развертыванию на сервере

## Вариант 1: Автоматическое развертывание (РЕКОМЕНДУЕТСЯ)

Просто запустите:
```
deploy_all.bat
```

Этот скрипт автоматически:
1. Установит все необходимые пакеты на сервере
2. Настроит PostgreSQL
3. Загрузит файлы проекта
4. Соберет фронтенд
5. Настроит Nginx и Supervisor
6. Запустит приложение

**Пароль**: `j4eVZ-g@aPA2U6` (вводите когда скрипт запросит)

---

## Вариант 2: Пошаговое развертывание

См. файл `deploy\QUICK_START.md`

---

## После развертывания

### Проверка работы

1. **Откройте браузер**: http://62.113.36.101
2. **Проверьте API**: http://62.113.36.101/api/regions

### Проверка статуса на сервере

```bash
ssh root@62.113.36.101

# Статус API
supervisorctl status capital-repair-api

# Статус Nginx
systemctl status nginx

# Логи
tail -f /var/log/capital-repair-api.out.log
```

### Импорт данных

Если нужно загрузить данные на сервер:

1. **Загрузите файлы данных**:
```powershell
scp -r data\regions root@62.113.36.101:/opt/capital-repair-db/data/
scp -r data\ojf_data root@62.113.36.101:/opt/capital-repair-db/data/
scp "Реестр поставщиков информации от  2026-02-02.xlsx" root@62.113.36.101:/opt/capital-repair-db/
```

2. **На сервере выполните импорт**:
```bash
ssh root@62.113.36.101
cd /opt/capital-repair-db
source venv/bin/activate

# Импорт зданий из КР
python3 scripts/import_buildings.py --region 63

# Импорт УК из реестра
python3 scripts/import_from_registry.py --region 63

# Импорт связей из ОЖФ
python3 scripts/import_ojf.py --region 63
```

---

## Управление приложением

### Перезапуск API
```bash
ssh root@62.113.36.101
supervisorctl restart capital-repair-api
```

### Перезапуск Nginx
```bash
ssh root@62.113.36.101
systemctl restart nginx
```

### Просмотр логов
```bash
ssh root@62.113.36.101
tail -f /var/log/capital-repair-api.out.log
tail -f /var/log/capital-repair-api.err.log
tail -f /var/log/nginx/access.log
```

---

## Обновление приложения

Для обновления после изменений в коде:

1. **Загрузите новые файлы**:
```
upload.bat
```

2. **Перезапустите сервисы**:
```bash
ssh root@62.113.36.101
cd /opt/capital-repair-db/frontend
npm run build
supervisorctl restart capital-repair-api
systemctl restart nginx
```

---

## Troubleshooting

### Приложение не открывается
```bash
# Проверьте статусы
ssh root@62.113.36.101
supervisorctl status capital-repair-api
systemctl status nginx

# Проверьте логи
tail -f /var/log/capital-repair-api.err.log
tail -f /var/log/nginx/error.log
```

### База данных недоступна
```bash
ssh root@62.113.36.101
systemctl status postgresql
sudo -u postgres psql capital_repair_db
```

### API возвращает ошибки
```bash
ssh root@62.113.36.101
tail -f /var/log/capital-repair-api.err.log
```

---

## Структура проекта на сервере

```
/opt/capital-repair-db/
├── venv/                 # Python окружение
├── scripts/              # Скрипты импорта
│   ├── init_db.py
│   ├── import_buildings.py
│   ├── import_ojf.py
│   ├── import_from_registry.py
│   └── config.py
├── app/                  # Flask API
│   └── api.py
├── frontend/             # React приложение
│   ├── build/           # Собранная версия
│   └── src/
├── deploy/               # Конфигурации
│   ├── nginx.conf
│   └── supervisor.conf
└── data/                 # Данные (опционально)
```

---

## Конфигурация базы данных

**Имя БД**: `capital_repair_db`
**Пользователь**: `repair_user`
**Пароль**: `repair_password_2026`
**Хост**: `localhost`
**Порт**: `5432`

---

## Полезные команды

### Подключение к серверу
```bash
ssh root@62.113.36.101
```

### Подключение к базе данных
```bash
psql -U repair_user -d capital_repair_db -h localhost
```

### Проверка портов
```bash
netstat -tlnp | grep -E '(80|5000|5432)'
```

### Освобождение места
```bash
# Очистка логов
truncate -s 0 /var/log/capital-repair-api.out.log
truncate -s 0 /var/log/capital-repair-api.err.log

# Очистка npm cache
npm cache clean --force
```
