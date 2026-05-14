-- 淘宝用户行为数据 - 表结构
-- 总行数: 99,457

CREATE TABLE `user_behavior` (
  `invoice_no` varchar(20) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `gender` varchar(10) NOT NULL,
  `age` int NOT NULL,
  `category` varchar(30) NOT NULL,
  `quantity` int NOT NULL,
  `price` double NOT NULL,
  `payment_method` varchar(20) NOT NULL,
  `invoice_date` datetime NOT NULL,
  `gmv` double DEFAULT NULL,
  `age_group` varchar(10) DEFAULT NULL,
  `yr` int DEFAULT NULL,
  `mth` int DEFAULT NULL,
  `yr_mth` varchar(7) DEFAULT NULL,
  `cust_tier` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`invoice_no`),
  KEY `idx_inv_date` (`invoice_date`),
  KEY `idx_cat` (`category`),
  KEY `idx_cust` (`customer_id`),
  KEY `idx_yr_mth` (`yr_mth`),
  KEY `idx_age_grp` (`age_group`),
  KEY `idx_cust_tier` (`cust_tier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
