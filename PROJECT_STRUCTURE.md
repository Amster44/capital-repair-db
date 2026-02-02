# Project Structure

## 📁 Complete File Tree

```
Region_parsing/
│
├── 📄 START_HERE_RU.md              ⭐ Главная инструкция (начните здесь!)
├── 📄 READY_TO_START.md             ⭐ Полное описание системы
├── 📄 DATA_STATUS.md                📊 Статус готовности данных
├── 📄 ИНСТРУКЦИЯ.txt                📖 Краткая инструкция
├── 📄 PROJECT_STRUCTURE.md          📁 Структура проекта (этот файл)
├── 📄 requirements.txt              🐍 Python зависимости
│
├── 🔧 install_postgres.bat          [ШАГ 1] Установка PostgreSQL
├── 🔧 setup_database.bat            [ШАГ 2] Создание БД
├── 🔧 import_data.bat               [ШАГ 3] Импорт домов/лифтов
├── 🔧 import_ojf.bat                [ШАГ 4] Импорт связей дом↔УК
├── 🔧 import_registry.bat           [ШАГ 5] Импорт контактов УК
├── 🔧 check_data.bat                [ШАГ 6] Проверка данных
│
├── 📊 Реестр поставщиков информации от  2026-02-01.xlsx
│
├── 📁 database/                     💾 SQL миграции
│   ├── 001_initial_schema.sql       - 19 таблиц + индексы
│   └── 002_views_and_data.sql       - 4 представления + справочники
│
├── 📁 docs/                         📚 Документация
│   ├── DATABASE_SCHEMA.md           - Полное описание схемы БД
│   ├── UK_DATA_SOURCES.md           - Источники данных об УК
│   └── API_DOCUMENTATION.md         - API (для будущего веб-интерфейса)
│
├── 📁 scripts/                      🐍 Python скрипты
│   ├── config.py                    - Настройки БД и регионов
│   ├── import_csv.py                - Импорт CSV (дома/лифты)
│   ├── import_ojf.py                - Импорт OJF (связи)
│   └── import_registry.py           - Импорт Registry (контакты)
│
├── 📁 data/                         📦 Данные
│   │
│   ├── 📁 regions/                  CSV файлы капремонта
│   │   ├── 📁 02_bashkortostan/
│   │   │   ├── export-kr1_1-02-20260201.csv
│   │   │   ├── export-kr1_2-02-20260201.csv
│   │   │   └── export-kr1_3-02-20260201.csv
│   │   │
│   │   ├── 📁 12_mariy-el/
│   │   ├── 📁 13_mordoviya/
│   │   ├── 📁 16_tatarstan/         ⭐ Для тестирования
│   │   ├── 📁 18_udmurtiya/
│   │   ├── 📁 21_chuvashiya/
│   │   ├── 📁 43_kirov/
│   │   ├── 📁 52_nizhniy-novgorod/
│   │   ├── 📁 56_orenburg/
│   │   ├── 📁 58_penza/
│   │   ├── 📁 59_perm/
│   │   ├── 📁 63_samara/
│   │   ├── 📁 64_saratov/
│   │   └── 📁 73_ulyanovsk/
│   │
│   ├── 📁 ojf_data/                 Данные ОЖФ (ГИС ЖКХ)
│   │   ├── Сведения по ОЖФ Татарстан Респ_1.csv
│   │   ├── Сведения по ОЖФ Татарстан Респ_2.csv
│   │   ├── Сведения по ОЖФ Башкортостан Респ_1.csv
│   │   └── ... (~40 файлов для ПФО)
│   │
│   └── 📁 uk_data/                  Дополнительные данные по УК
│       └── Сведения по субъекту [регион]_*.xlsx
│
└── 📁 web/                          🌐 Веб-интерфейс (будущее)
    ├── backend/                     FastAPI backend
    └── frontend/                    React/Vue frontend

```

---

## 🎯 Ключевые файлы по назначению

### 📖 Документация
| Файл | Описание | Когда читать |
|------|----------|--------------|
| [START_HERE_RU.md](START_HERE_RU.md) | Пошаговая инструкция | В самом начале |
| [READY_TO_START.md](READY_TO_START.md) | Полное описание системы | Перед установкой |
| [DATA_STATUS.md](DATA_STATUS.md) | Статус данных | Проверить готовность |
| [ИНСТРУКЦИЯ.txt](ИНСТРУКЦИЯ.txt) | Краткая инструкция | Быстрый старт |

### 🔧 Batch файлы (для Windows)
| Файл | Что делает | Когда запускать |
|------|------------|-----------------|
| install_postgres.bat | Открывает страницу скачивания PostgreSQL | Шаг 1 |
| setup_database.bat | Создает БД и таблицы | Шаг 2 |
| import_data.bat | Импортирует дома/лифты из CSV | Шаг 3 |
| import_ojf.bat | Связывает дома с УК | Шаг 4 |
| import_registry.bat | Добавляет контакты УК | Шаг 5 |
| check_data.bat | Показывает отчеты | Шаг 6 |

### 🐍 Python скрипты
| Файл | Что делает | Параметры |
|------|------------|-----------|
| import_csv.py | Импорт CSV файлов | `--region 16` `--clean` |
| import_ojf.py | Импорт файлов ОЖФ | `--region 16` `--all` |
| import_registry.py | Импорт Реестра | `--file путь/к/файлу.xlsx` |

### 💾 SQL файлы
| Файл | Что создает | Размер |
|------|-------------|--------|
| 001_initial_schema.sql | 19 таблиц + индексы | ~15 KB |
| 002_views_and_data.sql | 4 представления + справочники | ~8 KB |

### 📊 Данные
| Папка/Файл | Содержимое | Объем |
|------------|------------|-------|
| data/regions/XX_name/ | CSV файлы капремонта (КР 1.1, 1.2, 1.3) | ~2-10 MB каждый |
| data/ojf_data/ | Связи дом→УК (ОГРН) | ~40 файлов, ~500 MB |
| Реестр поставщиков информации.xlsx | Контакты 204K организаций | ~25 MB |

---

## 📊 Схема базы данных (19 таблиц)

### Справочники (4 таблицы)
1. `regions` - Регионы ПФО
2. `municipalities` - Муниципалитеты
3. `organization_types` - Типы организаций (UK/TSJ/JSK/REGOP)
4. `deal_statuses` - Статусы сделок

### Основные данные (7 таблиц)
5. `buildings` - Дома (houseguid, адрес, баланс капремонта)
6. `lifts` - Лифты (дата ввода, срок службы)
7. `construction_elements` - Конструктивные элементы (фасад, кровля)
8. `services` - Коммунальные услуги
9. `management_companies` - УК/ТСЖ/ЖСК (контакты)
10. `buildings_management` - Связь дома↔УК (многие ко многим)
11. `files` - Прикрепленные файлы

### CRM модуль (5 таблиц)
12. `deals` - Сделки
13. `contacts` - Контакты
14. `activities` - Активности (звонки, встречи)
15. `deal_stages` - Этапы сделок
16. `deal_notes` - Заметки по сделкам

### Пользователи (3 таблицы)
17. `roles` - Роли (admin/manager/analyst/viewer)
18. `users` - Пользователи системы
19. `audit_log` - Журнал аудита

### Представления (4 views)
- `v_target_buildings` - Целевые дома с приоритетами
- `v_sales_pipeline` - Воронка продаж
- `v_regional_stats` - Статистика по регионам
- `v_top_management_companies` - Топ УК

---

## 🔗 Связи между данными

```
CSV (КР 1.1)          OJF файлы           Реестр поставщиков
  ↓                      ↓                      ↓
buildings           buildings_management   management_companies
(houseguid)    →    (houseguid→ogrn)   →  (ogrn→контакты)
  ↓
lifts
construction_elements
services
```

### Цепочка импорта:
1. **CSV** → заполняет `buildings`, `lifts`, `construction_elements`, `services`
2. **OJF** → создает `management_companies`, связывает через `buildings.management_company_id`
3. **Реестр** → обновляет `management_companies` (phone, email, director)

---

## 📈 Объемы данных

### После импорта Татарстана (тест):
```
buildings:                17,942 записей
lifts:                    17,987 записей
construction_elements:   ~180,000 записей
services:                ~200,000 записей
management_companies:        542 записей
```

### После импорта всех 14 регионов ПФО:
```
buildings:                ~150,000 записей
lifts:                    ~150,000 записей
construction_elements:  ~1,500,000 записей
services:               ~1,200,000 записей
management_companies:      ~3,500 записей
```

### Размер БД:
- Татарстан: ~50 МБ
- Все 14 регионов: ~500 МБ - 1 ГБ

---

## 🎯 Как найти нужную информацию

### Хочу узнать про дом по адресу:
```sql
SELECT * FROM buildings WHERE address ILIKE '%Казань%Баумана%';
```

### Хочу найти все целевые дома:
```sql
SELECT * FROM v_target_buildings WHERE priority = 'HIGH' LIMIT 50;
```

### Хочу найти УК по названию:
```sql
SELECT * FROM management_companies WHERE full_name ILIKE '%жилсервис%';
```

### Хочу увидеть все дома одной УК:
```sql
SELECT b.* FROM buildings b
JOIN management_companies mc ON b.management_company_id = mc.id
WHERE mc.full_name ILIKE '%название УК%';
```

### Хочу экспортировать данные в Excel:
```bash
psql -U postgres -d capital_repair_db -c "\COPY (SELECT * FROM v_target_buildings) TO 'export.csv' CSV HEADER"
```

---

## ✅ Контрольный список готовности

### Установка
- [ ] PostgreSQL установлен
- [ ] База данных создана (команда: `setup_database.bat`)
- [ ] 19 таблиц созданы (проверка: `psql -U postgres -d capital_repair_db -c "\dt"`)

### Данные
- [ ] CSV файлы в `data/regions/` (14 регионов × 3 файла)
- [ ] OJF файлы в `data/ojf_data/` (~40 файлов)
- [ ] Реестр в корне проекта (.xlsx)

### Импорт
- [ ] Импорт CSV выполнен (`import_data.bat`)
- [ ] Импорт OJF выполнен (`import_ojf.bat`)
- [ ] Импорт Registry выполнен (`import_registry.bat`)
- [ ] Данные проверены (`check_data.bat`)

### Готовность к работе
- [ ] Целевые дома определены (v_target_buildings)
- [ ] УК с контактами (phone, email в management_companies)
- [ ] Связи дом↔УК установлены (management_company_id заполнен)

---

## 🚀 Следующий шаг

После успешного тестирования на Татарстане:

1. **Импортировать все регионы** (выбрать [2] во всех batch-файлах)
2. **Разработать веб-интерфейс** для удобной работы с данными
3. **Развернуть на Timeweb Cloud** для доступа всей команды

---

## 📞 Что спросить у разработчика

Если нужна помощь, подготовьте следующую информацию:

1. Какой шаг выполняете? (1-6)
2. Текст ошибки (скриншот или скопированный текст)
3. Что пытались сделать?
4. Какой регион импортируете?

Это ускорит решение проблемы! 🎯
