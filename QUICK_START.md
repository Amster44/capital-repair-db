# 🚀 Быстрый старт

## За 10 минут - от нуля до рабочей системы

### 1. Установите PostgreSQL (5 минут)

**Windows:**
Скачайте и установите с https://www.postgresql.org/download/windows/

**При установке запомните:**
- Порт: 5432
- Пароль для пользователя postgres

### 2. Создайте базу данных (1 минута)

```bash
# Откройте командную строку и выполните:
psql -U postgres -c "CREATE DATABASE capital_repair_db ENCODING 'UTF8';"
```

### 3. Примените миграции (1 минута)

```bash
cd c:\Users\makar\Desktop\Region_parsing

psql -U postgres -d capital_repair_db -f database/001_initial_schema.sql
psql -U postgres -d capital_repair_db -f database/002_views_and_data.sql
```

Если всё прошло успешно, увидите `CREATE TABLE`, `CREATE INDEX`, `INSERT 0 14` и т.д.

### 4. Установите Python зависимости (2 минуты)

```bash
pip install -r requirements.txt
```

### 5. Настройте подключение к БД (30 секунд)

Откройте файл [scripts/config.py](scripts/config.py) и измените:

```python
'password': os.getenv('DB_PASSWORD', 'ВАШ_ПАРОЛЬ')  # ← Укажите пароль от PostgreSQL
```

### 6. Импортируйте данные Татарстана (1 минута)

```bash
cd scripts
python import_csv.py --region 16
```

Увидите:
```
INFO - === Начало импорта региона: Республика Татарстан ===
INFO - КР 1.1 импортирован: 17941 записей
INFO - КР 1.2 импортирован: 198060 записей
INFO - КР 1.3 импортирован: 182158 записей
INFO - === Импорт завершен успешно ===
```

### 7. Проверьте данные (30 секунд)

```bash
psql -U postgres -d capital_repair_db
```

В консоли PostgreSQL выполните:

```sql
-- Сколько домов?
SELECT COUNT(*) FROM buildings;
-- Результат: 17942

-- Сколько лифтов?
SELECT COUNT(*) FROM lifts;
-- Результат: 17987

-- Топ-10 целевых домов
SELECT
    address,
    overhaul_funds_balance as balance,
    lifts_count,
    priority
FROM v_target_buildings
LIMIT 10;
```

---

## ✅ Готово!

Теперь у вас в базе данных:
- ✅ 17,942 дома Татарстана
- ✅ 17,987 лифтов
- ✅ 1,158 домов со спецсчетами (целевая аудитория!)
- ✅ Вся информация о финансах капремонта

---

## 📊 Полезные SQL запросы

### Найти дома с большим балансом и лифтами
```sql
SELECT
    b.address,
    b.overhaul_funds_balance,
    COUNT(l.id) as lifts,
    MIN(l.decommissioning_date) as replacement_date
FROM buildings b
LEFT JOIN lifts l ON b.id = l.building_id
WHERE b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK')
  AND b.overhaul_funds_balance > 2000000
GROUP BY b.id
ORDER BY b.overhaul_funds_balance DESC
LIMIT 20;
```

### Статистика по типам спецсчетов
```sql
SELECT
    spec_account_owner_type,
    COUNT(*) as buildings_count,
    SUM(overhaul_funds_balance) as total_balance,
    AVG(overhaul_funds_balance) as avg_balance
FROM buildings
WHERE spec_account_owner_type IS NOT NULL
GROUP BY spec_account_owner_type;
```

### Лифты требующие замены в ближайшие 3 года
```sql
SELECT
    b.address,
    l.lift_type,
    l.commissioning_date,
    l.decommissioning_date,
    EXTRACT(YEAR FROM l.decommissioning_date) - EXTRACT(YEAR FROM CURRENT_DATE) as years_left
FROM lifts l
JOIN buildings b ON l.building_id = b.id
WHERE l.decommissioning_date < CURRENT_DATE + INTERVAL '3 years'
  AND b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK')
ORDER BY l.decommissioning_date;
```

---

## 🎯 Следующие шаги

1. **Скачайте CSV для других регионов ПФО**
   - Сайт: https://фонд-кр.рф/opendata
   - Поместите в папки `data/regions/*/`
   - Импортируйте: `python import_csv.py --region XX`

2. **Изучите документацию:**
   - [SUMMARY.md](SUMMARY.md) - полное резюме проекта
   - [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - схема БД
   - [scripts/README.md](scripts/README.md) - инструкции по скриптам

3. **Готовы к разработке веб-интерфейса?**
   Сообщите когда будете готовы, и мы продолжим!

---

## ❓ Проблемы?

### Ошибка подключения к БД
```
psycopg2.OperationalError: FATAL: password authentication failed
```
**Решение:** Проверьте пароль в `scripts/config.py`

### Файлы CSV не найдены
```
FileNotFoundError: Папка региона не найдена
```
**Решение:** Убедитесь что CSV файлы в `data/regions/16_tatarstan/`

### Ошибки в данных
```
WARNING - Ошибка в строке 1234: ...
```
**Это нормально!** Скрипт пропускает некорректные строки.

---

**Всё работает? Отлично! Переходите к [SUMMARY.md](SUMMARY.md) для дальнейших шагов.**
