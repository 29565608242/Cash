-- ============================================================
-- 线上记账系统 - 完整数据库初始化脚本（v2.0）
-- 说明: 应用启动时会自动通过 SQLAlchemy 执行 db.create_all()
--       此文件仅作为数据库结构的参考和手动初始化使用
-- 共 15 张表：users, categories, accounts, transactions,
--   budgets, budget_category_items, export_tasks, file_uploads,
--   ledgers, ledger_members, invite_codes, loans, ai_analysis,
--   recurring_rules, money_change_logs
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 1. 用户表
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'default_avatar.svg',
  `email` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `username` (`username`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 2. 分类表
-- ----------------------------
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'expense',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `name` (`name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 3. 账户表
-- ----------------------------
DROP TABLE IF EXISTS `accounts`;
CREATE TABLE `accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `balance` decimal(10,2) DEFAULT 0,
  `account_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'cash',
  `user_id` int DEFAULT NULL,
  `ledger_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`),
  KEY `ledger_id` (`ledger_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 4. 交易记录表
-- ----------------------------
DROP TABLE IF EXISTS `transactions`;
CREATE TABLE `transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'income/expense',
  `amount` decimal(10,2) NOT NULL,
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `time` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `account_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `currency` varchar(10) DEFAULT 'CNY',
  `original_amount` decimal(10,2) DEFAULT NULL COMMENT '原始币种金额',
  `exchange_rate` decimal(10,6) DEFAULT NULL COMMENT '汇率',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `reimbursement_status` varchar(20) DEFAULT 'none' COMMENT 'none/pending/partial/reimbursed',
  `reimbursed_amount` decimal(10,2) DEFAULT 0,
  `write_off_id` int DEFAULT NULL COMMENT '关联的报销收入交易ID',
  `ledger_id` int DEFAULT NULL,
  `payer_user_id` int DEFAULT NULL COMMENT '实际付款人',
  `split_details` text DEFAULT NULL COMMENT '分摊详情(JSON)',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `account_id` (`account_id`),
  KEY `user_id` (`user_id`),
  KEY `ledger_id` (`ledger_id`),
  KEY `fk_write_off` (`write_off_id`),
  CONSTRAINT `fk_write_off` FOREIGN KEY (`write_off_id`) REFERENCES `transactions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 5. 预算表
-- ----------------------------
DROP TABLE IF EXISTS `budgets`;
CREATE TABLE `budgets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `ledger_id` int DEFAULT NULL,
  `account_id` int DEFAULT NULL,
  `month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`),
  KEY `account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 6. 预算分类明细表
-- ----------------------------
DROP TABLE IF EXISTS `budget_category_items`;
CREATE TABLE `budget_category_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `budget_id` int NOT NULL,
  `category_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `budget_id` (`budget_id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `budget_category_items_ibfk_1` FOREIGN KEY (`budget_id`) REFERENCES `budgets` (`id`),
  CONSTRAINT `budget_category_items_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 7. 导出任务表
-- ----------------------------
DROP TABLE IF EXISTS `export_tasks`;
CREATE TABLE `export_tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `status` varchar(20) DEFAULT 'pending',
  `progress` int DEFAULT 0,
  `file_format` varchar(10) NOT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `file_size` int DEFAULT NULL,
  `filters` text DEFAULT NULL,
  `total_records` int DEFAULT 0,
  `error_message` text DEFAULT NULL,
  `email_to` varchar(200) DEFAULT NULL,
  `email_sent` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 8. 文件上传表
-- ----------------------------
DROP TABLE IF EXISTS `file_uploads`;
CREATE TABLE `file_uploads` (
  `id` int NOT NULL AUTO_INCREMENT,
  `upload_id` varchar(36) NOT NULL,
  `user_id` int NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `file_format` varchar(10) NOT NULL,
  `total_rows` int DEFAULT 0,
  `columns` text DEFAULT NULL,
  `preview_data` text DEFAULT NULL,
  `status` varchar(20) DEFAULT 'uploaded',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `upload_id` (`upload_id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 9. 账本表
-- ----------------------------
DROP TABLE IF EXISTS `ledgers`;
CREATE TABLE `ledgers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `owner_id` int NOT NULL,
  `currency` varchar(10) DEFAULT 'CNY',
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `owner_id` (`owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 10. 账本成员表
-- ----------------------------
DROP TABLE IF EXISTS `ledger_members`;
CREATE TABLE `ledger_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ledger_id` int NOT NULL,
  `user_id` int NOT NULL,
  `role` varchar(20) DEFAULT 'viewer' COMMENT 'viewer/editor/manager',
  `joined_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uq_ledger_user` (`ledger_id`, `user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `ledger_members_ibfk_1` FOREIGN KEY (`ledger_id`) REFERENCES `ledgers` (`id`),
  CONSTRAINT `ledger_members_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 11. 邀请码表
-- ----------------------------
DROP TABLE IF EXISTS `invite_codes`;
CREATE TABLE `invite_codes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ledger_id` int NOT NULL,
  `code` varchar(64) NOT NULL,
  `created_by` int NOT NULL,
  `max_uses` int DEFAULT 0 COMMENT '0=无限制',
  `used_count` int DEFAULT 0,
  `expires_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `code` (`code`),
  KEY `ledger_id` (`ledger_id`),
  KEY `created_by` (`created_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 12. 借贷记录表
-- ----------------------------
DROP TABLE IF EXISTS `loans`;
CREATE TABLE `loans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `ledger_id` int DEFAULT NULL,
  `type` varchar(10) NOT NULL COMMENT 'borrow(借入)/lend(借出)',
  `counterparty` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `repaid_amount` decimal(10,2) DEFAULT 0 COMMENT '已还/已收金额',
  `date` varchar(20) NOT NULL,
  `due_date` varchar(20) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'active' COMMENT 'active/settled',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`),
  KEY `ledger_id` (`ledger_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 13. AI分析记录表
-- ----------------------------
DROP TABLE IF EXISTS `ai_analysis`;
CREATE TABLE `ai_analysis` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `period` varchar(20) NOT NULL COMMENT 'month/week/year',
  `start_date` varchar(20) NOT NULL,
  `end_date` varchar(20) NOT NULL,
  `analysis_content` text NOT NULL,
  `model_used` varchar(50) NOT NULL,
  `prompt_tokens` int DEFAULT 0,
  `completion_tokens` int DEFAULT 0,
  `total_tokens` int DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 14. 周期账单规则表
-- ----------------------------
DROP TABLE IF EXISTS `recurring_rules`;
CREATE TABLE `recurring_rules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(10) NOT NULL COMMENT 'income/expense',
  `period` varchar(20) NOT NULL COMMENT 'daily/weekly/monthly/yearly',
  `interval_value` int DEFAULT 1,
  `start_date` varchar(20) NOT NULL,
  `end_date` varchar(20) DEFAULT NULL,
  `next_date` varchar(20) NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` int NOT NULL,
  `ledger_id` int DEFAULT NULL,
  `account_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`),
  KEY `ledger_id` (`ledger_id`),
  KEY `account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- 15. 资金变动日志表
-- ----------------------------
DROP TABLE IF EXISTS `money_change_logs`;
CREATE TABLE `money_change_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `ledger_id` int DEFAULT NULL,
  `account_id` int DEFAULT NULL,
  `action_type` varchar(20) NOT NULL COMMENT 'create/update/delete/adjust/repay/import',
  `entity_type` varchar(20) NOT NULL COMMENT 'transaction/account/loan',
  `entity_id` int DEFAULT NULL,
  `amount_change` decimal(10,2) DEFAULT 0,
  `balance_before` decimal(10,2) DEFAULT NULL,
  `balance_after` decimal(10,2) DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  `details` text DEFAULT NULL COMMENT '额外上下文(JSON)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`),
  KEY `ledger_id` (`ledger_id`),
  KEY `account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 默认数据
-- ============================================================

-- ----------------------------
-- 默认分类
-- ----------------------------
INSERT IGNORE INTO `categories` (`name`, `type`) VALUES
-- 收入类
('工资', 'income'),
('奖金', 'income'),
('投资收益', 'income'),
('兼职', 'income'),
('红包', 'income'),
('报销收入', 'income'),
('其他收入', 'income'),
-- 支出类
('餐饮', 'expense'),
('交通', 'expense'),
('购物', 'expense'),
('娱乐', 'expense'),
('医疗', 'expense'),
('住房', 'expense'),
('教育', 'expense'),
('通讯', 'expense'),
('其他支出', 'expense');

-- ----------------------------
-- 默认用户 (密码: admin123 / user123)
-- ----------------------------
INSERT IGNORE INTO `users` (`username`, `password_hash`, `is_admin`, `avatar`, `created_at`) VALUES
('admin', 'scrypt:32768:8:1$SRtDXCRlCvd0ldLH$8fb9dcc3ca8c8774c68d151b37c48ec13f62f22088d7e9c31d3e2518a191e2e06fdcf8f637788840023a8ce41ea2e330e9a46d48f87d260580028760560a9cd', 1, 'default_avatar.svg', NOW()),
('user', 'scrypt:32768:8:1$SRtDXCRlCvd0ldLH$8fb9dcc3ca8c8774c68d151b37c48ec13f62f22088d7e9c31d3e2518a191e2e06fdcf8f637788840023a8ce41ea2e330e9a46d48f87d260580028760560a9cd', 0, 'default_avatar.svg', NOW());

SET FOREIGN_KEY_CHECKS = 1;
