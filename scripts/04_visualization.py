"""
阶段四：Python 数据可视化
输出：13 张 PNG 图表到 ./charts/ 目录
"""
import pandas as pd
import numpy as np
import pymysql
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# 全局设置
# ============================================================
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"

OUT_DIR = r"D:\Modeling code\数据分析项目\淘宝用户行为数据分析\charts"

COLORS = {
    "primary": "#2196F3",
    "secondary": "#FF9800",
    "accent": "#4CAF50",
    "palette": ["#2196F3", "#FF9800", "#4CAF50", "#E91E63", "#9C27B0",
                "#00BCD4", "#FF5722", "#607D8B"],
    "gender": {"Female": "#E91E63", "Male": "#2196F3"},
    "payment": {"Alipay": "#1677FF", "Card": "#FF9800", "WeChat Pay": "#4CAF50"},
    "tier_colors": ["#F44336", "#FF9800", "#2196F3", "#4CAF50"],
}

# ============================================================
# 1. 从 MySQL 读取数据
# ============================================================
conn = pymysql.connect(
    host="localhost", port=3306, user="root", password="wq010205",
    database="taobao_analysis", charset="utf8mb4",
)
df = pd.read_sql("SELECT * FROM user_behavior;", conn)
conn.close()

df["invoice_date"] = pd.to_datetime(df["invoice_date"])
CATEGORIES = sorted(df["category"].unique())
AGE_ORDER = ["18-25", "26-35", "36-45", "46-55", "56+"]
TIER_ORDER = ["低", "中", "高", "顶级"]
PAYMENT_ORDER = ["Alipay", "Card", "WeChat Pay"]

# ============================================================
# 2. 辅助函数
# ============================================================
def save(fig, name):
    path = f"{OUT_DIR}\\{name}.png"
    fig.savefig(path, facecolor="white", edgecolor="none")
    print(f"  [OK] {name}.png")
    plt.close(fig)

def autopct_fn(pct):
    return f"{pct:.1f}%" if pct > 3 else ""

# ============================================================
# 主题 A：经营健康度（3 张图）
# ============================================================
print("\n主题 A：经营健康度")

# --- A1: KPI 汇总表 (直接打印) ---
print("  A1: KPI汇总 (文本输出)")
total_gmv = df["gmv"].sum()
total_orders = len(df)
avg_order = df["gmv"].mean()
print(f"    总GMV: {total_gmv:,.0f} | 总订单: {total_orders:,} | "
      f"客单价: {avg_order:,.2f} | 客户数: {df['customer_id'].nunique():,}")

# --- A2: 月度经营趋势 (三线图, 双Y轴) ---
monthly = df.groupby("yr_mth").agg(
    orders=("invoice_no", "count"),
    gmv=("gmv", "sum"),
    avg_order=("gmv", "mean"),
).sort_index()

fig, ax1 = plt.subplots(figsize=(16, 6))
x = range(len(monthly))
labels = monthly.index.tolist()

ax1.fill_between(x, monthly["gmv"] / 1e4, alpha=0.2, color=COLORS["primary"])
ax1.plot(x, monthly["gmv"] / 1e4, "o-", color=COLORS["primary"], linewidth=1.8, markersize=4, label="GMV (万元)")
ax1.set_ylabel("GMV (万元)", color=COLORS["primary"], fontsize=12)
ax1.tick_params(axis="y", labelcolor=COLORS["primary"])

ax2 = ax1.twinx()
ax2.plot(x, monthly["avg_order"], "s--", color=COLORS["secondary"], linewidth=1.5, markersize=4, alpha=0.8, label="客单价")
ax2.set_ylabel("客单价 (元)", color=COLORS["secondary"], fontsize=12)
ax2.tick_params(axis="y", labelcolor=COLORS["secondary"])

ax1.set_xticks(x[::3])
ax1.set_xticklabels(labels[::3], rotation=45, ha="right", fontsize=9)
ax1.set_title("月度 GMV 与客单价趋势", fontsize=14, fontweight="bold")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)
fig.tight_layout()
save(fig, "A2_monthly_trend")

# --- A3: 年度同比 ---
yearly = df[df["yr"].isin([2021, 2022])].groupby("yr").agg(
    orders=("invoice_no", "count"), gmv=("gmv", "sum"), avg_order=("gmv", "mean"),
)
yoy = yearly.copy()
yoy["orders_chg"] = yoy["orders"].pct_change() * 100
yoy["gmv_chg"] = yoy["gmv"].pct_change() * 100
yoy["avg_order_chg"] = yoy["avg_order"].pct_change() * 100

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
metrics = [
    ("orders", "订单量", "#2196F3"),
    ("gmv", "GMV", "#FF9800"),
    ("avg_order", "客单价", "#4CAF50"),
]
for ax, (col, title, color) in zip(axes, metrics):
    ax.bar([0, 1], yearly[col].values, color=[color, color], alpha=0.85, width=0.5)
    for i, (v, y) in enumerate(zip(yearly[col].values, [2021, 2022])):
        ax.text(i, v * 1.02, f"{v:,.0f}", ha="center", fontsize=10, fontweight="bold")
    chg = yoy[f"{col}_chg"].iloc[1]
    ax.set_title(f"{title}\n同比 {chg:+.1f}%", fontsize=12, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2021", "2022"])
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e4:.0f}万" if v > 10000 else f"{v:,.0f}"))
fig.suptitle("2021 vs 2022 年度经营指标同比", fontsize=14, fontweight="bold")
fig.tight_layout()
save(fig, "A3_yoy_comparison")

# ============================================================
# 主题 B：客群洞察（3 张图）
# ============================================================
print("\n主题 B：客群洞察")

# --- B1: 年龄直方图 + 性别饼图 ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# 年龄直方图
n, bins, patches = ax1.hist(df["age"], bins=range(18, 71, 3), color=COLORS["primary"],
                             edgecolor="white", alpha=0.85)
ax1.axvline(df["age"].mean(), color="#E91E63", linestyle="--", linewidth=2, label=f"均值: {df['age'].mean():.1f}岁")
ax1.axvline(df["age"].median(), color="#FF9800", linestyle="--", linewidth=2, label=f"中位数: {df['age'].median():.0f}岁")
ax1.set_xlabel("年龄", fontsize=11)
ax1.set_ylabel("人数", fontsize=11)
ax1.set_title("客户年龄分布", fontsize=13, fontweight="bold")
ax1.legend(fontsize=9)

# 性别饼图
gender_counts = df["gender"].value_counts()
wedges, texts, autotexts = ax2.pie(
    gender_counts.values, labels=gender_counts.index,
    colors=[COLORS["gender"]["Female"], COLORS["gender"]["Male"]],
    autopct="%1.1f%%", startangle=90, explode=(0.02, 0.02),
    textprops={"fontsize": 11},
)
for at in autotexts:
    at.set_fontweight("bold")
    at.set_fontsize(12)
ax2.set_title("客户性别构成", fontsize=13, fontweight="bold")

fig.suptitle("客户人口画像", fontsize=14, fontweight="bold")
fig.tight_layout()
save(fig, "B1_demographic")

# --- B2: 消费四层多维度对比 ---
tier_stats = df.groupby("cust_tier").agg(
    count=("invoice_no", "count"), avg_age=("age", "mean"),
    female_pct=("gender", lambda x: (x == "Female").sum() / len(x) * 100),
    avg_gmv=("gmv", "mean"), total_gmv=("gmv", "sum"),
).reindex(TIER_ORDER)

# 各层品类偏好 (top 3)
tier_cat = df.groupby(["cust_tier", "category"]).size().unstack(fill_value=0)
tier_cat_pct = tier_cat.div(tier_cat.sum(axis=1), axis=0) * 100

# 各层支付偏好
tier_pmt = df.groupby(["cust_tier", "payment_method"]).size().unstack(fill_value=0)
tier_pmt_pct = tier_pmt.div(tier_pmt.sum(axis=1), axis=0) * 100

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Subplot 1: 平均年龄 + 女性占比
ax = axes[0, 0]
x = np.arange(len(TIER_ORDER))
w = 0.35
bars1 = ax.bar(x - w/2, tier_stats["avg_age"], w, color=COLORS["primary"], alpha=0.85, label="平均年龄")
ax.set_ylabel("平均年龄", color=COLORS["primary"])
ax_twin = ax.twinx()
bars2 = ax_twin.bar(x + w/2, tier_stats["female_pct"], w, color="#E91E63", alpha=0.85, label="女性占比(%)")
ax_twin.set_ylabel("女性占比 (%)", color="#E91E63")
ax.set_xticks(x)
ax.set_xticklabels(TIER_ORDER)
ax.set_title("各层年龄与性别结构", fontsize=12, fontweight="bold")
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax_twin.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

# Subplot 2: GMV 贡献
ax = axes[0, 1]
ax.pie(tier_stats["total_gmv"].values, labels=TIER_ORDER,
       colors=COLORS["tier_colors"], autopct="%1.1f%%",
       startangle=90, explode=(0.02, 0.02, 0.02, 0.05),
       textprops={"fontsize": 10})
ax.set_title("各消费层级 GMV 贡献", fontsize=12, fontweight="bold")

# Subplot 3: 品类偏好 (堆叠柱状图)
ax = axes[1, 0]
tier_cat_pct_reindex = tier_cat_pct.reindex(TIER_ORDER)
bottom = np.zeros(len(TIER_ORDER))
for i, cat in enumerate(tier_cat_pct.columns):
    ax.bar(TIER_ORDER, tier_cat_pct_reindex[cat], bottom=bottom,
           color=COLORS["palette"][i % len(COLORS["palette"])], alpha=0.85, label=cat[:15])
    bottom += tier_cat_pct_reindex[cat].values
ax.set_ylabel("占比 (%)", fontsize=10)
ax.set_title("各层品类偏好构成", fontsize=12, fontweight="bold")
ax.legend(fontsize=7, loc="upper right", ncol=2)

# Subplot 4: 支付偏好
ax = axes[1, 1]
tier_pmt_pct_reindex = tier_pmt_pct.reindex(TIER_ORDER)
tier_pmt_pct_reindex[PAYMENT_ORDER].plot(
    kind="bar", ax=ax, color=[COLORS["payment"][p] for p in PAYMENT_ORDER], alpha=0.85)
ax.set_ylabel("占比 (%)", fontsize=10)
ax.set_title("各层支付方式偏好", fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.set_xticklabels(TIER_ORDER, rotation=0)

fig.suptitle("消费四层客群特征对比", fontsize=14, fontweight="bold")
fig.tight_layout()
save(fig, "B2_customer_tier")

# --- B3: 客群×品类 TGI 热力图 ---
tgi_base = df.groupby(["age_group", "gender", "category"]).size().reset_index(name="n")
total_pop = tgi_base["n"].sum()
tgi_base["pop_pct"] = tgi_base["n"] / total_pop
# 每个品类占总体的比例
cat_total = tgi_base.groupby("category")["n"].sum().reset_index()
cat_total.columns = ["category", "cat_n"]
tgi_base = tgi_base.merge(cat_total, on="category")
# 每个客群占总体的比例
seg_total = tgi_base.groupby(["age_group", "gender"])["n"].sum().reset_index()
seg_total.columns = ["age_group", "gender", "seg_n"]
tgi_base = tgi_base.merge(seg_total, on=["age_group", "gender"])
# TGI = (客群在品类中占比) / (客群在总体中占比) * 100
tgi_base["tgi"] = ((tgi_base["n"] / tgi_base["cat_n"]) / (tgi_base["seg_n"] / total_pop)) * 100
tgi_base["segment"] = tgi_base["age_group"] + "-" + tgi_base["gender"]

tgi_pivot = tgi_base.pivot_table(values="tgi", index="segment", columns="category", aggfunc="mean")
# 按年龄段排序
seg_order = [f"{a}-{g}" for a in AGE_ORDER for g in ["Female", "Male"]]
tgi_pivot = tgi_pivot.reindex(seg_order)

fig, ax = plt.subplots(figsize=(14, 7))
sns.heatmap(tgi_pivot, annot=True, fmt=".0f", cmap="RdYlBu_r", center=100,
            linewidths=0.5, ax=ax, cbar_kws={"label": "TGI", "shrink": 0.8},
            vmin=70, vmax=130, annot_kws={"fontsize": 8})
ax.set_title("客群 × 品类 TGI 偏好热力图\n(TGI>100 表示该客群对该品类有正向偏好)", fontsize=14, fontweight="bold")
ax.set_xlabel("品类", fontsize=11)
ax.set_ylabel("客群 (年龄段-性别)", fontsize=11)
fig.tight_layout()
save(fig, "B3_tgi_heatmap")

# ============================================================
# 主题 C：品类策略（4 张图）
# ============================================================
print("\n主题 C：品类策略")

# --- C1: 品类 GMV 帕累托图 ---
cat_stats = df.groupby("category").agg(
    gmv=("gmv", "sum"), orders=("invoice_no", "count"), avg_order=("gmv", "mean"),
).sort_values("gmv", ascending=False)
cat_stats["gmv_pct"] = cat_stats["gmv"] / cat_stats["gmv"].sum() * 100
cat_stats["cum_pct"] = cat_stats["gmv_pct"].cumsum()

fig, ax1 = plt.subplots(figsize=(12, 6))
bars = ax1.bar(cat_stats.index, cat_stats["gmv"] / 1e4, color=COLORS["palette"][:8], alpha=0.85, edgecolor="white")
ax1.set_ylabel("GMV (万元)", fontsize=11)
ax1.set_xlabel("")
# 数值标注
for bar, gmv, pct in zip(bars, cat_stats["gmv"], cat_stats["gmv_pct"]):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
             f"{pct:.1f}%", ha="center", fontsize=9, fontweight="bold")

ax2 = ax1.twinx()
ax2.plot(range(len(cat_stats)), cat_stats["cum_pct"], "o-", color="#E91E63",
         linewidth=2.5, markersize=8, markerfacecolor="white")
ax2.set_ylabel("累计 GMV 占比 (%)", color="#E91E63", fontsize=11)
ax2.tick_params(axis="y", labelcolor="#E91E63")
ax2.set_ylim(0, 105)
ax2.axhline(80, color="gray", linestyle="--", alpha=0.5, linewidth=1)
ax2.text(len(cat_stats) - 0.5, 81, "80%线", fontsize=8, color="gray")

ax1.set_xticklabels(cat_stats.index, rotation=30, ha="right", fontsize=10)
ax1.set_title("品类 GMV 帕累托分析", fontsize=14, fontweight="bold")
fig.tight_layout()
save(fig, "C1_pareto")

# --- C2: 品类定位气泡图 ---
fig, ax = plt.subplots(figsize=(11, 8))
x = cat_stats["gmv_pct"].values
y = cat_stats["avg_order"].values
sizes = cat_stats["orders"].values / 30

scatter = ax.scatter(x, y, s=sizes, c=COLORS["palette"][:8], alpha=0.7, edgecolors="black", linewidth=1)
ax.axhline(y=df["gmv"].mean(), color="gray", linestyle="--", alpha=0.4)
ax.axvline(x=100/8, color="gray", linestyle="--", alpha=0.4)
ax.set_xlabel("GMV 占比 (%)", fontsize=12)
ax.set_ylabel("客单价 (元)", fontsize=12)
ax.set_title("品类定位矩阵\n(气泡大小 = 订单量, 虚线 = 均值)", fontsize=14, fontweight="bold")
for i, cat in enumerate(cat_stats.index):
    ax.annotate(cat, (x[i], y[i]), textcoords="offset points",
                xytext=(0, 15 if i % 2 == 0 else -20), ha="center", fontsize=10, fontweight="bold")
# 象限标注
ax.text(x.max() * 0.85, y.max() * 0.95, "明星品类", fontsize=9, color="#4CAF50", fontweight="bold", alpha=0.6)
ax.text(x.min() * 2, y.max() * 0.95, "潜力品类", fontsize=9, color="#FF9800", fontweight="bold", alpha=0.6)
ax.text(x.max() * 0.85, y.min() * 1.5, "金牛品类", fontsize=9, color="#2196F3", fontweight="bold", alpha=0.6)
ax.text(x.min() * 2, y.min() * 1.5, "瘦狗品类", fontsize=9, color="#F44336", fontweight="bold", alpha=0.6)
fig.tight_layout()
save(fig, "C2_bubble_matrix")

# --- C3: 品类价格箱线图 ---
fig, ax = plt.subplots(figsize=(13, 6))
price_data = [df[df["category"] == cat]["price"].values for cat in CATEGORIES]
bp = ax.boxplot(price_data, labels=CATEGORIES, patch_artist=True, showmeans=True,
                meanprops=dict(marker="D", markerfacecolor="red", markersize=6),
                flierprops=dict(marker="o", alpha=0.4))
for patch, color in zip(bp["boxes"], COLORS["palette"][:len(CATEGORIES)]):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
ax.set_ylabel("单价 (元)", fontsize=11)
ax.set_title("各类目价格分布", fontsize=14, fontweight="bold")
ax.set_xticklabels(CATEGORIES, rotation=30, ha="right", fontsize=10)
fig.tight_layout()
save(fig, "C3_price_boxplot")

# --- C4: 量价关系散点图 ---
qv_stats = df.groupby("category").agg(
    avg_price=("price", "mean"), avg_quantity=("quantity", "mean"),
    total_gmv=("gmv", "sum"), orders=("invoice_no", "count"),
).reset_index()

fig, ax = plt.subplots(figsize=(11, 7))
scatter = ax.scatter(
    qv_stats["avg_price"], qv_stats["avg_quantity"],
    s=qv_stats["total_gmv"] / 500000,
    c=COLORS["palette"][:len(qv_stats)], alpha=0.7, edgecolors="black", linewidth=1,
)
z = np.polyfit(qv_stats["avg_price"], qv_stats["avg_quantity"], 1)
p = np.poly1d(z)
x_line = np.linspace(qv_stats["avg_price"].min(), qv_stats["avg_price"].max(), 100)
ax.plot(x_line, p(x_line), "--", color="gray", alpha=0.5, linewidth=1)
ax.set_xlabel("平均单价 (元)", fontsize=12)
ax.set_ylabel("平均购买数量", fontsize=12)
ax.set_title("品类的量价关系\n(气泡大小 = GMV, 虚线 = 趋势)", fontsize=14, fontweight="bold")
for _, row in qv_stats.iterrows():
    ax.annotate(row["category"], (row["avg_price"], row["avg_quantity"]),
                textcoords="offset points", xytext=(0, 12), ha="center", fontsize=10, fontweight="bold")
fig.tight_layout()
save(fig, "C4_quantity_price_scatter")

# ============================================================
# 主题 D：交易行为（3 张图）
# ============================================================
print("\n主题 D：交易行为")

# --- D1: 支付方式月度趋势 (堆叠面积图) + 客单价对比 ---
pmt_monthly = df.groupby(["yr_mth", "payment_method"]).size().unstack(fill_value=0)
pmt_monthly = pmt_monthly[PAYMENT_ORDER]
pmt_pct = pmt_monthly.div(pmt_monthly.sum(axis=1), axis=0) * 100

pmt_avg = df.groupby("payment_method")["gmv"].mean().reindex(PAYMENT_ORDER)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# 堆叠面积图
x = range(len(pmt_pct))
labels = pmt_pct.index.tolist()
ax1.stackplot(x, pmt_pct["Alipay"], pmt_pct["Card"], pmt_pct["WeChat Pay"],
              labels=PAYMENT_ORDER,
              colors=[COLORS["payment"][p] for p in PAYMENT_ORDER], alpha=0.8)
ax1.set_xticks(x[::3])
ax1.set_xticklabels(labels[::3], rotation=45, ha="right", fontsize=9)
ax1.set_ylabel("占比 (%)", fontsize=11)
ax1.set_title("支付方式月度占比趋势", fontsize=13, fontweight="bold")
ax1.legend(fontsize=10, loc="upper right")
ax1.set_ylim(0, 100)

# 客单价对比
bars = ax2.bar(PAYMENT_ORDER, pmt_avg.values,
               color=[COLORS["payment"][p] for p in PAYMENT_ORDER], alpha=0.85, width=0.5)
for bar, val in zip(bars, pmt_avg.values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
             f"{val:,.2f}", ha="center", fontsize=11, fontweight="bold")
ax2.set_ylabel("客单价 (元)", fontsize=11)
ax2.set_title("各支付方式平均客单价", fontsize=13, fontweight="bold")
ax2.set_ylim(0, pmt_avg.max() * 1.08)

fig.suptitle("支付方式分析", fontsize=14, fontweight="bold")
fig.tight_layout()
save(fig, "D1_payment_trend")

# --- D2: 品类×支付热力图 + 年龄×支付分组柱状图 ---
cat_pmt = df.groupby(["category", "payment_method"]).size().unstack(fill_value=0)
cat_pmt_pct = cat_pmt.div(cat_pmt.sum(axis=1), axis=0) * 100
cat_pmt_pct = cat_pmt_pct[PAYMENT_ORDER]

age_pmt = df.groupby(["age_group", "payment_method"]).size().unstack(fill_value=0)
age_pmt_pct = age_pmt.div(age_pmt.sum(axis=1), axis=0) * 100
age_pmt_pct = age_pmt_pct.reindex(AGE_ORDER)[PAYMENT_ORDER]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# 热力图
sns.heatmap(cat_pmt_pct, annot=True, fmt=".1f", cmap="YlOrRd",
            linewidths=0.5, ax=ax1, cbar_kws={"label": "%", "shrink": 0.8},
            annot_kws={"fontsize": 9})
ax1.set_title("品类 × 支付方式 (%)\n", fontsize=13, fontweight="bold")
ax1.set_xlabel("支付方式", fontsize=10)
ax1.set_ylabel("品类", fontsize=10)

# 分组柱状图
age_pmt_pct.plot(kind="bar", ax=ax2, color=[COLORS["payment"][p] for p in PAYMENT_ORDER],
                 alpha=0.85, edgecolor="white")
ax2.set_ylabel("占比 (%)", fontsize=11)
ax2.set_title("年龄 × 支付方式", fontsize=13, fontweight="bold")
ax2.legend(fontsize=9)
ax2.set_xticklabels(AGE_ORDER, rotation=0)

fig.suptitle("支付方式交叉分析", fontsize=14, fontweight="bold")
fig.tight_layout()
save(fig, "D2_payment_cross")

# --- D3: 品类×quantity 堆叠柱状图 ---
cat_qty = df.groupby(["category", "quantity"]).size().unstack(fill_value=0)
cat_qty_pct = cat_qty.div(cat_qty.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(12, 6))
qty_colors = ["#E3F2FD", "#90CAF9", "#42A5F5", "#1E88E5", "#0D47A1"]
bottom = np.zeros(len(cat_qty_pct))
for i, qty in enumerate([1, 2, 3, 4, 5]):
    ax.bar(cat_qty_pct.index, cat_qty_pct[qty], bottom=bottom,
           color=qty_colors[i], alpha=0.85, label=f"数量={qty}", edgecolor="white")
    bottom += cat_qty_pct[qty].values
ax.set_ylabel("占比 (%)", fontsize=11)
ax.set_title("各类目购买数量分布", fontsize=14, fontweight="bold")
ax.legend(fontsize=9, loc="upper right")
ax.set_xticklabels(cat_qty_pct.index, rotation=30, ha="right", fontsize=10)
fig.tight_layout()
save(fig, "D3_quantity_stack")

print(f"\n阶段四完成! 共 13 张图表, 保存在 {OUT_DIR}")
