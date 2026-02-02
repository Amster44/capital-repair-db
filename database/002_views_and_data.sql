-- ============================================
-- Миграция 002: Представления и начальные данные
-- ============================================

-- Установка кодировки клиента для корректного чтения UTF-8
SET client_encoding = 'UTF8';

-- ============================================
-- ПРЕДСТАВЛЕНИЯ (VIEWS)
-- ============================================

-- View 1: Целевые дома для продаж
CREATE OR REPLACE VIEW v_target_buildings AS
SELECT
    b.id as building_id,
    b.address,
    r.region_name,
    m.name as municipality,
    b.spec_account_owner_type,
    b.overhaul_funds_balance,
    b.total_ppl as residents,
    b.commission_year,

    -- Лифты
    COUNT(l.id) as lifts_count,
    MIN(l.decommissioning_date) as earliest_replacement_date,
    MIN(EXTRACT(YEAR FROM l.decommissioning_date) - EXTRACT(YEAR FROM CURRENT_DATE)) as years_to_replacement,
    ROUND(AVG(EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM l.commissioning_date))) as avg_lift_age,

    -- УК
    mc.id as company_id,
    mc.name as management_company,
    mc.director_name,
    mc.phone as company_phone,
    mc.email as company_email,
    mc.inn as company_inn,

    -- CRM данные
    d.id as deal_id,
    ds.name as deal_status,
    ds.code as deal_status_code,
    d.assigned_user_id,
    u.full_name as assigned_user_name,
    d.potential_amount,
    d.probability_percent,

    -- Приоритет (формула)
    CASE
        WHEN b.overhaul_funds_balance >= 5000000
            AND MIN(EXTRACT(YEAR FROM l.decommissioning_date) - EXTRACT(YEAR FROM CURRENT_DATE)) <= 2
            THEN 'HIGH'
        WHEN b.overhaul_funds_balance >= 2000000
            AND MIN(EXTRACT(YEAR FROM l.decommissioning_date) - EXTRACT(YEAR FROM CURRENT_DATE)) <= 5
            THEN 'MEDIUM'
        ELSE 'LOW'
    END as priority,

    -- Потенциал сделки
    COUNT(l.id) * 2400000 as estimated_deal_amount

FROM buildings b
JOIN regions r ON b.region_id = r.id
LEFT JOIN municipalities m ON b.municipality_id = m.id
LEFT JOIN lifts l ON b.id = l.building_id
LEFT JOIN buildings_management bm ON b.id = bm.building_id AND bm.is_active = true
LEFT JOIN management_companies mc ON bm.company_id = mc.id
LEFT JOIN deals d ON b.id = d.building_id
    AND d.status_id NOT IN (
        SELECT id FROM deal_statuses WHERE code IN ('won', 'lost')
    )
LEFT JOIN deal_statuses ds ON d.status_id = ds.id
LEFT JOIN users u ON d.assigned_user_id = u.id

WHERE b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK')
  AND b.overhaul_funds_balance >= 1200000

GROUP BY b.id, r.region_name, m.name, mc.id, mc.name, mc.director_name,
         mc.phone, mc.email, mc.inn, d.id, ds.name, ds.code,
         d.assigned_user_id, u.full_name, d.potential_amount, d.probability_percent

ORDER BY
    b.overhaul_funds_balance DESC,
    MIN(l.decommissioning_date) ASC;

COMMENT ON VIEW v_target_buildings IS 'Целевые дома для продаж: спецсчета, есть деньги, есть лифты';

-- View 2: Воронка продаж
CREATE OR REPLACE VIEW v_sales_pipeline AS
SELECT
    ds.name as stage,
    ds.code as stage_code,
    ds.sort_order,
    ds.color,
    COUNT(d.id) as deals_count,
    COALESCE(SUM(d.potential_amount), 0) as total_amount,
    COALESCE(ROUND(AVG(d.probability_percent)), 0) as avg_probability,
    STRING_AGG(DISTINCT u.full_name, ', ') as managers

FROM deal_statuses ds
LEFT JOIN deals d ON d.status_id = ds.id
LEFT JOIN users u ON d.assigned_user_id = u.id

GROUP BY ds.id, ds.name, ds.code, ds.sort_order, ds.color
ORDER BY ds.sort_order;

COMMENT ON VIEW v_sales_pipeline IS 'Воронка продаж по этапам';

-- View 3: Статистика по регионам
CREATE OR REPLACE VIEW v_regional_stats AS
SELECT
    r.region_name,
    r.region_code,

    -- Дома
    COUNT(DISTINCT b.id) as total_buildings,
    COUNT(DISTINCT CASE WHEN b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK') THEN b.id END) as spec_account_buildings,
    ROUND(AVG(b.overhaul_funds_balance), 2) as avg_balance,
    SUM(b.overhaul_funds_balance) as total_balance,

    -- Лифты
    COUNT(l.id) as total_lifts,
    COUNT(CASE WHEN EXTRACT(YEAR FROM l.decommissioning_date) - EXTRACT(YEAR FROM CURRENT_DATE) <= 5
          THEN 1 END) as lifts_need_replacement_5y,

    -- Сделки
    COUNT(DISTINCT d.id) as active_deals,
    COALESCE(SUM(d.potential_amount), 0) as pipeline_amount

FROM regions r
LEFT JOIN buildings b ON r.id = b.region_id
LEFT JOIN lifts l ON b.id = l.building_id
LEFT JOIN deals d ON b.id = d.building_id
    AND d.status_id NOT IN (SELECT id FROM deal_statuses WHERE code IN ('won', 'lost'))

GROUP BY r.id, r.region_name, r.region_code
ORDER BY total_buildings DESC;

COMMENT ON VIEW v_regional_stats IS 'Статистика по регионам: дома, лифты, сделки';

-- View 4: Топ управляющих компаний
CREATE OR REPLACE VIEW v_top_management_companies AS
SELECT
    mc.id,
    mc.name,
    mc.inn,
    mc.director_name,
    mc.phone,
    mc.email,
    r.region_name,

    -- Статистика
    COUNT(DISTINCT bm.building_id) as buildings_count,
    COUNT(DISTINCT l.id) as lifts_count,
    SUM(b.overhaul_funds_balance) as total_balance_in_buildings,

    -- Потенциал
    COUNT(DISTINCT l.id) * 2400000 as potential_revenue,

    -- Сделки
    COUNT(DISTINCT d.id) as active_deals_count,
    COALESCE(SUM(d.potential_amount), 0) as deals_amount

FROM management_companies mc
LEFT JOIN buildings_management bm ON mc.id = bm.company_id AND bm.is_active = true
LEFT JOIN buildings b ON bm.building_id = b.id
LEFT JOIN lifts l ON b.id = l.building_id
LEFT JOIN deals d ON b.id = d.building_id
    AND d.status_id NOT IN (SELECT id FROM deal_statuses WHERE code IN ('won', 'lost'))
LEFT JOIN regions r ON mc.region_id = r.id

WHERE b.spec_account_owner_type IN ('UK', 'TSJ', 'JSK')

GROUP BY mc.id, mc.name, mc.inn, mc.director_name, mc.phone, mc.email, r.region_name

HAVING COUNT(DISTINCT bm.building_id) > 0

ORDER BY COUNT(DISTINCT l.id) DESC, total_balance_in_buildings DESC;

COMMENT ON VIEW v_top_management_companies IS 'ТОП управляющих компаний по количеству домов и лифтов';

-- ============================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- ============================================

-- Регионы Приволжского ФО
INSERT INTO regions (region_code, region_name, federal_district, is_active) VALUES
('02', 'Республика Башкортостан', 'Приволжский ФО', true),
('12', 'Республика Марий Эл', 'Приволжский ФО', true),
('13', 'Республика Мордовия', 'Приволжский ФО', true),
('16', 'Республика Татарстан', 'Приволжский ФО', true),
('18', 'Удмуртская Республика', 'Приволжский ФО', true),
('21', 'Чувашская Республика', 'Приволжский ФО', true),
('43', 'Кировская область', 'Приволжский ФО', true),
('52', 'Нижегородская область', 'Приволжский ФО', true),
('56', 'Оренбургская область', 'Приволжский ФО', true),
('58', 'Пензенская область', 'Приволжский ФО', true),
('59', 'Пермский край', 'Приволжский ФО', true),
('63', 'Самарская область', 'Приволжский ФО', true),
('64', 'Саратовская область', 'Приволжский ФО', true),
('73', 'Ульяновская область', 'Приволжский ФО', true)
ON CONFLICT (region_code) DO NOTHING;

-- Типы организаций
INSERT INTO organization_types (code, name, description) VALUES
('UK', 'Управляющая компания', 'Специальный счет, владельцем которого является управляющая компания'),
('TSJ', 'ТСЖ', 'Специальный счет, владельцем которого является товарищество собственников жилья'),
('JSK', 'ЖСК', 'Специальный счет, владельцем которого является жилищно-строительный кооператив'),
('REGOP', 'Региональный оператор', 'Счет регионального оператора')
ON CONFLICT (code) DO NOTHING;

-- Статусы сделок
INSERT INTO deal_statuses (code, name, color, sort_order) VALUES
('new', 'Новый лид', '#6c757d', 10),
('in_contact', 'Первый контакт', '#17a2b8', 20),
('qualified', 'Квалифицирован', '#007bff', 30),
('presentation', 'Презентация', '#ffc107', 40),
('negotiation', 'Переговоры', '#fd7e14', 50),
('offer_sent', 'Отправлено КП', '#e83e8c', 60),
('contract', 'Подготовка договора', '#6f42c1', 70),
('won', 'Выиграна', '#28a745', 80),
('lost', 'Проиграна', '#dc3545', 90),
('postponed', 'Отложена', '#6c757d', 100)
ON CONFLICT (code) DO NOTHING;

-- Роли пользователей
INSERT INTO roles (name, description, permissions) VALUES
('admin', 'Администратор', '{"all": true}'::jsonb),
('manager', 'Менеджер по продажам', '{"deals": ["create", "read", "update"], "contacts": ["create", "read", "update"], "activities": ["create", "read", "update"]}'::jsonb),
('analyst', 'Аналитик', '{"buildings": ["read", "export"], "deals": ["read", "export"], "reports": ["read", "export"]}'::jsonb),
('viewer', 'Наблюдатель', '{"buildings": ["read"], "deals": ["read"]}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- ФУНКЦИИ
-- ============================================

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автообновления updated_at
CREATE TRIGGER update_management_companies_updated_at BEFORE UPDATE ON management_companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_buildings_management_updated_at BEFORE UPDATE ON buildings_management
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deals_updated_at BEFORE UPDATE ON deals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для автоматического расчета суммы аванса
CREATE OR REPLACE FUNCTION calculate_advance_amount()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.potential_amount IS NOT NULL AND NEW.advance_percent IS NOT NULL THEN
        NEW.advance_amount = NEW.potential_amount * NEW.advance_percent / 100;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_deal_advance BEFORE INSERT OR UPDATE ON deals
    FOR EACH ROW EXECUTE FUNCTION calculate_advance_amount();

-- ============================================
-- КОММЕНТАРИИ К ПРЕДСТАВЛЕНИЯМ
-- ============================================

COMMENT ON VIEW v_target_buildings IS
'Основное представление для поиска целевых домов.
Фильтры:
- Только спецсчета (УК/ТСЖ/ЖСК)
- Баланс >= 1.2 млн руб (минимальный аванс)
- Есть лифты
Приоритет:
- HIGH: баланс >= 5 млн + замена через 2 года
- MEDIUM: баланс >= 2 млн + замена через 5 лет
- LOW: остальные';

COMMENT ON VIEW v_sales_pipeline IS
'Воронка продаж для дашборда.
Показывает распределение сделок по этапам:
- Количество сделок
- Общая сумма
- Средняя вероятность
- Менеджеры на этапе';
