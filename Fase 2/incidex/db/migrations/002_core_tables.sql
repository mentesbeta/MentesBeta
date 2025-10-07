-- 002_core_tables.sql (versión ajustada)
USE incidex_db;

-- USUARIOS Y ROLES
CREATE TABLE IF NOT EXISTS users (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  names_worker    VARCHAR(120)   NOT NULL,
  last_name       VARCHAR(120)   NOT NULL,
  birthdate       DATE           NOT NULL,
  email           VARCHAR(120)   NOT NULL UNIQUE,
  gender          ENUM('M','F','X','N/A') NOT NULL,
  password_hash   VARCHAR(255)   NOT NULL,
  department_id   INT            NULL,
  is_active       TINYINT(1)     NOT NULL DEFAULT 1,
  created_at      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_department FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_roles (
  user_id INT NOT NULL,
  role_id INT NOT NULL,
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES roles(id)  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- TICKETS
CREATE TABLE IF NOT EXISTS tickets (
  id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(20)  NOT NULL UNIQUE,
  title           VARCHAR(200) NOT NULL,
  description     TEXT         NOT NULL,
  requester_id    INT          NOT NULL,
  assignee_id     INT          NULL,
  department_id   INT          NULL,
  category_id     INT          NULL,
  priority_id     INT          NOT NULL,
  status_id       INT          NOT NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  resolved_at     DATETIME     NULL,
  closed_at       DATETIME     NULL,
  INDEX idx_tickets_requester   (requester_id),
  INDEX idx_tickets_assignee    (assignee_id),
  INDEX idx_tickets_status      (status_id),
  INDEX idx_tickets_category    (category_id),
  INDEX idx_tickets_priority    (priority_id),
  INDEX idx_tickets_created_at  (created_at),
  FULLTEXT INDEX ft_tickets_title_desc (title, description),
  CONSTRAINT fk_t_req  FOREIGN KEY (requester_id)  REFERENCES users(id),
  CONSTRAINT fk_t_ass  FOREIGN KEY (assignee_id)   REFERENCES users(id),
  CONSTRAINT fk_t_dep  FOREIGN KEY (department_id) REFERENCES departments(id),
  CONSTRAINT fk_t_cat  FOREIGN KEY (category_id)   REFERENCES categories(id),
  CONSTRAINT fk_t_pri  FOREIGN KEY (priority_id)   REFERENCES priorities(id),
  CONSTRAINT fk_t_sta  FOREIGN KEY (status_id)     REFERENCES statuses(id)
) ENGINE=InnoDB;

-- HISTORIAL
CREATE TABLE IF NOT EXISTS ticket_history (
  id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  ticket_id       BIGINT     NOT NULL,
  actor_user_id   INT        NOT NULL,
  from_status_id  INT        NULL,
  to_status_id    INT        NOT NULL,
  note            VARCHAR(500) NULL,
  created_at      DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_th_ticket (ticket_id),
  CONSTRAINT fk_th_ticket  FOREIGN KEY (ticket_id)     REFERENCES tickets(id)  ON DELETE CASCADE,
  CONSTRAINT fk_th_actor   FOREIGN KEY (actor_user_id) REFERENCES users(id),
  CONSTRAINT fk_th_from    FOREIGN KEY (from_status_id)REFERENCES statuses(id),
  CONSTRAINT fk_th_to      FOREIGN KEY (to_status_id)  REFERENCES statuses(id)
) ENGINE=InnoDB;

-- COMENTARIOS
CREATE TABLE IF NOT EXISTS ticket_comments (
  id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  ticket_id       BIGINT   NOT NULL,
  author_user_id  INT      NOT NULL,
  body            TEXT     NOT NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_tc_ticket (ticket_id),
  CONSTRAINT fk_tc_ticket FOREIGN KEY (ticket_id)      REFERENCES tickets(id) ON DELETE CASCADE,
  CONSTRAINT fk_tc_author FOREIGN KEY (author_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- ADJUNTOS (con tamaño y checksum)
CREATE TABLE IF NOT EXISTS ticket_attachments (
  id               BIGINT AUTO_INCREMENT PRIMARY KEY,
  ticket_id        BIGINT        NOT NULL,
  uploader_user_id INT           NOT NULL,
  file_name        VARCHAR(255)  NOT NULL,
  mime_type        VARCHAR(100)  NOT NULL,
  file_path        VARCHAR(500)  NOT NULL,
  file_size        BIGINT        NULL,
  checksum_sha256  VARCHAR(64)   NULL,
  created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_ta_ticket (ticket_id),
  CONSTRAINT fk_ta_ticket   FOREIGN KEY (ticket_id)        REFERENCES tickets(id) ON DELETE CASCADE,
  CONSTRAINT fk_ta_uploader FOREIGN KEY (uploader_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- WATCHERS
CREATE TABLE IF NOT EXISTS ticket_watchers (
  ticket_id BIGINT NOT NULL,
  user_id   INT    NOT NULL,
  PRIMARY KEY (ticket_id, user_id),
  CONSTRAINT fk_tw_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
  CONSTRAINT fk_tw_user   FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE
) ENGINE=InnoDB;

-- IA
CREATE TABLE IF NOT EXISTS ai_suggestions (
  id                     BIGINT AUTO_INCREMENT PRIMARY KEY,
  ticket_id              BIGINT   NOT NULL,
  model                  VARCHAR(80)  NOT NULL,
  suggested_category_id  INT       NULL,
  suggested_priority_id  INT       NULL,
  confidence             DECIMAL(5,4) NULL,
  summary                TEXT       NULL,
  recommendation         TEXT       NULL,
  accepted               TINYINT(1) NOT NULL DEFAULT 0,
  accepted_by            INT        NULL,
  created_at             DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ai_ticket   FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
  CONSTRAINT fk_ai_cat      FOREIGN KEY (suggested_category_id) REFERENCES categories(id),
  CONSTRAINT fk_ai_pri      FOREIGN KEY (suggested_priority_id) REFERENCES priorities(id),
  CONSTRAINT fk_ai_user     FOREIGN KEY (accepted_by) REFERENCES users(id)
) ENGINE=InnoDB;
