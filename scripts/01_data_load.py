"""
阶段一：数据导入 MySQL
功能：读取 CSV → 清洗 → 衍生字段计算 → 写入 MySQL 表 user_behavior
列名说明：
  invoice_no / customer_id / gender / age / category / quantity / price / payment_method / invoice_date（原始字段）
  gmv / age_group / yr / mth / yr_mth / cust_tier（衍生字段）
"""
import pandas as pd
import pymysql
from sqlalchemy import create_engine

# ============================================================
# 1. 配置
# ============================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "wq010205",
    "charset": "utf8mb4",
}
DB_NAME = "taobao_analysis"
CSV_PATH = r"D:\Modeling code\数据分析项目\淘宝用户行为数据分析\淘宝用户行为.csv"

# ============================================================
# 2. 创建数据库
# ============================================================
conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4;")
print(f"数据库 '{DB_NAME}' 已就绪")
cursor.close()
conn.close()

# ============================================================
# 3. 读取 CSV
# ============================================================
df = pd.read_csv(CSV_PATH)
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
print(f"读取数据: {len(df):,} 行, {len(df.columns)} 列")

# ============================================================
# 4. 数据类型转换
# ============================================================
df["invoice_date"] = pd.to_datetime(df["invoice_date"])
df["age"] = df["age"].astype(int)
df["quantity"] = df["quantity"].astype(int)
df["price"] = df["price"].astype(float)

# ============================================================
# 5. 衍生字段计算
# ============================================================
df["gmv"] = (df["quantity"] * df["price"]).round(2)
df["age_group"] = pd.cut(
    df["age"],
    bins=[0, 25, 35, 45, 55, 100],
    labels=["18-25", "26-35", "36-45", "46-55", "56+"],
)
df["yr"] = df["invoice_date"].dt.year
df["mth"] = df["invoice_date"].dt.month
df["yr_mth"] = df["invoice_date"].dt.strftime("%Y-%m")
df["cust_tier"] = pd.qcut(
    df["gmv"],
    q=4,
    labels=["低", "中", "高", "顶级"],
)
print("衍生字段已生成: gmv, age_group, yr, mth, yr_mth, cust_tier")

# ============================================================
# 6. 建表（VARCHAR 列类型，避免 MySQL 保留字）
# ============================================================
conn = pymysql.connect(**DB_CONFIG, database=DB_NAME)
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS user_behavior;")
cursor.execute("""
    CREATE TABLE user_behavior (
        invoice_no     VARCHAR(20)   NOT NULL PRIMARY KEY,
        customer_id    VARCHAR(20)   NOT NULL,
        gender         VARCHAR(10)   NOT NULL,
        age            INT           NOT NULL,
        category       VARCHAR(30)   NOT NULL,
        quantity       INT           NOT NULL,
        price          DOUBLE        NOT NULL,
        payment_method VARCHAR(20)   NOT NULL,
        invoice_date   DATETIME      NOT NULL,
        gmv            DOUBLE        DEFAULT NULL,
        age_group      VARCHAR(10)   DEFAULT NULL,
        yr             INT           DEFAULT NULL,
        mth            INT           DEFAULT NULL,
        yr_mth         VARCHAR(7)    DEFAULT NULL,
        cust_tier      VARCHAR(10)   DEFAULT NULL
    ) DEFAULT CHARSET=utf8mb4;
""")
conn.commit()
cursor.close()
conn.close()
print("表结构已创建")

# ============================================================
# 7. 写入数据
# ============================================================
engine = create_engine(
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_NAME}"
)
df.to_sql(
    name="user_behavior",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=5000,
)
print("数据已写入")

# ============================================================
# 8. 创建索引
# ============================================================
conn = pymysql.connect(**DB_CONFIG, database=DB_NAME)
cursor = conn.cursor()
indexes = [
    "CREATE INDEX idx_inv_date ON user_behavior(invoice_date);",
    "CREATE INDEX idx_cat ON user_behavior(category);",
    "CREATE INDEX idx_cust ON user_behavior(customer_id);",
    "CREATE INDEX idx_yr_mth ON user_behavior(yr_mth);",
    "CREATE INDEX idx_age_grp ON user_behavior(age_group);",
    "CREATE INDEX idx_cust_tier ON user_behavior(cust_tier);",
]
for sql in indexes:
    cursor.execute(sql)
conn.commit()
cursor.close()
conn.close()
print("索引创建完成")

# ============================================================
# 9. 验证
# ============================================================
conn = pymysql.connect(**DB_CONFIG, database=DB_NAME)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM user_behavior;")
row_count = cursor.fetchone()[0]
cursor.execute("SHOW COLUMNS FROM user_behavior;")
columns = [col[0] for col in cursor.fetchall()]
cursor.close()
conn.close()

print(f"\n验证通过: {row_count:,} 行, {len(columns)} 列")
print(f"列: {columns}")
print("\n阶段一完成！")
