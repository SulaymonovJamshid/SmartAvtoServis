-- ============================================================
-- SmartAvtoServis - MySQL Database Schema
-- Encoding: UTF8MB4
-- ============================================================

CREATE DATABASE IF NOT EXISTS `smartavto_clean`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `smartavto_clean`;

-- ─── Users ────────────────────────────────────────────────────────────────────

CREATE TABLE `users` (
  `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `password`            VARCHAR(128)    NOT NULL,
  `last_login`          DATETIME(6)     NULL,
  `is_superuser`        TINYINT(1)      NOT NULL DEFAULT 0,
  `email`               VARCHAR(254)    NULL UNIQUE,
  `phone`               VARCHAR(20)     NULL UNIQUE,
  `first_name`          VARCHAR(100)    NOT NULL,
  `last_name`           VARCHAR(100)    NOT NULL,
  `role`                ENUM('user','service','admin') NOT NULL DEFAULT 'user',
  `is_verified`         TINYINT(1)      NOT NULL DEFAULT 0,
  `is_active`           TINYINT(1)      NOT NULL DEFAULT 1,
  `is_staff`            TINYINT(1)      NOT NULL DEFAULT 0,
  `avatar`              VARCHAR(200)    NULL,
  `preferred_language`  VARCHAR(5)      NOT NULL DEFAULT 'uz',
  `theme`               VARCHAR(10)     NOT NULL DEFAULT 'light',
  `created_at`          DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  INDEX `idx_users_email`  (`email`),
  INDEX `idx_users_phone`  (`phone`),
  INDEX `idx_users_role`   (`role`),
  INDEX `idx_users_active` (`is_active`),
  CONSTRAINT `chk_user_contact` CHECK (`email` IS NOT NULL OR `phone` IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── User Permissions (many-to-many) ─────────────────────────────────────────

CREATE TABLE `user_user_permissions` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`       BIGINT UNSIGNED NOT NULL,
  `permission_id` INT             NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_perm` (`user_id`, `permission_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user_groups` (
  `id`       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`  BIGINT UNSIGNED NOT NULL,
  `group_id` INT             NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_group` (`user_id`, `group_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── SMS Verifications ────────────────────────────────────────────────────────

CREATE TABLE `sms_verifications` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `phone`      VARCHAR(20)     NOT NULL,
  `code`       VARCHAR(6)      NOT NULL,
  `is_used`    TINYINT(1)      NOT NULL DEFAULT 0,
  `created_at` DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `expires_at` DATETIME(6)     NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_sms_phone`    (`phone`),
  INDEX `idx_sms_code`     (`code`),
  INDEX `idx_sms_expires`  (`expires_at`),
  INDEX `idx_sms_used`     (`is_used`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Services ─────────────────────────────────────────────────────────────────

CREATE TABLE `services` (
  `id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `owner_id`          BIGINT UNSIGNED NOT NULL,
  `name`              VARCHAR(200)    NOT NULL,
  `specializations`   JSON            NOT NULL DEFAULT ('[]'),
  `description`       TEXT            NULL,
  `experience_years`  SMALLINT UNSIGNED NOT NULL DEFAULT 0,

  -- Location
  `viloyat`           VARCHAR(50)     NOT NULL,
  `tuman`             VARCHAR(100)    NOT NULL DEFAULT '',
  `shahar`            VARCHAR(100)    NOT NULL DEFAULT '',
  `address`           VARCHAR(300)    NOT NULL DEFAULT '',
  `latitude`          DECIMAL(10,7)   NULL,
  `longitude`         DECIMAL(10,7)   NULL,

  -- Working hours
  `work_start`        TIME            NOT NULL DEFAULT '08:00:00',
  `work_end`          TIME            NOT NULL DEFAULT '18:00:00',
  `work_days`         JSON            NOT NULL DEFAULT ('[]'),
  `is_24h`            TINYINT(1)      NOT NULL DEFAULT 0,

  -- Pricing
  `price_from`        INT UNSIGNED    NOT NULL DEFAULT 0,
  `price_to`          INT UNSIGNED    NOT NULL DEFAULT 0,
  `price_description` TEXT            NULL,

  -- Contact
  `phone`             VARCHAR(20)     NOT NULL DEFAULT '',
  `website`           VARCHAR(200)    NULL,
  `telegram`          VARCHAR(100)    NULL,

  -- Status
  `is_approved`       TINYINT(1)      NOT NULL DEFAULT 0,
  `is_active`         TINYINT(1)      NOT NULL DEFAULT 1,

  `created_at`        DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at`        DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_owner` (`owner_id`),
  INDEX `idx_service_viloyat`    (`viloyat`),
  INDEX `idx_service_approved`   (`is_approved`),
  INDEX `idx_service_active`     (`is_active`),
  INDEX `idx_service_coords`     (`latitude`, `longitude`),
  INDEX `idx_service_name`       (`name`),
  FULLTEXT INDEX `ft_service_search` (`name`, `address`, `description`),
  FOREIGN KEY (`owner_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Service Images ───────────────────────────────────────────────────────────

CREATE TABLE `service_images` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `service_id`  BIGINT UNSIGNED NOT NULL,
  `image`       VARCHAR(200)    NOT NULL,
  `order`       SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `uploaded_at` DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  INDEX `idx_images_service` (`service_id`),
  INDEX `idx_images_order`   (`service_id`, `order`),
  CONSTRAINT `chk_max_images` CHECK (`order` < 6),
  FOREIGN KEY (`service_id`) REFERENCES `services`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Reviews ──────────────────────────────────────────────────────────────────

CREATE TABLE `reviews` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `service_id` BIGINT UNSIGNED NOT NULL,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `rating`     TINYINT UNSIGNED NOT NULL,
  `comment`    TEXT            NULL,
  `created_at` DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_review` (`service_id`, `user_id`),
  INDEX `idx_reviews_service` (`service_id`),
  INDEX `idx_reviews_user`    (`user_id`),
  INDEX `idx_reviews_rating`  (`rating`),
  CONSTRAINT `chk_rating_range` CHECK (`rating` BETWEEN 1 AND 5),
  FOREIGN KEY (`service_id`) REFERENCES `services`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`)    REFERENCES `users`(`id`)    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Favorites ────────────────────────────────────────────────────────────────

CREATE TABLE `favorites` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `service_id` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_favorite` (`user_id`, `service_id`),
  INDEX `idx_fav_user`    (`user_id`),
  INDEX `idx_fav_service` (`service_id`),
  FOREIGN KEY (`user_id`)    REFERENCES `users`(`id`)    ON DELETE CASCADE,
  FOREIGN KEY (`service_id`) REFERENCES `services`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Django system tables hint ────────────────────────────────────────────────
-- Run: python manage.py migrate
-- This will create: django_migrations, django_session, django_content_type,
--                   auth_permission, auth_group, django_admin_log

-- ─── Seed: Demo Admin User ────────────────────────────────────────────────────
-- Password: Admin@12345 (bcrypt hashed — change in production!)
INSERT INTO `users`
  (`password`, `is_superuser`, `email`, `phone`, `first_name`, `last_name`,
   `role`, `is_verified`, `is_active`, `is_staff`, `preferred_language`, `theme`)
VALUES
  ('pbkdf2_sha256$600000$seed$CHANGETHISPASSWORDHASH', 1,
   'admin@smartavto.uz', NULL, 'Admin', 'User',
   'admin', 1, 1, 1, 'uz', 'light');

-- ─── Seed: Sample Viloyat Services ───────────────────────────────────────────
-- (demo data — phone verification bypassed for seeds)
INSERT INTO `users`
  (`password`, `is_superuser`, `email`, `phone`, `first_name`, `last_name`,
   `role`, `is_verified`, `is_active`, `is_staff`, `preferred_language`, `theme`)
VALUES
  ('pbkdf2_sha256$600000$demo$hash1', 0, NULL, '+998901111111', 'Jasur', 'Toshmatov',  'service', 1, 1, 0, 'uz', 'light'),
  ('pbkdf2_sha256$600000$demo$hash2', 0, NULL, '+998902222222', 'Dilshod', 'Rahimov',  'service', 1, 1, 0, 'uz', 'light'),
  ('pbkdf2_sha256$600000$demo$hash3', 0, 'user1@test.com', NULL, 'Kamol', 'Yusupov',  'user',    1, 1, 0, 'uz', 'dark');

INSERT INTO `services`
  (`owner_id`, `name`, `specializations`, `description`, `experience_years`,
   `viloyat`, `tuman`, `address`, `latitude`, `longitude`,
   `work_start`, `work_end`, `work_days`, `is_24h`,
   `price_from`, `price_to`, `phone`, `is_approved`, `is_active`)
VALUES
  (2, 'AutoMaster Pro',
   '["engine","electrical","diagnostics","oil_change"]',
   'Toshkentdagi eng ishonchli avto servis markazlaridan biri. 10 yillik tajriba.',
   10, 'toshkent_sh', 'Yunusobod', 'Yunusobod 19-mavze, 45-uy',
   41.3345678, 69.3012345,
   '08:00:00', '20:00:00', '["Mon","Tue","Wed","Thu","Fri","Sat"]', 0,
   50000, 500000, '+998901111111', 1, 1),

  (3, 'SpeedFix Servis',
   '["general","brake","suspension","tires"]',
   'Tez va sifatli ta\'mirlash xizmati. Barcha markali avtomobillar qabul qilinadi.',
   7, 'toshkent_sh', 'Chilonzor', 'Chilonzor 9-kvartal, 12-uy',
   41.2798765, 69.2234567,
   '09:00:00', '19:00:00', '["Mon","Tue","Wed","Thu","Fri"]', 0,
   30000, 300000, '+998902222222', 1, 1);

-- ─── Sample Reviews ────────────────────────────────────────────────────────────
INSERT INTO `reviews` (`service_id`, `user_id`, `rating`, `comment`)
VALUES
  (1, 4, 5, 'Juda yaxshi servis! Dvigatelimdagi muammo bir kunda hal qilindi.'),
  (2, 4, 4, 'Tezkor xizmat, narx ham qulay. Tavsiya qilaman.');

-- ─── Useful Views ─────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW `v_service_stats` AS
SELECT
  s.id,
  s.name,
  s.viloyat,
  s.tuman,
  s.is_approved,
  s.is_active,
  COALESCE(AVG(r.rating), 0)     AS avg_rating,
  COUNT(r.id)                     AS review_count,
  COUNT(f.id)                     AS favorite_count
FROM `services` s
LEFT JOIN `reviews`   r ON r.service_id = s.id
LEFT JOIN `favorites` f ON f.service_id = s.id
GROUP BY s.id;

CREATE OR REPLACE VIEW `v_user_summary` AS
SELECT
  u.id,
  u.first_name,
  u.last_name,
  u.email,
  u.phone,
  u.role,
  u.is_verified,
  u.is_active,
  u.created_at,
  COUNT(DISTINCT rv.id)  AS reviews_given,
  COUNT(DISTINCT fv.id)  AS favorites_count
FROM `users` u
LEFT JOIN `reviews`   rv ON rv.user_id = u.id
LEFT JOIN `favorites` fv ON fv.user_id = u.id
GROUP BY u.id;

-- ─── Stored procedure: get nearby services ────────────────────────────────────

DELIMITER $$
CREATE PROCEDURE `sp_nearby_services`(
  IN  p_lat    DOUBLE,
  IN  p_lng    DOUBLE,
  IN  p_radius DOUBLE,   -- km
  IN  p_limit  INT
)
BEGIN
  SELECT
    s.id, s.name, s.address, s.viloyat, s.phone, s.is_24h,
    s.latitude, s.longitude,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(r.id) AS review_count,
    (
      6371 * ACOS(
        COS(RADIANS(p_lat)) * COS(RADIANS(s.latitude)) *
        COS(RADIANS(s.longitude) - RADIANS(p_lng)) +
        SIN(RADIANS(p_lat)) * SIN(RADIANS(s.latitude))
      )
    ) AS distance_km
  FROM `services` s
  LEFT JOIN `reviews` r ON r.service_id = s.id
  WHERE s.is_approved = 1 AND s.is_active = 1
    AND s.latitude IS NOT NULL AND s.longitude IS NOT NULL
  GROUP BY s.id
  HAVING distance_km <= p_radius
  ORDER BY distance_km ASC
  LIMIT p_limit;
END$$
DELIMITER ;

-- Usage: CALL sp_nearby_services(41.2995, 69.2401, 10, 20);
