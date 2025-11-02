-- 001_init.sql - incidex_db - Inicialización de esquema y catálogos de Incidex
CREATE DATABASE IF NOT EXISTS incidex_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE incidex_db;

-- Opcional: zona horaria consistente
SET time_zone = '+00:00';

-- Catálogos mínimos (para pruebas y reportes CSV)
CREATE TABLE IF NOT EXISTS roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS priorities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(20) NOT NULL UNIQUE,
  sla_hours INT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS statuses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE,
  is_terminal TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Semillas iniciales
INSERT IGNORE INTO roles (name, description) VALUES
  ('ADMIN', 'Administrador del sistema'),
  ('ANALYST', 'Analista / Soporte'),
  ('REQUESTER', 'Usuario solicitante'),
  ('QA', 'Calidad / Auditoría');

INSERT IGNORE INTO priorities (name, sla_hours) VALUES
  ('ALTA', 24), ('MEDIA', 72), ('BAJA', 120);

INSERT IGNORE INTO statuses (name, is_terminal) VALUES
  ('NUEVO', 0), ('ASIGNADO', 0), ('EN_PROGRESO', 0), ('RESUELTO', 0), ('CERRADO', 1), ('RECHAZADO', 1);

INSERT IGNORE INTO categories (name, description) VALUES
  ('Hardware', 'Equipos y periféricos'),
  ('Software', 'Aplicaciones y sistemas'),
  ('Red', 'Conectividad y VPN'),
  ('Seguridad', 'Accesos y credenciales'),
  ('Aplicaciones internas', 'Sistemas internos');

INSERT IGNORE INTO departments (name) VALUES
  ('TI'), ('Recursos Humanos'), ('Finanzas'), ('Operaciones');
