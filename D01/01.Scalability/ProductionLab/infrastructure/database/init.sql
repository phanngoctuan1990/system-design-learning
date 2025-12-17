-- ============================================================
-- Master Address (Flat table - simple, no JOINs needed)
-- ============================================================
CREATE TABLE IF NOT EXISTS master_address (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    province VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    INDEX idx_country (country),
    INDEX idx_country_province (country, province)
);

-- Sample data for Vietnam
INSERT INTO master_address (country, province, district) VALUES
('Vietnam', 'Ha Noi', 'Ba Dinh'),
('Vietnam', 'Ha Noi', 'Hoan Kiem'),
('Vietnam', 'Ha Noi', 'Cau Giay'),
('Vietnam', 'Da Nang', 'Hai Chau'),
('Vietnam', 'Da Nang', 'Thanh Khe'),
('Vietnam', 'Da Nang', 'Son Tra'),
('Vietnam', 'Ho Chi Minh', 'Quan 1'),
('Vietnam', 'Ho Chi Minh', 'Quan 3'),
('Vietnam', 'Ho Chi Minh', 'Binh Thanh');

-- ============================================================
-- User Tables
-- ============================================================
CREATE TABLE IF NOT EXISTS auth_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
);

CREATE TABLE IF NOT EXISTS user_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    address_id INT,
    address_detail VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (address_id) REFERENCES master_address(id)
);
