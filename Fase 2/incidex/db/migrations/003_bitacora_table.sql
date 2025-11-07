-- 003_bitacora_table.sql
USE incidex_db;

CREATE TABLE IF NOT EXISTS bitacora (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  fecha       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuario     VARCHAR(120) NOT NULL,
  rol         VARCHAR(50)  NULL,
  accion      VARCHAR(255) NOT NULL,
  resultado   VARCHAR(255) NULL,
  INDEX idx_bitacora_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


