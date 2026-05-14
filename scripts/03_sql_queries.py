"""
阶段三：SQL 聚合查询
功能：执行所有分析查询，打印结果并保存 CSV
"""
import pandas as pd
import pymysql
import os

OUT_DIR = r"D:\Modeling code\数据分析项目\淘宝用户行为数据分析\sql"
os.makedirs(OUT_DIR, exist_ok=True)

conn = pymysql.connect(
    host="localhost", port=3306, user="root", password="wq010205",
    database="taobao_analysis", charset="utf8mb4",
)

def query(label, sql):
    """执行SQL并打印+保存"""
    df = pd.read_sql(sql, conn)
    print(f"\n{'='*60}")
    print(f" {label}")
    print(f"{'='*60}")
    print(df.to_string(index=False))
    # 保存CSV（仅作为中间数据参考，Power BI直接连MySQL）
    filename = label.replace(" ", "_").replace("/", "_") + ".csv"
    df.to_csv(os.path.join(OUT_DIR, filename), index=False, encoding="utf-8-sig")
    return df

# ============================================================
# 主题 A：经营健康度
# ============================================================
print("\n" + "=" * 60)
print(" 主题 A：经营健康度")
print("=" * 60)

query("A1_KPI汇总", """
    SELECT
        COUNT(*) AS total_orders,
        ROUND(SUM(gmv), 0) AS total_gmv,
        ROUND(AVG(gmv), 2) AS avg_order_value,
        ROUND(COUNT(*)/COUNT(DISTINCT yr_mth), 0) AS avg_monthly_orders,
        COUNT(DISTINCT customer_id) AS total_customers
    FROM user_behavior;
""")

monthly = query("A2_月度经营趋势", """
    SELECT yr_mth, COUNT(*) AS orders,
           ROUND(SUM(gmv),0) AS total_gmv,
           ROUND(AVG(gmv),2) AS avg_order_value
    FROM user_behavior GROUP BY yr_mth ORDER BY yr_mth;
""")

query("A3_年度同比", """
    SELECT yr, COUNT(*) AS orders,
           ROUND(SUM(gmv),0) AS total_gmv,
           ROUND(AVG(gmv),2) AS avg_order_value
    FROM user_behavior WHERE yr IN (2021,2022)
    GROUP BY yr ORDER BY yr;
""")

# ============================================================
# 主题 B：客群洞察
# ============================================================
print("\n" + "=" * 60)
print(" 主题 B：客群洞察")
print("=" * 60)

query("B1_年龄分布", """
    SELECT age_group, COUNT(*) AS customer_count,
           ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 1) AS pct,
           ROUND(AVG(age),1) AS avg_age,
           ROUND(AVG(gmv),2) AS avg_gmv
    FROM user_behavior GROUP BY age_group ORDER BY age_group;
""")

query("B1_性别分布", """
    SELECT gender, COUNT(*) AS customer_count,
           ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 1) AS pct,
           ROUND(AVG(gmv),2) AS avg_gmv
    FROM user_behavior GROUP BY gender;
""")

query("B1_年龄性别交叉", """
    SELECT age_group, gender, COUNT(*) AS customer_count
    FROM user_behavior GROUP BY age_group, gender ORDER BY age_group, gender;
""")

query("B2_消费力分层", """
    SELECT cust_tier, COUNT(*) AS customer_count,
           ROUND(SUM(gmv),0) AS total_gmv,
           ROUND(AVG(gmv),2) AS avg_gmv,
           ROUND(MIN(gmv),2) AS min_gmv,
           ROUND(MAX(gmv),2) AS max_gmv,
           ROUND(AVG(age),1) AS avg_age,
           ROUND(SUM(CASE WHEN gender='Female' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS female_pct
    FROM user_behavior GROUP BY cust_tier ORDER BY avg_gmv;
""")

tgi_data = query("B3_客群品类偏好_TGI数据", """
    SELECT age_group, gender, category, COUNT(*) AS customer_count
    FROM user_behavior GROUP BY age_group, gender, category
    ORDER BY age_group, gender, category;
""")

# ============================================================
# 主题 C：品类策略
# ============================================================
print("\n" + "=" * 60)
print(" 主题 C：品类策略")
print("=" * 60)

query("C1_品类贡献", """
    SELECT category, COUNT(*) AS orders,
           ROUND(SUM(gmv),0) AS total_gmv,
           ROUND(AVG(gmv),2) AS avg_order_value,
           ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS order_pct,
           ROUND(SUM(gmv)*100.0/SUM(SUM(gmv)) OVER(),1) AS gmv_pct
    FROM user_behavior GROUP BY category ORDER BY total_gmv DESC;
""")

query("C2_品类价格结构", """
    SELECT category, price, COUNT(*) AS orders,
           ROUND(AVG(quantity),2) AS avg_quantity
    FROM user_behavior GROUP BY category, price ORDER BY category, price;
""")

query("C3_量价关系", """
    SELECT category, ROUND(AVG(price),2) AS avg_price,
           ROUND(AVG(quantity),2) AS avg_quantity,
           ROUND(SUM(gmv),0) AS total_gmv,
           COUNT(*) AS orders
    FROM user_behavior GROUP BY category ORDER BY avg_price;
""")

# ============================================================
# 主题 D：交易行为
# ============================================================
print("\n" + "=" * 60)
print(" 主题 D：交易行为")
print("=" * 60)

query("D1_支付方式全景", """
    SELECT payment_method, COUNT(*) AS orders,
           ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct,
           ROUND(SUM(gmv),0) AS total_gmv,
           ROUND(AVG(gmv),2) AS avg_order_value
    FROM user_behavior GROUP BY payment_method ORDER BY orders DESC;
""")

query("D1_支付月度趋势", """
    SELECT yr_mth, payment_method, COUNT(*) AS orders,
           ROUND(SUM(gmv),0) AS total_gmv
    FROM user_behavior GROUP BY yr_mth, payment_method ORDER BY yr_mth, payment_method;
""")

query("D2_品类支付交叉", """
    SELECT category, payment_method, COUNT(*) AS orders,
           ROUND(AVG(gmv),2) AS avg_gmv
    FROM user_behavior GROUP BY category, payment_method ORDER BY category, payment_method;
""")

query("D2_年龄支付交叉", """
    SELECT age_group, payment_method, COUNT(*) AS orders,
           ROUND(AVG(gmv),2) AS avg_gmv
    FROM user_behavior GROUP BY age_group, payment_method ORDER BY age_group, payment_method;
""")

query("D3_品类购买数量", """
    SELECT category, quantity, COUNT(*) AS orders,
           ROUND(AVG(gmv),2) AS avg_gmv
    FROM user_behavior GROUP BY category, quantity ORDER BY category, quantity;
""")

query("D3_年龄购买数量", """
    SELECT age_group, quantity, COUNT(*) AS orders
    FROM user_behavior GROUP BY age_group, quantity ORDER BY age_group, quantity;
""")

conn.close()
print(f"\n阶段三完成! 所有查询结果已输出。")
print(f"CSV 文件保存在: {OUT_DIR}")
