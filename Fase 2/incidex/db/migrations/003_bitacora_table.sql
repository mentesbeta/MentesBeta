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

CREATE TABLE IF NOT EXISTS ticket_notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  ticket_id INT NOT NULL,
  kind VARCHAR(30) NOT NULL,               
  message VARCHAR(255) NOT NULL,           
  is_read TINYINT(1) NOT NULL DEFAULT 0,   
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_notif_user (user_id),
  INDEX idx_notif_ticket (ticket_id),
  INDEX idx_notif_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


