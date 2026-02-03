-- MySQL Schema для Capital Repair Database
-- Упрощённая версия для локальной разработки

CREATE DATABASE IF NOT EXISTS capital_repair_db
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE capital_repair_db;

-- Регионы
CREATE TABLE regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_code VARCHAR(2) NOT NULL UNIQUE,
    region_name VARCHAR(255) NOT NULL,
    federal_district VARCHAR(100) DEFAULT 'Приволжский ФО',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Управляющие компании
CREATE TABLE management_companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ogrn VARCHAR(15) UNIQUE,
    name VARCHAR(500),
    inn VARCHAR(12),
    kpp VARCHAR(9),
    phone VARCHAR(100),
    email VARCHAR(255),
    director_name VARCHAR(255),
    address TEXT,
    region_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL,
    INDEX idx_ogrn (ogrn),
    INDEX idx_name (name(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Дома
CREATE TABLE buildings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Идентификация
    region_id INT,
    houseguid VARCHAR(36),
    mkd_code VARCHAR(20),
    address TEXT NOT NULL,
    region VARCHAR(255),

    -- Характеристики
    commission_year INT,
    total_sq DECIMAL(12,2),
    number_floors_max INT,
    total_ppl INT,

    -- Финансы
    spec_account_owner_type VARCHAR(10),
    overhaul_funds_balance DECIMAL(15,2),

    -- Связь с УК
    ogrn_uo VARCHAR(15),
    management_company_id INT,

    -- Метаданные
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (region_id) REFERENCES regions(id),
    FOREIGN KEY (management_company_id) REFERENCES management_companies(id) ON DELETE SET NULL,

    INDEX idx_houseguid (houseguid),
    INDEX idx_region (region_id),
    INDEX idx_ogrn_uo (ogrn_uo),
    INDEX idx_balance (overhaul_funds_balance),
    INDEX idx_spec_account (spec_account_owner_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Лифты
CREATE TABLE lifts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    building_id BIGINT,
    element_code VARCHAR(20),

    lift_type VARCHAR(100),
    stops_count INT,
    commissioning_date DATE,
    decommissioning_date DATE,

    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,

    INDEX idx_building (building_id),
    INDEX idx_decommission (decommissioning_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Связь домов и УК (если нужна many-to-many)
CREATE TABLE buildings_management (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    building_id BIGINT NOT NULL,
    company_id INT NOT NULL,
    ogrn VARCHAR(15),
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES management_companies(id) ON DELETE CASCADE,

    UNIQUE KEY unique_link (building_id, company_id),
    INDEX idx_building (building_id),
    INDEX idx_company (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
