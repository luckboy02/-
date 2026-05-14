-- ============================================================
-- 淘宝用户行为分析 - SQL 聚合查询
-- 数据库: taobao_analysis  表: user_behavior
-- ============================================================

-- ============================================================
-- 主题 A：经营健康度
-- ============================================================

-- A1: 经营KPI汇总
SELECT
    COUNT(*)                                  AS total_orders,
    ROUND(SUM(gmv), 0)                        AS total_gmv,
    ROUND(AVG(gmv), 2)                        AS avg_order_value,
    ROUND(COUNT(*) / COUNT(DISTINCT yr_mth), 0) AS avg_monthly_orders,
    COUNT(DISTINCT customer_id)               AS total_customers,
    COUNT(DISTINCT category)                  AS total_categories,
    MIN(invoice_date)                         AS earliest_date,
    MAX(invoice_date)                         AS latest_date
FROM user_behavior;

-- A2: 月度经营趋势
SELECT
    yr_mth,
    COUNT(*)                AS orders,
    ROUND(SUM(gmv), 0)      AS total_gmv,
    ROUND(AVG(gmv), 2)      AS avg_order_value
FROM user_behavior
GROUP BY yr_mth
ORDER BY yr_mth;

-- A3: 年度同比 (2021 vs 2022)
SELECT
    yr,
    COUNT(*)                AS orders,
    ROUND(SUM(gmv), 0)      AS total_gmv,
    ROUND(AVG(gmv), 2)      AS avg_order_value
FROM user_behavior
WHERE yr IN (2021, 2022)
GROUP BY yr
ORDER BY yr;

-- ============================================================
-- 主题 B：客群洞察
-- ============================================================

-- B1: 年龄分布统计
SELECT
    age_group,
    COUNT(*)                AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
    ROUND(AVG(age), 1)      AS avg_age,
    ROUND(AVG(gmv), 2)      AS avg_gmv
FROM user_behavior
GROUP BY age_group
ORDER BY age_group;

-- B1-补充: 性别分布
SELECT
    gender,
    COUNT(*)                AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
    ROUND(AVG(gmv), 2)      AS avg_gmv
FROM user_behavior
GROUP BY gender;

-- B1-补充: 年龄×性别交叉
SELECT
    age_group,
    gender,
    COUNT(*)                AS customer_count
FROM user_behavior
GROUP BY age_group, gender
ORDER BY age_group, gender;

-- B2: 消费力分层对比
SELECT
    cust_tier,
    COUNT(*)                AS customer_count,
    ROUND(SUM(gmv), 0)      AS total_gmv,
    ROUND(AVG(gmv), 2)      AS avg_gmv,
    ROUND(MIN(gmv), 2)      AS min_gmv,
    ROUND(MAX(gmv), 2)      AS max_gmv,
    ROUND(AVG(age), 1)      AS avg_age,
    ROUND(SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS female_pct
FROM user_behavior
GROUP BY cust_tier
ORDER BY avg_gmv;

-- B3: 客群×品类偏好 (三维聚合，用于TGI计算)
SELECT
    age_group,
    gender,
    category,
    COUNT(*)                AS customer_count
FROM user_behavior
GROUP BY age_group, gender, category
ORDER BY age_group, gender, category;

-- ============================================================
-- 主题 C：品类策略
-- ============================================================

-- C1: 品类贡献分析 (GMV帕累托)
SELECT
    category,
    COUNT(*)                                 AS orders,
    ROUND(SUM(gmv), 0)                       AS total_gmv,
    ROUND(AVG(gmv), 2)                       AS avg_order_value,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1)   AS order_pct,
    ROUND(SUM(gmv) * 100.0 / SUM(SUM(gmv)) OVER(), 1)   AS gmv_pct
FROM user_behavior
GROUP BY category
ORDER BY total_gmv DESC;

-- C2: 品类价格结构 (每个品类每个价位的订单量)
SELECT
    category,
    price,
    COUNT(*)                AS orders,
    ROUND(AVG(quantity), 2) AS avg_quantity
FROM user_behavior
GROUP BY category, price
ORDER BY category, price;

-- C3: 量价关系
SELECT
    category,
    ROUND(AVG(price), 2)    AS avg_price,
    ROUND(AVG(quantity), 2) AS avg_quantity,
    ROUND(SUM(gmv), 0)      AS total_gmv,
    COUNT(*)                AS orders
FROM user_behavior
GROUP BY category
ORDER BY avg_price;

-- C3-补充: 品类×年龄段偏好 (用于客群偏好深度分析)
SELECT
    category,
    age_group,
    COUNT(*)                AS customer_count,
    ROUND(AVG(gmv), 2)      AS avg_gmv
FROM user_behavior
GROUP BY category, age_group
ORDER BY category, age_group;

-- ============================================================
-- 主题 D：交易行为
-- ============================================================

-- D1: 支付方式全景
SELECT
    payment_method,
    COUNT(*)                                     AS orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
    ROUND(SUM(gmv), 0)                           AS total_gmv,
    ROUND(AVG(gmv), 2)                           AS avg_order_value
FROM user_behavior
GROUP BY payment_method
ORDER BY orders DESC;

-- D1-补充: 支付方式月度趋势
SELECT
    yr_mth,
    payment_method,
    COUNT(*)                AS orders,
    ROUND(SUM(gmv), 0)      AS total_gmv
FROM user_behavior
GROUP BY yr_mth, payment_method
ORDER BY yr_mth, payment_method;

-- D2: 品类×支付方式交叉
SELECT
    category,
    payment_method,
    COUNT(*)                AS orders,
    ROUND(AVG(gmv), 2)      AS avg_gmv
FROM user_behavior
GROUP BY category, payment_method
ORDER BY category, payment_method;

-- D2-补充: 年龄×支付方式
SELECT
    age_group,
    payment_method,
    COUNT(*)                AS orders,
    ROUND(AVG(gmv), 2)      AS avg_gmv
FROM user_behavior
GROUP BY age_group, payment_method
ORDER BY age_group, payment_method;

-- D3: 购买数量规律 - 品类×quantity
SELECT
    category,
    quantity,
    COUNT(*)                AS orders,
    ROUND(AVG(gmv), 2)      AS avg_gmv
FROM user_behavior
GROUP BY category, quantity
ORDER BY category, quantity;

-- D3-补充: 年龄×quantity
SELECT
    age_group,
    quantity,
    COUNT(*)                AS orders
FROM user_behavior
GROUP BY age_group, quantity
ORDER BY age_group, quantity;
