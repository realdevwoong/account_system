CREATE DATABASE IF NOT EXISTS my_database
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE my_database;

-- login (정확히 7컬럼)
CREATE TABLE IF NOT EXISTS login (
  id           INT           NOT NULL AUTO_INCREMENT,
  username     VARCHAR(50)   NOT NULL,
  password     VARCHAR(255)  NOT NULL,
  email        VARCHAR(100)  NOT NULL,
  phone_number VARCHAR(20)   NOT NULL,
  address      TEXT          NOT NULL,
  birthdate    DATE          NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_login_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- account (보내주신 desc 그대로)
CREATE TABLE IF NOT EXISTS account (
  id             INT            NOT NULL AUTO_INCREMENT,
  user_id        INT            NOT NULL,
  account_number VARCHAR(30)    NOT NULL,
  bank_name      VARCHAR(50)    NOT NULL,
  balance        DECIMAL(15,2)  NOT NULL DEFAULT 0.00,
  account_type   VARCHAR(20)    NOT NULL,
  created_at     DATETIME                DEFAULT CURRENT_TIMESTAMP,
  interest_rate  DECIMAL(5,2)   NOT NULL,
  maturity_date  DATE                   DEFAULT NULL,
  product_name   VARCHAR(100)           DEFAULT NULL,
  is_fixed_term  TINYINT(1)             DEFAULT 0,
  monthly_limit  DECIMAL(15,2)          DEFAULT NULL,
  auto_transfer  TINYINT(1)             DEFAULT 0,
  note           TEXT                   DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_account_account_number (account_number),
  KEY idx_account_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
