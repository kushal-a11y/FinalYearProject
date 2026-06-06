-- ============================================================================
--  Shubh Vivah — Schema migration for the matchmaker upgrade
-- ----------------------------------------------------------------------------
--  Apply this to an EXISTING `matrimony_db` database that already contains the
--  original `user_profile` table. (For a brand-new database, app.py's /init-db
--  route + SQLAlchemy db.create_all() will build everything automatically and
--  this file is not required.)
--
--  Usage:
--      mysql -u <user> -p matrimony_db < migrations.sql
--
--  Adds: phone, profile image filename, and REAL PAN identity-verification
--        columns to user_profile, plus the new chat_message table.
--  Safe to re-run: uses IF NOT EXISTS guards where MySQL supports them.
-- ============================================================================

-- ---- 1. New columns on user_profile -------------------------------------- --
-- MySQL 8.0+ supports IF NOT EXISTS on ADD COLUMN. On older servers, remove
-- the "IF NOT EXISTS" tokens (the columns will error only if already present).

ALTER TABLE user_profile
    ADD COLUMN IF NOT EXISTS Phone          VARCHAR(20)  NULL,
    ADD COLUMN IF NOT EXISTS ImageFilename  VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS PanNumber      VARCHAR(10)  NULL,
    ADD COLUMN IF NOT EXISTS PanHolderName  VARCHAR(120) NULL,
    ADD COLUMN IF NOT EXISTS PanVerified    TINYINT(1)   NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS PanVerifiedAt  DATETIME     NULL;

-- Enforce one verified PAN per account (a PAN can back only one profile).
-- Wrapped so a re-run won't fail if the index already exists.
SET @idx := (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name   = 'user_profile'
      AND index_name   = 'uq_user_profile_pan'
);
SET @sql := IF(@idx = 0,
    'ALTER TABLE user_profile ADD CONSTRAINT uq_user_profile_pan UNIQUE (PanNumber)',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---- 2. Chat messages table ---------------------------------------------- --
CREATE TABLE IF NOT EXISTS chat_message (
    id          INT          NOT NULL AUTO_INCREMENT,
    sender_id   INT          NOT NULL,
    receiver_id INT          NOT NULL,
    content     TEXT         NOT NULL,
    timestamp   DATETIME     NULL,
    is_read     TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_chat_sender   (sender_id),
    KEY idx_chat_receiver (receiver_id),
    KEY idx_chat_time     (timestamp),
    CONSTRAINT fk_chat_sender
        FOREIGN KEY (sender_id)   REFERENCES user_profile (UserID) ON DELETE CASCADE,
    CONSTRAINT fk_chat_receiver
        FOREIGN KEY (receiver_id) REFERENCES user_profile (UserID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
--  Done.
-- ============================================================================
