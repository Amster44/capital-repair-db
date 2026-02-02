-- ============================================
-- Миграция 001: Начальная схема БД
-- Система управления капремонтом МКД
-- ============================================

-- Установка кодировки клиента для корректного чтения UTF-8
SET client_encoding = 'UTF8';

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Для полнотекстового поиска

-- ============================================
-- 1. СПРАВОЧНИКИ
-- ============================================

-- 1.1. Регионы
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    region_code VARCHAR(2) NOT NULL UNIQUE,
    region_name VARCHAR(255) NOT NULL,
    federal_district VARCHAR(100) DEFAULT 'Приволжский ФО',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE regions IS 'Регионы Приволжского федерального округа';

-- 1.2. Муниципальные образования
CREATE TABLE municipalities (
    id SERIAL PRIMARY KEY,
    region_id INTEGER REFERENCES regions(id) ON DELETE CASCADE,
    oktmo_code VARCHAR(11),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_municipalities_region ON municipalities(region_id);
CREATE INDEX idx_municipalities_oktmo ON municipalities(oktmo_code);

-- 1.3. Типы организаций
CREATE TABLE organization_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

COMMENT ON TABLE organization_types IS 'Типы управляющих организаций: УК, ТСЖ, ЖСК, REGOP';

-- 1.4. Статусы сделок
CREATE TABLE deal_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7),
    sort_order INTEGER DEFAULT 0
);

COMMENT ON TABLE deal_statuses IS 'Статусы сделок для CRM воронки';

-- ============================================
-- 2. ОСНОВНЫЕ ДАННЫЕ (ИЗ CSV)
-- ============================================

-- 2.1. Многоквартирные дома
CREATE TABLE buildings (
    id BIGSERIAL PRIMARY KEY,

    -- Идентификация
    region_id INTEGER REFERENCES regions(id),
    municipality_id INTEGER REFERENCES municipalities(id),
    mkd_code VARCHAR(20),
    houseguid UUID,
    house_id VARCHAR(20),
    address TEXT NOT NULL,

    -- Основные характеристики
    commission_year INTEGER,
    total_sq DECIMAL(12,2),
    total_rooms_amount INTEGER,
    living_rooms_amount INTEGER,
    total_rooms_sq DECIMAL(12,2),
    living_rooms_sq DECIMAL(12,2),
    total_ppl INTEGER,
    number_floors_max INTEGER,

    -- Финансы капремонта
    money_collecting_way TEXT,
    spec_account_owner_type VARCHAR(10),
    money_ppl_collected DECIMAL(15,2),
    money_ppl_collected_debts DECIMAL(15,2),
    overhaul_funds_spent_all DECIMAL(15,2),
    overhaul_funds_spent_subsidy DECIMAL(15,2),
    overhaul_fund_spent_other DECIMAL(15,2),
    overhaul_funds_balance DECIMAL(15,2),
    owners_payment DECIMAL(10,2),

    -- Дополнительно
    energy_efficiency VARCHAR(5),
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

    CONSTRAINT unique_building UNIQUE(region_id, mkd_code)
);

COMMENT ON TABLE buildings IS 'Многоквартирные дома в программе капремонта';
COMMENT ON COLUMN buildings.overhaul_funds_balance IS 'КЛЮЧЕВОЕ ПОЛЕ: остаток средств на капремонт';
COMMENT ON COLUMN buildings.spec_account_owner_type IS 'UK/TSJ/JSK/REGOP';

-- Индексы для buildings
CREATE INDEX idx_buildings_houseguid ON buildings(houseguid);
CREATE INDEX idx_buildings_region ON buildings(region_id);
CREATE INDEX idx_buildings_municipality ON buildings(municipality_id);
CREATE INDEX idx_buildings_spec_account ON buildings(spec_account_owner_type)
    WHERE spec_account_owner_type IS NOT NULL;
CREATE INDEX idx_buildings_balance ON buildings(overhaul_funds_balance);
CREATE INDEX idx_buildings_address_gin ON buildings USING gin(address gin_trgm_ops);

-- 2.2. Лифты
CREATE TABLE lifts (
    id BIGSERIAL PRIMARY KEY,

    building_id BIGINT REFERENCES buildings(id) ON DELETE CASCADE,
    element_code VARCHAR(20),

    -- Характеристики лифта
    lift_type VARCHAR(100),
    stops_count INTEGER,
    commissioning_date DATE,
    decommissioning_date DATE,

    -- Метаданные
    last_update TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_lift UNIQUE(building_id, element_code)
);

COMMENT ON TABLE lifts IS 'Лифтовое оборудование в домах';
COMMENT ON COLUMN lifts.decommissioning_date IS 'КЛЮЧЕВОЕ ПОЛЕ: дата планового вывода из эксплуатации';

-- Индексы для lifts
CREATE INDEX idx_lifts_building ON lifts(building_id);
CREATE INDEX idx_lifts_decommission ON lifts(decommissioning_date);
CREATE INDEX idx_lifts_type ON lifts(lift_type);

-- 2.3. Прочие конструктивные элементы
CREATE TABLE construction_elements (
    id BIGSERIAL PRIMARY KEY,

    building_id BIGINT REFERENCES buildings(id) ON DELETE CASCADE,
    element_code VARCHAR(20),
    element_type TEXT,
    system_type VARCHAR(255),

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

-- 2.4. Услуги и работы по капремонту
CREATE TABLE services (
    id BIGSERIAL PRIMARY KEY,

    building_id BIGINT REFERENCES buildings(id) ON DELETE CASCADE,
    element_code VARCHAR(20),
    service_code VARCHAR(20),

    -- Описание услуги
    service_type TEXT,
    event_type TEXT,
    work_code VARCHAR(20),

    -- Даты
    service_date INTEGER,
    service_date_by_plan INTEGER,
    date_contract_concluded DATE,
    contract_date_services_finished DATE,
    fact_date_services_finished DATE,

    -- Стоимость
    plan_service_cost_kpkr DECIMAL(15,2),
    plan_service_cost_conclusion_contract DECIMAL(15,2),
    plan_service_cost_contract DECIMAL(15,2),

    -- Объем работ
    measure VARCHAR(50),
    service_scope DECIMAL(12,2),
    lifts_count INTEGER,

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

-- ============================================
-- 3. УК/ТСЖ
-- ============================================

-- 3.1. Управляющие компании
CREATE TABLE management_companies (
    id BIGSERIAL PRIMARY KEY,

    -- Основные данные
    type_id INTEGER REFERENCES organization_types(id),
    name TEXT NOT NULL,
    inn VARCHAR(12) UNIQUE,
    ogrn VARCHAR(15),
    kpp VARCHAR(9),

    -- Контакты
    director_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    legal_address TEXT,
    actual_address TEXT,
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
    data_source VARCHAR(50),
    source_url TEXT,

    -- Метаданные
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_parsed_at TIMESTAMP
);

COMMENT ON TABLE management_companies IS 'Управляющие компании, ТСЖ, ЖСК';
COMMENT ON COLUMN management_companies.director_name IS 'ВАЖНО: ФИО руководителя для контакта';
COMMENT ON COLUMN management_companies.phone IS 'ВАЖНО: Телефон для связи';
COMMENT ON COLUMN management_companies.email IS 'ВАЖНО: Email для связи';

CREATE INDEX idx_companies_inn ON management_companies(inn);
CREATE INDEX idx_companies_region ON management_companies(region_id);
CREATE INDEX idx_companies_type ON management_companies(type_id);
CREATE INDEX idx_companies_name_gin ON management_companies USING gin(name gin_trgm_ops);

-- 3.2. Связь дом ↔ УК
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

-- ============================================
-- 4. CRM МОДУЛЬ
-- ============================================

-- 4.1. Роли пользователей
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB
);

-- 4.2. Пользователи
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
    responsible_regions INTEGER[],

    -- Метаданные
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- 4.3. Сделки
CREATE TABLE deals (
    id BIGSERIAL PRIMARY KEY,

    -- Связи
    building_id BIGINT REFERENCES buildings(id),
    company_id BIGINT REFERENCES management_companies(id),
    status_id INTEGER REFERENCES deal_statuses(id),

    -- Информация о сделке
    deal_name TEXT,
    potential_amount DECIMAL(15,2),
    lift_count_to_replace INTEGER,
    estimated_cost_per_lift DECIMAL(15,2) DEFAULT 2400000,

    -- Условия
    advance_percent INTEGER DEFAULT 50,
    advance_amount DECIMAL(15,2),
    installment_months INTEGER,

    -- Важные даты
    first_contact_date DATE,
    presentation_date DATE,
    expected_close_date DATE,
    actual_close_date DATE,

    -- Вероятность успеха
    probability_percent INTEGER DEFAULT 0,

    -- Ответственный менеджер
    assigned_user_id INTEGER REFERENCES users(id),

    -- Комментарии
    notes TEXT,
    rejection_reason TEXT,

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

COMMENT ON COLUMN deals.estimated_cost_per_lift IS 'По умолчанию 2,400,000 руб за лифт с монтажом';
COMMENT ON COLUMN deals.advance_percent IS 'По умолчанию 50% аванс';

CREATE INDEX idx_deals_building ON deals(building_id);
CREATE INDEX idx_deals_company ON deals(company_id);
CREATE INDEX idx_deals_status ON deals(status_id);
CREATE INDEX idx_deals_assigned ON deals(assigned_user_id);
CREATE INDEX idx_deals_close_date ON deals(expected_close_date);

-- 4.4. Контактные лица
CREATE TABLE contacts (
    id BIGSERIAL PRIMARY KEY,

    company_id BIGINT REFERENCES management_companies(id),
    building_id BIGINT REFERENCES buildings(id),

    -- Персональные данные
    full_name VARCHAR(255) NOT NULL,
    position VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    additional_phone VARCHAR(50),

    -- Соцсети и мессенджеры
    telegram VARCHAR(100),
    whatsapp VARCHAR(50),

    -- Статус
    is_decision_maker BOOLEAN DEFAULT false,
    is_primary BOOLEAN DEFAULT false,

    -- Заметки
    notes TEXT,

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

COMMENT ON COLUMN contacts.is_decision_maker IS 'ЛПР - лицо принимающее решение';

CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_contacts_building ON contacts(building_id);
CREATE INDEX idx_contacts_decision_maker ON contacts(is_decision_maker)
    WHERE is_decision_maker = true;

-- 4.5. История взаимодействий
CREATE TABLE activities (
    id BIGSERIAL PRIMARY KEY,

    deal_id BIGINT REFERENCES deals(id) ON DELETE CASCADE,
    contact_id BIGINT REFERENCES contacts(id),

    -- Тип активности
    activity_type VARCHAR(50) NOT NULL,
    subject VARCHAR(500),
    description TEXT,

    -- Результат
    outcome VARCHAR(100),
    next_action TEXT,
    next_action_date DATE,

    -- Время
    activity_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER,

    -- Ответственный
    user_id INTEGER REFERENCES users(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN activities.activity_type IS 'call, email, meeting, presentation, offer_sent';

CREATE INDEX idx_activities_deal ON activities(deal_id);
CREATE INDEX idx_activities_contact ON activities(contact_id);
CREATE INDEX idx_activities_user ON activities(user_id);
CREATE INDEX idx_activities_date ON activities(activity_date);
CREATE INDEX idx_activities_next_action ON activities(next_action_date)
    WHERE next_action_date IS NOT NULL;

-- 4.6. Файлы
CREATE TABLE files (
    id BIGSERIAL PRIMARY KEY,

    -- Привязка к сущности
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,

    -- Файл
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),

    -- Описание
    file_type VARCHAR(50),
    description TEXT,

    -- Метаданные
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_files_entity ON files(entity_type, entity_id);
CREATE INDEX idx_files_user ON files(uploaded_by);

-- 4.7. Журнал аудита
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,

    user_id INTEGER REFERENCES users(id),

    -- Действие
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
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
