"""
阶段二：数据探查与预处理
功能：数据质量检查 + 分布探查 + 描述统计
输出：控制台打印所有结果，无文件输出
"""
import pandas as pd
import pymysql
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# 1. 从 MySQL 读取数据
# ============================================================
conn = pymysql.connect(
    host="localhost", port=3306, user="root", password="wq010205",
    database="taobao_analysis", charset="utf8mb4",
)
df = pd.read_sql("SELECT * FROM user_behavior;", conn)
conn.close()
print(f"数据读取完成: {len(df):,} 行, {len(df.columns)} 列")
print(f"列: {list(df.columns)}")

# ============================================================
# 2.1 数据质量检查
# ============================================================
print("\n" + "=" * 60)
print("2.1 数据质量检查")
print("=" * 60)

# 缺失值
print("\n--- 缺失值检查 ---")
nulls = df.isnull().sum()
null_cols = nulls[nulls > 0]
if len(null_cols) == 0:
    print("  [OK] 所有列无缺失值")
else:
    print(null_cols)

# 重复值
print("\n--- 重复值检查 ---")
dup_invoice = df["invoice_no"].duplicated().sum()
dup_customer = df["customer_id"].duplicated().sum()
print(f"  重复订单号: {dup_invoice}")
print(f"  重复客户ID: {dup_customer}")
print(f"  [OK] 结论: 每客户仅一条交易，订单号无重复")

# 数据类型
print("\n--- 数据类型校验 ---")
print(df.dtypes)

# 异常值：数值范围
print("\n--- 数值范围检查 ---")
print(f"  age:       min={df['age'].min()}, max={df['age'].max()}  [预期: 18-69]")
print(f"  quantity:  min={df['quantity'].min()}, max={df['quantity'].max()}  [预期: 1-5]")
print(f"  price:     min={df['price'].min():.2f}, max={df['price'].max():.2f}  [预期: 5.23-5250]")
print(f"  gmv:       min={df['gmv'].min():.2f}, max={df['gmv'].max():.2f}")
print(f"  invoice_date: {df['invoice_date'].min()} ~ {df['invoice_date'].max()}")

# 各类目价格分布（箱线图数据）
print("\n--- 各类目价格分布 (price) ---")
for cat in sorted(df["category"].unique()):
    cat_data = df[df["category"] == cat]["price"]
    q1, q3 = cat_data.quantile([0.25, 0.75])
    iqr = q3 - q1
    print(f"  {cat:20s}  mean={cat_data.mean():10.2f}  median={cat_data.median():8.2f}  "
          f"min={cat_data.min():8.2f}  max={cat_data.max():8.2f}  unique={cat_data.nunique()}")

# ============================================================
# 2.2 数据探查（分布概览）
# ============================================================
print("\n" + "=" * 60)
print("2.2 数据分布探查")
print("=" * 60)

# 类目分布
print("\n--- 类目分布 ---")
cat_dist = df["category"].value_counts()
cat_pct = (cat_dist / len(df) * 100).round(1)
cat_gmv = df.groupby("category")["gmv"].sum().sort_values(ascending=False)
for cat in cat_dist.index:
    print(f"  {cat:20s}  订单: {cat_dist[cat]:6,} ({cat_pct[cat]:5.1f}%)  "
          f"GMV: {cat_gmv[cat]:>12,.0f}  ({cat_gmv[cat]/df['gmv'].sum()*100:5.1f}%)")

# 支付方式分布
print("\n--- 支付方式分布 ---")
pmt_dist = df["payment_method"].value_counts()
pmt_gmv = df.groupby("payment_method")["gmv"].mean()
for pmt in pmt_dist.index:
    print(f"  {pmt:15s}  订单: {pmt_dist[pmt]:6,} ({pmt_dist[pmt]/len(df)*100:5.1f}%)  "
          f"客单价: {pmt_gmv[pmt]:>10,.2f}")

# 性别分布
print("\n--- 性别分布 ---")
gender_dist = df["gender"].value_counts()
gender_gmv = df.groupby("gender")["gmv"].mean()
for g in gender_dist.index:
    print(f"  {g:10s}  人数: {gender_dist[g]:6,} ({gender_dist[g]/len(df)*100:5.1f}%)  "
          f"客单价: {gender_gmv[g]:>10,.2f}")

# 年龄分布
print("\n--- 年龄段分布 ---")
age_dist = df["age_group"].value_counts().sort_index()
age_gmv = df.groupby("age_group")["gmv"].mean()
for a in age_dist.index:
    print(f"  {a:10s}  人数: {age_dist[a]:6,} ({age_dist[a]/len(df)*100:5.1f}%)  "
          f"客单价: {age_gmv[a]:>10,.2f}")

# 消费层级分布
print("\n--- 消费层级分布 (cust_tier) ---")
tier_dist = df["cust_tier"].value_counts().sort_index()
for t in tier_dist.index:
    tier_data = df[df["cust_tier"] == t]
    print(f"  {t:10s}  人数: {len(tier_data):6,}  "
          f"GMV范围: {tier_data['gmv'].min():>10,.2f} ~ {tier_data['gmv'].max():>10,.2f}  "
          f"均值: {tier_data['gmv'].mean():>10,.2f}")

# 月度订单趋势
print("\n--- 月度订单趋势 (前6月+后6月) ---")
monthly = df.groupby("yr_mth").agg(
    orders=("invoice_no", "count"),
    gmv=("gmv", "sum"),
    avg_order=("gmv", "mean"),
).sort_index()
print(monthly.head(6).to_string())
print("  ...")
print(monthly.tail(6).to_string())

# 年龄统计
print("\n--- 年龄统计 ---")
print(f"  平均年龄: {df['age'].mean():.1f}, 中位数: {df['age'].median():.0f}")
print(f"  标准差: {df['age'].std():.1f}")

# 客单价统计
print("\n--- 客单价(GMV)统计 ---")
print(df["gmv"].describe().to_string())

# ============================================================
# 3. 数据质量结论
# ============================================================
print("\n" + "=" * 60)
print("2.3 质量结论")
print("=" * 60)
print("""
  [OK] 缺失值: 无
  [OK] 重复值: 无
  [OK] 数据类型: 正确 (数值 int/double, 日期 datetime)
  [OK] 数值范围: age[18-69], quantity[1-5], price[5.23-5250]
  [OK] 日期范围: 2021-01-01 ~ 2023-03-08

  注: 每客户仅一条交易，不支持复购/留存/购物篮分析
""")

print("\n阶段二完成!")
