SHOW DATABASES;

USE aimgd;

SHOW TABLES;

-- 创建表
CREATE TABLE IF NOT EXISTS symptom_prob
(
    id           INT AUTO_INCREMENT PRIMARY KEY,
    symptom_name VARCHAR(255)    NOT NULL,
    probability  DECIMAL(20, 10) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

SELECT *
FROM symptom_prob;