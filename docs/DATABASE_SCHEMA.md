# Схема базы данных PostgreSQL для системы управления капремонтом МКД

## Общая архитектура

База данных разделена на несколько логических блоков:

1. **Справочники** - регионы, типы организаций, статусы
2. **Основные данные** - дома, лифты, услуги (из CSV)
3. **УК/ТСЖ** - управляющие компании (парсинг)
4. **CRM модуль** - переговоры, сделки, контакты (ручное заполнение)
5. **Система пользователей** - роли, доступы, аудит

---

## 1. СПРАВОЧНИКИ

### 1.1. regions (Регионы)
```sql
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    region_code VARCHAR(2) NOT NULL UNIQUE,          -- Код региона (02, 16, и т.д.)
    region_name VARCHAR(255) NOT NULL,               -- Республика Татарстан
    federal_district VARCHAR(100),                   -- Приволжский ФО
    is_active BOOLEAN DEFAULT true,                  -- Активен ли регион для работы
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.2. municipalities (Муниципальные образования)
```sql
CREATE TABLE municipalities (
    id SERIAL PRIMARY KEY,
    region_id INTEGER REFERENCES regions(id),
    oktmo_code VARCHAR(11),                          -- ОКТМО код
    name VARCHAR(255) NOT NULL,                      -- Альметьевский р-н
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3. organization_types (Типы организаций)
```sql
CREATE TABLE organization_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,                -- UK, TSJ, JSK, REGOP
    name VARCHAR(100) NOT NULL,                      -- УК, ТСЖ, ЖСК, Регоператор
    description TEXT
);
```

### 1.4. deal_statuses (Статусы сделок)
```sql
CREATE TABLE deal_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,                -- new, in_contact, negotiation, contract, won, lost
    name VARCHAR(100) NOT NULL,                      -- Новый лид, В переговорах, и т.д.
    color VARCHAR(7),                                -- #28a745 (для UI)
    sort_order INTEGER DEFAULT 0
);
```

---

## 2. ОСНОВНЫЕ ДАННЫЕ (ИЗ CSV)

### 2.1. buildings (Многоквартирные дома)
```sql
CREATE TABLE buildings (
    id BIGSERIAL PRIMARY KEY,

    -- Идентификация
    region_id INTEGER REFERENCES regions(id),
    municipality_id INTEGER REFERENCES municipalities(id),
    mkd_code VARCHAR(20),                            -- Код МКД из отчета
    houseguid UUID,                                  -- GUID из ФИАС
    house_id VARCHAR(20),                            -- ID из отчета
    address TEXT NOT NULL,                           -- Полный адрес

    -- Основные характеристики
    commission_year INTEGER,                         -- Год ввода в эксплуатацию
    total_sq DECIMAL(12,2),                         -- Общая площадь
    total_rooms_amount INTEGER,                      -- Количество помещений
    living_rooms_amount INTEGER,                     -- Количество жилых помещений
    total_rooms_sq DECIMAL(12,2),                   -- Площадь всех помещений
    living_rooms_sq DECIMAL(12,2),                  -- Площадь жилых помещений
    total_ppl INTEGER,                              -- Количество жителей
    number_floors_max INTEGER,                       -- Количество этажей

    -- Финансы капремонта (КЛЮЧЕВЫЕ ПОЛЯ!)
    money_collecting_way TEXT,                       -- Способ формирования фонда (полный текст)
    spec_account_owner_type VARCHAR(10),            -- UK, TSJ, JSK, REGOP (код)
    money_ppl_collected DECIMAL(15,2),              -- Собрано средств с жителей
    money_ppl_collected_debts DECIMAL(15,2),        -- Задолженность
    overhaul_funds_spent_all DECIMAL(15,2),         -- Потрачено всего
    overhaul_funds_spent_subsidy DECIMAL(15,2),     -- Потрачено субсидий
    overhaul_fund_spent_other DECIMAL(15,2),        -- Потрачено прочих средств
    overhaul_funds_balance DECIMAL(15,2),           -- ОСТАТОК СРЕДСТВ (важно!)
    owners_payment DECIMAL(10,2),                    -- Взнос собственников

    -- Дополнительно
    energy_efficiency VARCHAR(5),                    -- Класс энергоэффективности
    architectural_monument_category TEXT,
    alarm_document_date DATE,
    exclude_date_from_program DATE,
    inclusion_date_to_program DATE,
    comment TEXT,

    -- Метаданные
    update_date_of_information DATE,
    money_ppl_collected_date DATE,
    last_update TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Индексы для быстрого поиска
    CONSTRAINT unique_building UNIQUE(region_id, mkd_code)
);

-- Индексы
CREATE INDEX idx_buildings_houseguid ON buildings(houseguid);
CREATE INDEX idx_buildings_region ON buildings(region_id);
CREATE INDEX idx_buildings_spec_account ON buildings(spec_account_owner_type) WHERE spec_account_owner_type IS NOT NULL;
CREATE INDEX idx_buildings_balance ON buildings(overhaul_funds_balance);
CREATE INDEX idx_buildings_address ON buildings USING gin(to_tsvector('russian', address));
```

### 2.2. lifts (Лифты)
```sql
CREATE TABLE lifts (
    id BIGSERIAL PRIMARY KEY,

    building_id BIGINT REFERENCES buildings(id) ON DELETE CASCADE,
    element_code VARCHAR(20),                        -- Код конструктивного элемента

    -- Характеристики лифта
    lift_type VARCHAR(100),                          -- Пассажирский, грузовой
    stops_count INTEGER,                             -- Количество остановок
    commissioning_date DATE,                         -- Дата ввода в эксплуатацию
    decommissioning_date DATE,                       -- ДАТА ПЛАНОВОГО ВЫВОДА (важно!)

    -- Вычисляемые поля
    age_years INTEGER GENERATED ALWAYS AS (
        EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM commissioning_date)
    ) STORED,
    years_to_replacement INTEGER GENERATED ALWAYS AS (
        EXTRACT(YEAR FROM decommissioning_date) - EXTRACT(YEAR FROM CURRENT_DATE)
    ) STORED,

    -- Метаданные
    last_update TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_lift UNIQUE(building_id, element_code)
);

-- Индексы
CREATE INDEX idx_lifts_building ON lifts(building_id);
CREATE INDEX idx_lifts_decommission ON lifts(decommissioning_date);
CREATE INDEX idx_lifts_replacement ON lifts(years_to_replacement);
```

### 2.3. construction_elements (Прочие конструктивные элементы)
```sql
CREATE TABLE construction_elements (
    id BIGSERIAL PRIMARY KEY,

    building_id BIGINT REFERENCES buildings(id) ON DELETE CASCADE,
    element_code VARCHAR(20),
    element_type TEXT,                               -- Тип элемента
    system_type VARCHAR(255),                        -- Центральная, автономная и т.д.

    -- Для крыш
    roof_type VARCHAR(255),
    roofing_area DECIMAL(12,2),

    -- Для подвалов
    basement_area DECIMAL(12,2),

    -- Для фасадов
    facade_type VARCHAR(255),
    facade_area DECIMAL(12,2),

    -- Для фундаментов
    foundation_type VARCHAR(255),
    wall_material VARCHAR(255),

    comment TEXT,
    last_update TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_elements_building ON construction_elements(building_id);
CREATE INDEX idx_elements_type ON construction_elements(element_type);
```

### 2.4. services (Услуги и работы по капремонту)
```sql
CREATE TABLE services (
    id BIGSERIAL PRIMARY KEY,

    building_id BIGINT REFERENCES buildings(id) ON DELETE CASCADE,
    element_code VARCHAR(20),
    service_code VARCHAR(20),

    -- Описание услуги
    service_type TEXT,                               -- Тип услуги
    event_type TEXT,
    work_code VARCHAR(20),

    -- Даты
    service_date INTEGER,                            -- Год выполнения
    service_date_by_plan INTEGER,                    -- Плановый год
    date_contract_concluded DATE,
    contract_date_services_finished DATE,
    fact_date_services_finished DATE,

    -- Стоимость
    plan_service_cost_kpkr DECIMAL(15,2),
    plan_service_cost_conclusion_contract DECIMAL(15,2),
    plan_service_cost_contract DECIMAL(15,2),

    -- Объем работ
    measure VARCHAR(50),                             -- Единица измерения
    service_scope DECIMAL(12,2),                    -- Объем
    lifts_count INTEGER,                             -- Количество лифтов (если замена)

    -- Подрядчик
    contractor_name TEXT,
    contractor_inn VARCHAR(12),

    last_update TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_services_building ON services(building_id);
CREATE INDEX idx_services_contractor_inn ON services(contractor_inn);
CREATE INDEX idx_services_type ON services(service_type);
CREATE INDEX idx_services_date ON services(service_date);
```

---

## 3. УК/ТСЖ (ПАРСИНГ ИЗ ВНЕШНИХ ИСТОЧНИКОВ)

### 3.1. management_companies (Управляющие компании)
```sql
CREATE TABLE management_companies (
    id BIGSERIAL PRIMARY KEY,

    -- Основные данные
    type_id INTEGER REFERENCES organization_types(id), -- УК/ТСЖ/ЖСК
    name TEXT NOT NULL,                              -- Название организации
    inn VARCHAR(12) UNIQUE,                          -- ИНН
    ogrn VARCHAR(15),                                -- ОГРН
    kpp VARCHAR(9),

    -- Контакты (КЛЮЧЕВЫЕ ДЛЯ ПРОДАЖ!)
    director_name VARCHAR(255),                      -- ФИО руководителя
    phone VARCHAR(50),                               -- Телефон
    email VARCHAR(255),                              -- Email
    legal_address TEXT,                              -- Юридический адрес
    actual_address TEXT,                             -- Фактический адрес
    website VARCHAR(255),

    -- Лицензия
    license_number VARCHAR(50),
    license_date DATE,
    license_status VARCHAR(50),

    -- Финансовые данные
    authorized_capital DECIMAL(15,2),

    -- География
    region_id INTEGER REFERENCES regions(id),

    -- Источник данных
    data_source VARCHAR(50),                         -- reform_gkh, gis_zkh, egrul, manual
    source_url TEXT,

    -- Метаданные
    is_verified BOOLEAN DEFAULT false,               -- Проверена ли информация
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_parsed_at TIMESTAMP
);

CREATE INDEX idx_companies_inn ON management_companies(inn);
CREATE INDEX idx_companies_region ON management_companies(region_id);
CREATE INDEX idx_companies_type ON management_companies(type_id);
CREATE INDEX idx_companies_name ON management_companies USING gin(to_tsvector('russian', name));
```

### 3.2. buildings_management (Связь дом ↔ УК)
```sql
CREATE TABLE buildings_management (
    id BIGSERIAL PRIMARY KEY,

    building_id BIGINT REFERENCES buildings(id) ON DELETE CASCADE,
    company_id BIGINT REFERENCES management_companies(id),

    -- Период управления
    contract_start_date DATE,
    contract_end_date DATE,
    is_active BOOLEAN DEFAULT true,

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_building_management UNIQUE(building_id, company_id, contract_start_date)
);

CREATE INDEX idx_bm_building ON buildings_management(building_id);
CREATE INDEX idx_bm_company ON buildings_management(company_id);
CREATE INDEX idx_bm_active ON buildings_management(is_active) WHERE is_active = true;
```

---

## 4. CRM МОДУЛЬ (РУЧНОЕ ЗАПОЛНЕНИЕ КОМАНДОЙ)

### 4.1. deals (Сделки)
```sql
CREATE TABLE deals (
    id BIGSERIAL PRIMARY KEY,

    -- Связи
    building_id BIGINT REFERENCES buildings(id),
    company_id BIGINT REFERENCES management_companies(id),
    status_id INTEGER REFERENCES deal_statuses(id),

    -- Информация о сделке
    deal_name TEXT,                                  -- Название сделки
    potential_amount DECIMAL(15,2),                  -- Потенциальная сумма сделки
    lift_count_to_replace INTEGER,                   -- Сколько лифтов планируем заменить
    estimated_cost_per_lift DECIMAL(15,2),          -- Стоимость за 1 лифт

    -- Условия
    advance_percent INTEGER DEFAULT 50,              -- Процент аванса (по умолч. 50%)
    advance_amount DECIMAL(15,2),                    -- Сумма аванса
    installment_months INTEGER,                      -- Срок рассрочки (мес.)

    -- Важные даты
    first_contact_date DATE,                         -- Дата первого контакта
    presentation_date DATE,                          -- Дата презентации
    expected_close_date DATE,                        -- Ожидаемая дата закрытия
    actual_close_date DATE,                          -- Фактическая дата закрытия

    -- Вероятность успеха
    probability_percent INTEGER DEFAULT 0,           -- 0-100%

    -- Ответственный менеджер
    assigned_user_id INTEGER REFERENCES users(id),

    -- Комментарии и заметки
    notes TEXT,                                      -- Общие заметки
    rejection_reason TEXT,                           -- Причина отказа (если lost)

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_deals_building ON deals(building_id);
CREATE INDEX idx_deals_company ON deals(company_id);
CREATE INDEX idx_deals_status ON deals(status_id);
CREATE INDEX idx_deals_assigned ON deals(assigned_user_id);
CREATE INDEX idx_deals_close_date ON deals(expected_close_date);
```

### 4.2. contacts (Контактные лица)
```sql
CREATE TABLE contacts (
    id BIGSERIAL PRIMARY KEY,

    company_id BIGINT REFERENCES management_companies(id),
    building_id BIGINT REFERENCES buildings(id),      -- Может быть привязан к дому (председатель ТСЖ)

    -- Персональные данные
    full_name VARCHAR(255) NOT NULL,
    position VARCHAR(255),                            -- Директор, Председатель, и т.д.
    phone VARCHAR(50),
    email VARCHAR(255),
    additional_phone VARCHAR(50),

    -- Соцсети и мессенджеры
    telegram VARCHAR(100),
    whatsapp VARCHAR(50),

    -- Статус
    is_decision_maker BOOLEAN DEFAULT false,          -- ЛПР (лицо принимающее решение)
    is_primary BOOLEAN DEFAULT false,                 -- Основной контакт

    -- Заметки
    notes TEXT,

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_contacts_building ON contacts(building_id);
CREATE INDEX idx_contacts_decision_maker ON contacts(is_decision_maker) WHERE is_decision_maker = true;
```

### 4.3. activities (История взаимодействий)
```sql
CREATE TABLE activities (
    id BIGSERIAL PRIMARY KEY,

    deal_id BIGINT REFERENCES deals(id) ON DELETE CASCADE,
    contact_id BIGINT REFERENCES contacts(id),

    -- Тип активности
    activity_type VARCHAR(50) NOT NULL,              -- call, email, meeting, presentation, offer_sent
    subject VARCHAR(500),
    description TEXT,

    -- Результат
    outcome VARCHAR(100),                            -- positive, negative, neutral, no_answer
    next_action TEXT,                                -- Следующий шаг
    next_action_date DATE,

    -- Время
    activity_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER,

    -- Ответственный
    user_id INTEGER REFERENCES users(id),

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activities_deal ON activities(deal_id);
CREATE INDEX idx_activities_contact ON activities(contact_id);
CREATE INDEX idx_activities_user ON activities(user_id);
CREATE INDEX idx_activities_date ON activities(activity_date);
CREATE INDEX idx_activities_next_action ON activities(next_action_date) WHERE next_action_date IS NOT NULL;
```

### 4.4. files (Файлы и документы)
```sql
CREATE TABLE files (
    id BIGSERIAL PRIMARY KEY,

    -- Привязка к сущности
    entity_type VARCHAR(50) NOT NULL,                -- deal, building, company, contact
    entity_id BIGINT NOT NULL,

    -- Файл
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,                                -- Размер в байтах
    mime_type VARCHAR(100),

    -- Описание
    file_type VARCHAR(50),                           -- contract, presentation, photo, document
    description TEXT,

    -- Метаданные
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_files_entity ON files(entity_type, entity_id);
CREATE INDEX idx_files_user ON files(uploaded_by);
```

---

## 5. СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ

### 5.1. roles (Роли)
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,                -- admin, manager, analyst, viewer
    description TEXT,
    permissions JSONB                                 -- Права доступа в JSON
);
```

### 5.2. users (Пользователи)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    -- Аутентификация
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Личные данные
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),

    -- Роль и доступ
    role_id INTEGER REFERENCES roles(id),
    is_active BOOLEAN DEFAULT true,

    -- Регионы ответственности
    responsible_regions INTEGER[],                    -- Массив region_id

    -- Метаданные
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
```

### 5.3. audit_log (Журнал аудита)
```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,

    user_id INTEGER REFERENCES users(id),

    -- Действие
    action VARCHAR(50) NOT NULL,                     -- create, update, delete, login, export
    entity_type VARCHAR(50),                         -- building, deal, company, и т.д.
    entity_id BIGINT,

    -- Изменения
    old_values JSONB,
    new_values JSONB,

    -- Контекст
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
```

---

## 6. ПРЕДСТАВЛЕНИЯ (VIEWS) ДЛЯ АНАЛИТИКИ

### 6.1. v_target_buildings (Целевые дома для продаж)
```sql
CREATE VIEW v_target_buildings AS
SELECT
    b.id as building_id,
    b.address,
    r.region_name,
    m.name as municipality,
    b.spec_account_owner_type,
    b.overhaul_funds_balance,
    b.total_ppl as residents,

    -- Лифты
    COUNT(l.id) as lifts_count,
    MIN(l.decommissioning_date) as earliest_replacement_date,
    MIN(l.years_to_replacement) as years_to_replacement,
    AVG(l.age_years) as avg_lift_age,

    -- УК
    mc.name as management_company,
    mc.director_name,
    mc.phone as company_phone,
    mc.email as company_email,

    -- CRM данные
    d.id as deal_id,
    ds.name as deal_status,
    d.assigned_user_id,
    u.full_name as assigned_user_name,

    -- Приоритет (формула)
    CASE
        WHEN b.overhaul_funds_balance >= 5000000 AND MIN(l.years_to_replacement) <= 2 THEN 'HIGH'
        WHEN b.overhaul_funds_balance >= 2000000 AND MIN(l.years_to_replacement) <= 5 THEN 'MEDIUM'
        ELSE 'LOW'
    END as priority

FROM buildings b
JOIN regions r ON b.region_id = r.id
LEFT JOIN municipalities m ON b.municipality_id = m.id
LEFT JOIN lifts l ON b.id = l.building_id
LEFT JOIN buildings_management bm ON b.id = bm.building_id AND bm.is_active = true
LEFT JOIN management_companies mc ON bm.company_id = mc.id
LEFT JOIN deals d ON b.id = d.building_id AND d.status_id NOT IN (SELECT id FROM deal_statuses WHERE code IN ('won', 'lost'))
LEFT JOIN deal_statuses ds ON d.status_id = ds.id
LEFT JOIN users u ON d.assigned_user_id = u.id

WHERE b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK')  -- Только спецсчета (не регоператор)
  AND b.overhaul_funds_balance >= 1200000                 -- Минимум на аванс 50%

GROUP BY b.id, r.region_name, m.name, mc.id, d.id, ds.name, u.full_name

ORDER BY
    b.overhaul_funds_balance DESC,
    MIN(l.years_to_replacement) ASC;
```

### 6.2. v_sales_pipeline (Воронка продаж)
```sql
CREATE VIEW v_sales_pipeline AS
SELECT
    ds.name as stage,
    ds.sort_order,
    COUNT(d.id) as deals_count,
    SUM(d.potential_amount) as total_amount,
    AVG(d.probability_percent) as avg_probability,
    STRING_AGG(DISTINCT u.full_name, ', ') as managers

FROM deals d
JOIN deal_statuses ds ON d.status_id = ds.id
LEFT JOIN users u ON d.assigned_user_id = u.id

GROUP BY ds.id, ds.name, ds.sort_order
ORDER BY ds.sort_order;
```

---

## ИТОГО

**Всего таблиц:** 19
- Справочники: 4
- Основные данные (CSV): 4
- УК/ТСЖ: 2
- CRM: 4
- Пользователи: 3
- Файлы: 1
- Журнал: 1

**Ключевые особенности схемы:**
1. Полная поддержка данных из CSV (3 отчета)
2. Модуль УК/ТСЖ с контактами для парсинга
3. CRM модуль для отслеживания продаж (сделки, контакты, активности)
4. Система пользователей с ролями и аудитом
5. Представления для быстрой аналитики
6. Индексы для быстрого поиска
7. Поля для ручного заполнения командой

**Расчетный объем данных:**
- 14 регионов ПФО × ~18,000 домов = ~250,000 домов
- ~250,000 × 2 лифта = ~500,000 лифтов
- ~250,000 × 10 услуг = ~2,500,000 записей услуг
- ~10,000 УК/ТСЖ
- Всего: ~3.5 млн записей (база среднего размера для PostgreSQL)
