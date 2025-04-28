import json
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 或者使用 'SimHei'
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
output_dir = "lottery_analysis"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 加载双色球历史数据
try:
    with open('dual_history.json', 'r', encoding='utf-8') as f:
        lottery_data = json.load(f)
    
    # 提取数据
    draws = lottery_data.get('data', [])
    total_periods = len(draws)
    fetch_time = lottery_data.get('fetch_time', '未知')
    
    if total_periods == 0:
        print("未找到有效的双色球历史数据，请先运行 fetch_history_dual.py 获取数据")
        exit()
except FileNotFoundError:
    print("未找到 dual_history.json 文件，请先运行 fetch_history_dual.py 获取数据")
    exit()
except json.JSONDecodeError:
    print("dual_history.json 文件格式错误，请重新获取数据")
    exit()

# 设置要分析的期数
periods_to_analyze = [100, 200, 300, 500, 1000, total_periods]
# 过滤掉超过总期数的值
periods_to_analyze = [p for p in periods_to_analyze if p <= total_periods]

# 设置显示格式
pd.set_option('display.float_format', '{:.2f}'.format)

# 创建分析报告文件
report_file = os.path.join(output_dir, "双色球分析报告.txt")
with open(report_file, 'w', encoding='utf-8') as report:
    # 写入报告头部
    report.write(f"双色球历史数据分析报告\n")
    report.write(f"{'='*50}\n")
    report.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.write(f"数据获取时间: {fetch_time}\n")
    report.write(f"总期数: {total_periods}\n")
    report.write(f"{'='*50}\n\n")
    
    # 对每个期数进行分析
    for periods in periods_to_analyze:
        report.write(f"\n{'-'*50}\n")
        report.write(f"分析过去 {periods} 期双色球开奖结果\n")
        report.write(f"{'-'*50}\n")
        
        # 统计红球和蓝球出现次数
        red_balls = []
        blue_balls = []
        
        for draw in draws[:periods]:
            red_balls.extend(draw.get('red_numbers', []))
            blue_balls.append(draw.get('blue_number'))
        
        # 计数
        red_counter = Counter(red_balls)
        blue_counter = Counter(blue_balls)
        
        # 确保所有可能的号码都在计数器中
        for i in range(1, 34):
            if i not in red_counter:
                red_counter[i] = 0
        
        for i in range(1, 17):
            if i not in blue_counter:
                blue_counter[i] = 0
        
        # 排序
        red_sorted = red_counter.most_common()
        blue_sorted = blue_counter.most_common()
        
        # 计算理论概率
        theoretical_red_prob = 6 / 33  # 每期6个红球，总共33个红球号码
        theoretical_blue_prob = 1 / 16  # 每期1个蓝球，总共16个蓝球号码
        
        # 创建DataFrame并添加统计列
        red_df = pd.DataFrame(red_sorted, columns=['红球号码', '出现次数'])
        red_df['出现率'] = red_df['出现次数'] / periods * 100
        red_df['理论次数'] = periods * theoretical_red_prob
        red_df['偏差率'] = (red_df['出现次数'] - red_df['理论次数']) / red_df['理论次数'] * 100
        
        blue_df = pd.DataFrame(blue_sorted, columns=['蓝球号码', '出现次数'])
        blue_df['出现率'] = blue_df['出现次数'] / periods * 100
        blue_df['理论次数'] = periods * theoretical_blue_prob
        blue_df['偏差率'] = (blue_df['出现次数'] - blue_df['理论次数']) / blue_df['理论次数'] * 100
        
        # 定义热门和冷门号码（偏差率超过±20%）
        hot_red = red_df[red_df['偏差率'] > 20]
        cold_red = red_df[red_df['偏差率'] < -20]
        
        hot_blue = blue_df[blue_df['偏差率'] > 20]
        cold_blue = blue_df[blue_df['偏差率'] < -20]
        
        # 写入红球统计
        report.write("\n红球出现频率 (前10名):\n")
        report.write(red_df.head(10).to_string(index=False) + "\n")
        
        report.write("\n红球统计信息:\n")
        report.write(f"平均出现次数: {red_df['出现次数'].mean():.2f}\n")
        report.write(f"最大偏差率: {red_df['偏差率'].abs().max():.2f}%\n")
        report.write(f"标准差: {red_df['出现次数'].std():.2f}\n")
        
        # 写入热门和冷门红球
        report.write("\n热门红球 (偏差率 > 20%):\n")
        if not hot_red.empty:
            report.write(hot_red.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率超过20%的热门红球\n")
        
        report.write("\n冷门红球 (偏差率 < -20%):\n")
        if not cold_red.empty:
            report.write(cold_red.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率低于-20%的冷门红球\n")
        
        # 写入蓝球统计
        report.write("\n蓝球出现频率 (全部):\n")
        report.write(blue_df.to_string(index=False) + "\n")
        
        report.write("\n蓝球统计信息:\n")
        report.write(f"平均出现次数: {blue_df['出现次数'].mean():.2f}\n")
        report.write(f"最大偏差率: {blue_df['偏差率'].abs().max():.2f}%\n")
        report.write(f"标准差: {blue_df['出现次数'].std():.2f}\n")
        
        # 写入热门和冷门蓝球
        report.write("\n热门蓝球 (偏差率 > 20%):\n")
        if not hot_blue.empty:
            report.write(hot_blue.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率超过20%的热门蓝球\n")
        
        report.write("\n冷门蓝球 (偏差率 < -20%):\n")
        if not cold_blue.empty:
            report.write(cold_blue.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率低于-20%的冷门蓝球\n")
        
        # 生成图表
        # 红球频率图
        plt.figure(figsize=(15, 8))
        plt.bar(red_df['红球号码'], red_df['出现次数'], color='red', alpha=0.7)
        plt.axhline(y=red_df['理论次数'].iloc[0], color='black', linestyle='--', label=f'理论平均值: {red_df["理论次数"].iloc[0]:.2f}')
        plt.title(f'过去{periods}期双色球红球出现频率')
        plt.xlabel('红球号码')
        plt.ylabel('出现次数')
        plt.xticks(range(1, 34))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'红球频率_{periods}期.png'))
        plt.close()
        
        # 蓝球频率图
        plt.figure(figsize=(12, 6))
        plt.bar(blue_df['蓝球号码'], blue_df['出现次数'], color='blue', alpha=0.7)
        plt.axhline(y=blue_df['理论次数'].iloc[0], color='black', linestyle='--', label=f'理论平均值: {blue_df["理论次数"].iloc[0]:.2f}')
        plt.title(f'过去{periods}期双色球蓝球出现频率')
        plt.xlabel('蓝球号码')
        plt.ylabel('出现次数')
        plt.xticks(range(1, 17))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'蓝球频率_{periods}期.png'))
        plt.close()
        
        # 红球偏差率图
        plt.figure(figsize=(15, 8))
        colors = ['green' if x >= 0 else 'red' for x in red_df['偏差率']]
        plt.bar(red_df['红球号码'], red_df['偏差率'], color=colors, alpha=0.7)
        plt.axhline(y=0, color='black', linestyle='-')
        plt.title(f'过去{periods}期双色球红球偏差率')
        plt.xlabel('红球号码')
        plt.ylabel('偏差率 (%)')
        plt.xticks(range(1, 34))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'红球偏差率_{periods}期.png'))
        plt.close()
        
        # 蓝球偏差率图
        plt.figure(figsize=(12, 6))
        colors = ['green' if x >= 0 else 'red' for x in blue_df['偏差率']]
        plt.bar(blue_df['蓝球号码'], blue_df['偏差率'], color=colors, alpha=0.7)
        plt.axhline(y=0, color='black', linestyle='-')
        plt.title(f'过去{periods}期双色球蓝球偏差率')
        plt.xlabel('蓝球号码')
        plt.ylabel('偏差率 (%)')
        plt.xticks(range(1, 17))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'蓝球偏差率_{periods}期.png'))
        plt.close()

# 添加趋势分析
with open(report_file, 'a', encoding='utf-8') as report:
    report.write(f"\n\n{'='*50}\n")
    report.write("双色球号码趋势分析\n")
    report.write(f"{'='*50}\n\n")
    
    # 分析不同期数下热门号码的变化
    report.write("红球热门号码变化趋势:\n")
    report.write("-" * 40 + "\n")
    report.write("| 期数 | 最热门红球 | 偏差率 |\n")
    report.write("|" + "-" * 10 + "|" + "-" * 14 + "|" + "-" * 10 + "|\n")
    
    for periods in periods_to_analyze:
        red_balls = []
        for draw in draws[:periods]:
            red_balls.extend(draw.get('red_numbers', []))
        
        red_counter = Counter(red_balls)
        theoretical = periods * 6 / 33
        
        # 找出最热门的红球
        most_common = red_counter.most_common(1)[0]
        ball_num = most_common[0]
        count = most_common[1]
        deviation = (count - theoretical) / theoretical * 100
        
        report.write(f"| {periods:8d} | {ball_num:12d} | {deviation:8.2f}% |\n")
    
    report.write("\n蓝球热门号码变化趋势:\n")
    report.write("-" * 40 + "\n")
    report.write("| 期数 | 最热门蓝球 | 偏差率 |\n")
    report.write("|" + "-" * 10 + "|" + "-" * 14 + "|" + "-" * 10 + "|\n")
    
    for periods in periods_to_analyze:
        blue_balls = []
        for draw in draws[:periods]:
            blue_balls.append(draw.get('blue_number'))
        
        blue_counter = Counter(blue_balls)
        theoretical = periods * 1 / 16
        
        # 找出最热门的蓝球
        most_common = blue_counter.most_common(1)[0]
        ball_num = most_common[0]
        count = most_common[1]
        deviation = (count - theoretical) / theoretical * 100
        
        report.write(f"| {periods:8d} | {ball_num:12d} | {deviation:8.2f}% |\n")

    # 分析最近100期的走势
    recent_100 = draws[:100]
    report.write("\n\n最近100期走势分析:\n")
    report.write("-" * 40 + "\n")
    
    # 计算连号出现频率
    consecutive_count = 0
    for draw in recent_100:
        red_numbers = sorted(draw.get('red_numbers', []))
        for i in range(len(red_numbers) - 1):
            if red_numbers[i + 1] - red_numbers[i] == 1:
                consecutive_count += 1
                break
    
    consecutive_rate = consecutive_count / 100 * 100
    report.write(f"连号出现率: {consecutive_rate:.2f}%\n")
    
    # 计算奇偶比例
    odd_count = 0
    even_count = 0
    for draw in recent_100:
        red_numbers = draw.get('red_numbers', [])
        for num in red_numbers:
            if num % 2 == 0:
                even_count += 1
            else:
                odd_count += 1
    
    total_numbers = odd_count + even_count
    odd_rate = odd_count / total_numbers * 100
    even_rate = even_count / total_numbers * 100
    report.write(f"奇数比例: {odd_rate:.2f}%\n")
    report.write(f"偶数比例: {even_rate:.2f}%\n")
    
    # 计算大小比例（以17为界限）
    small_count = 0
    large_count = 0
    for draw in recent_100:
        red_numbers = draw.get('red_numbers', [])
        for num in red_numbers:
            if num <= 17:
                small_count += 1
            else:
                large_count += 1
    
    small_rate = small_count / total_numbers * 100
    large_rate = large_count / total_numbers * 100
    report.write(f"小号(1-17)比例: {small_rate:.2f}%\n")
    report.write(f"大号(18-33)比例: {large_rate:.2f}%\n")
    
    # 计算和值分布
    sum_values = []
    for draw in recent_100:
        red_numbers = draw.get('red_numbers', [])
        sum_values.append(sum(red_numbers))
    
    avg_sum = sum(sum_values) / len(sum_values)
    min_sum = min(sum_values)
    max_sum = max(sum_values)
    report.write(f"红球和值平均: {avg_sum:.2f}\n")
    report.write(f"红球和值范围: {min_sum} - {max_sum}\n")
    
    # 生成和值分布图
    plt.figure(figsize=(12, 6))
    plt.hist(sum_values, bins=20, color='purple', alpha=0.7)
    plt.axvline(x=avg_sum, color='red', linestyle='--', label=f'平均值: {avg_sum:.2f}')
    plt.title('最近100期双色球红球和值分布')
    plt.xlabel('和值')
    plt.ylabel('频率')
    plt.grid(linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '红球和值分布_100期.png'))
    plt.close()

print(f"分析完成！报告已保存到 {report_file}")
print(f"图表已保存到 {output_dir} 目录")
