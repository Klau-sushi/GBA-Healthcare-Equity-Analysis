# --- 终极武器：用Python绘制学术级洛伦兹曲线 ---

# 1. 导入我们的“武器库”
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# 设置中文字体，确保图表中的中文能正确显示
mpl.rcParams['font.sans-serif'] = ['SimHei']  # SimHei是常用的黑体
mpl.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 2. 读取数据文件
try:
    df = pd.read_csv('hongkong_gini.csv',encoding='gbk')
except FileNotFoundError:
    print("错误：未在当前文件夹下找到 hongkong_gini.csv 文件！请检查文件名和位置。")
    exit()

# 3. ★ 核心计算：这是洛伦兹曲线的数学灵魂 ★
#    确保数据是数值类型
df['population'] = pd.to_numeric(df['population'])
df['num_doctors'] = pd.to_numeric(df['num_doctors'])

#    计算人均医生数，并根据这个指标对各区进行“从穷到富”的排序
df['doctors_per_capita'] = df['num_doctors'] / df['population']
df_sorted = df.sort_values(by='doctors_per_capita')

#    计算人口和医生数量的累计百分比
df_sorted['cum_population_pct'] = df_sorted['population'].cumsum() / df_sorted['population'].sum()
df_sorted['cum_doctors_pct'] = df_sorted['num_doctors'].cumsum() / df_sorted['num_doctors'].sum()

#    在数据开头加上(0,0)这个点，让曲线从原点开始
lorenz_data = pd.concat([pd.DataFrame({'cum_population_pct': [0], 'cum_doctors_pct': [0]}), df_sorted[['cum_population_pct', 'cum_doctors_pct']]])

#    计算基尼系数 (面积法)
area_between_curves = np.trapz(lorenz_data['cum_doctors_pct'], lorenz_data['cum_population_pct'])
gini_coefficient = (0.5 - area_between_curves) / 0.5

# 4. ★ 绘制无可辩驳的“洛伦兹曲线” ★
fig, ax = plt.subplots(figsize=(8, 8)) # 创建一个8x8英寸的画布

#   绘制“绝对公平线”
ax.plot([0, 1], [0, 1], 'k--', label='绝对公平线 (Line of Perfect Equality)')

#   绘制洛伦兹曲线
ax.plot(lorenz_data['cum_population_pct'], lorenz_data['cum_doctors_pct'], 'r-', linewidth=2, label='洛伦兹曲线 (Lorenz Curve)')

#   设置图表样式，使其符合学术规范
ax.set_title('香港医疗资源（医生）分布的洛伦兹曲线', fontsize=16, fontweight='bold')
ax.set_xlabel('人口累计百分比', fontsize=12)
ax.set_ylabel('医生资源累计百分比', fontsize=12)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect('equal', adjustable='box')
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(loc='upper left', fontsize=10)

#   在图中标注出计算出的基尼系数值
ax.text(0.6, 0.2, f'基尼系数 (Gini Coefficient) = {gini_coefficient:.4f}', fontsize=12, bbox=dict(facecolor='white', alpha=0.5))

# 5. ★ 自动保存高清图片到文件夹 ★
plt.savefig('lorenz_curve.png', dpi=300, bbox_inches='tight')

print("任务完成！")
print(f"计算出的基尼系数为: {gini_coefficient:.4f}")
print("名为 lorenz_curve.png 的高清图片已保存到当前文件夹中！")