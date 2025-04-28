SHOW DATABASES;

USE aimgd;

SHOW TABLES;

-- 创建表
CREATE TABLE IF NOT EXISTS relation_disease_symptom
(
    id           INT AUTO_INCREMENT PRIMARY KEY,
    disease_name VARCHAR(255) NOT NULL,
    symptom_list JSON         NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

SELECT *
FROM relation_disease_symptom;

SELECT COUNT(id)
FROM relation_disease_symptom;