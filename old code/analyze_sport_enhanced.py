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
output_dir = "sport_lottery_analysis"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 加载大乐透历史数据
try:
    # 先尝试加载完整的历史数据文件
    try:
        with open('sport_history_full.json', 'r', encoding='utf-8') as f:
            lottery_data = json.load(f)
            print("使用完整的大乐透历史数据文件")
    except FileNotFoundError:
        # 如果完整文件不存在，尝试加载原始文件
        with open('sport_history.json', 'r', encoding='utf-8') as f:
            lottery_data = json.load(f)
            print("使用原始的大乐透历史数据文件")

    # 提取数据
    draws = lottery_data.get('data', [])
    total_periods = len(draws)
    fetch_time = lottery_data.get('fetch_time', '未知')

    if total_periods == 0:
        print("未找到有效的大乐透历史数据，请先运行 fetch_history_sport_enhanced.py 获取数据")
        exit()

    print(f"成功加载 {total_periods} 期大乐透历史数据")

except FileNotFoundError:
    print("未找到大乐透历史数据文件，请先运行 fetch_history_sport_enhanced.py 获取数据")
    exit()
except json.JSONDecodeError:
    print("大乐透历史数据文件格式错误，请重新获取数据")
    exit()

# 设置要分析的期数
periods_to_analyze = [100, 200, 300, 500, 1000, total_periods]
# 过滤掉超过总期数的值
periods_to_analyze = [p for p in periods_to_analyze if p <= total_periods]

# 设置显示格式
pd.set_option('display.float_format', '{:.2f}'.format)

# 创建分析报告文件
report_file = os.path.join(output_dir, "大乐透分析报告.txt")
with open(report_file, 'w', encoding='utf-8') as report:
    # 写入报告头部
    report.write(f"大乐透历史数据分析报告\n")
    report.write(f"{'='*50}\n")
    report.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.write(f"数据获取时间: {fetch_time}\n")
    report.write(f"总期数: {total_periods}\n")
    report.write(f"{'='*50}\n\n")

    # 对每个期数进行分析
    for periods in periods_to_analyze:
        report.write(f"\n{'-'*50}\n")
        report.write(f"分析过去 {periods} 期大乐透开奖结果\n")
        report.write(f"{'-'*50}\n")

        # 统计前区和后区出现次数
        front_balls = []
        back_balls = []

        for draw in draws[:periods]:
            front_balls.extend(draw.get('front_numbers', []))
            back_balls.extend(draw.get('back_numbers', []))

        # 计数
        front_counter = Counter(front_balls)
        back_counter = Counter(back_balls)

        # 确保所有可能的号码都在计数器中
        for i in range(1, 36):  # 大乐透前区1-35
            if i not in front_counter:
                front_counter[i] = 0

        for i in range(1, 13):  # 大乐透后区1-12
            if i not in back_counter:
                back_counter[i] = 0

        # 排序
        front_sorted = front_counter.most_common()
        back_sorted = back_counter.most_common()

        # 计算理论概率
        theoretical_front_prob = 5 / 35  # 每期5个前区号码，总共35个前区号码
        theoretical_back_prob = 2 / 12  # 每期2个后区号码，总共12个后区号码

        # 创建DataFrame并添加统计列
        front_df = pd.DataFrame(front_sorted, columns=['前区号码', '出现次数'])
        front_df['出现率'] = front_df['出现次数'] / periods * 100
        front_df['理论次数'] = periods * theoretical_front_prob
        front_df['偏差率'] = (front_df['出现次数'] - front_df['理论次数']) / front_df['理论次数'] * 100

        back_df = pd.DataFrame(back_sorted, columns=['后区号码', '出现次数'])
        back_df['出现率'] = back_df['出现次数'] / periods * 100
        back_df['理论次数'] = periods * theoretical_back_prob
        back_df['偏差率'] = (back_df['出现次数'] - back_df['理论次数']) / back_df['理论次数'] * 100

        # 定义热门和冷门号码（偏差率超过±20%）
        hot_front = front_df[front_df['偏差率'] > 20]
        cold_front = front_df[front_df['偏差率'] < -20]

        hot_back = back_df[back_df['偏差率'] > 20]
        cold_back = back_df[back_df['偏差率'] < -20]

        # 写入前区统计
        report.write("\n前区出现频率 (前10名):\n")
        report.write(front_df.head(10).to_string(index=False) + "\n")

        report.write("\n前区统计信息:\n")
        report.write(f"平均出现次数: {front_df['出现次数'].mean():.2f}\n")
        report.write(f"最大偏差率: {front_df['偏差率'].abs().max():.2f}%\n")
        report.write(f"标准差: {front_df['出现次数'].std():.2f}\n")

        # 写入热门和冷门前区号码
        report.write("\n热门前区号码 (偏差率 > 20%):\n")
        if not hot_front.empty:
            report.write(hot_front.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率超过20%的热门前区号码\n")

        report.write("\n冷门前区号码 (偏差率 < -20%):\n")
        if not cold_front.empty:
            report.write(cold_front.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率低于-20%的冷门前区号码\n")

        # 写入后区统计
        report.write("\n后区出现频率 (全部):\n")
        report.write(back_df.to_string(index=False) + "\n")

        report.write("\n后区统计信息:\n")
        report.write(f"平均出现次数: {back_df['出现次数'].mean():.2f}\n")
        report.write(f"最大偏差率: {back_df['偏差率'].abs().max():.2f}%\n")
        report.write(f"标准差: {back_df['出现次数'].std():.2f}\n")

        # 写入热门和冷门后区号码
        report.write("\n热门后区号码 (偏差率 > 20%):\n")
        if not hot_back.empty:
            report.write(hot_back.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率超过20%的热门后区号码\n")

        report.write("\n冷门后区号码 (偏差率 < -20%):\n")
        if not cold_back.empty:
            report.write(cold_back.to_string(index=False) + "\n")
        else:
            report.write("没有偏差率低于-20%的冷门后区号码\n")

        # 生成图表
        # 前区频率图
        plt.figure(figsize=(15, 8))
        plt.bar(front_df['前区号码'], front_df['出现次数'], color='red', alpha=0.7)
        plt.axhline(y=front_df['理论次数'].iloc[0], color='black', linestyle='--', label=f'理论平均值: {front_df["理论次数"].iloc[0]:.2f}')
        plt.title(f'过去{periods}期大乐透前区出现频率')
        plt.xlabel('前区号码')
        plt.ylabel('出现次数')
        plt.xticks(range(1, 36))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'前区频率_{periods}期.png'))
        plt.close()

        # 后区频率图
        plt.figure(figsize=(12, 6))
        plt.bar(back_df['后区号码'], back_df['出现次数'], color='blue', alpha=0.7)
        plt.axhline(y=back_df['理论次数'].iloc[0], color='black', linestyle='--', label=f'理论平均值: {back_df["理论次数"].iloc[0]:.2f}')
        plt.title(f'过去{periods}期大乐透后区出现频率')
        plt.xlabel('后区号码')
        plt.ylabel('出现次数')
        plt.xticks(range(1, 13))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'后区频率_{periods}期.png'))
        plt.close()

        # 前区偏差率图
        plt.figure(figsize=(15, 8))
        colors = ['green' if x >= 0 else 'red' for x in front_df['偏差率']]
        plt.bar(front_df['前区号码'], front_df['偏差率'], color=colors, alpha=0.7)
        plt.axhline(y=0, color='black', linestyle='-')
        plt.title(f'过去{periods}期大乐透前区偏差率')
        plt.xlabel('前区号码')
        plt.ylabel('偏差率 (%)')
        plt.xticks(range(1, 36))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'前区偏差率_{periods}期.png'))
        plt.close()

        # 后区偏差率图
        plt.figure(figsize=(12, 6))
        colors = ['green' if x >= 0 else 'red' for x in back_df['偏差率']]
        plt.bar(back_df['后区号码'], back_df['偏差率'], color=colors, alpha=0.7)
        plt.axhline(y=0, color='black', linestyle='-')
        plt.title(f'过去{periods}期大乐透后区偏差率')
        plt.xlabel('后区号码')
        plt.ylabel('偏差率 (%)')
        plt.xticks(range(1, 13))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'后区偏差率_{periods}期.png'))
        plt.close()

# 添加趋势分析
with open(report_file, 'a', encoding='utf-8') as report:
    report.write(f"\n\n{'='*50}\n")
    report.write("大乐透号码趋势分析\n")
    report.write(f"{'='*50}\n\n")

    # 分析不同期数下热门号码的变化
    report.write("前区热门号码变化趋势:\n")
    report.write("-" * 40 + "\n")
    report.write("| 期数 | 最热门前区号码 | 偏差率 |\n")
    report.write("|" + "-" * 10 + "|" + "-" * 14 + "|" + "-" * 10 + "|\n")

    for periods in periods_to_analyze:
        front_balls = []
        for draw in draws[:periods]:
            front_balls.extend(draw.get('front_numbers', []))

        front_counter = Counter(front_balls)
        theoretical = periods * 5 / 35

        # 找出最热门的前区号码
        most_common = front_counter.most_common(1)[0]
        ball_num = most_common[0]
        count = most_common[1]
        deviation = (count - theoretical) / theoretical * 100

        report.write(f"| {periods:8d} | {ball_num:12d} | {deviation:8.2f}% |\n")

    report.write("\n后区热门号码变化趋势:\n")
    report.write("-" * 40 + "\n")
    report.write("| 期数 | 最热门后区号码 | 偏差率 |\n")
    report.write("|" + "-" * 10 + "|" + "-" * 14 + "|" + "-" * 10 + "|\n")

    for periods in periods_to_analyze:
        back_balls = []
        for draw in draws[:periods]:
            back_balls.extend(draw.get('back_numbers', []))

        back_counter = Counter(back_balls)
        theoretical = periods * 2 / 12

        # 找出最热门的后区号码
        most_common = back_counter.most_common(1)[0]
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
        front_numbers = sorted(draw.get('front_numbers', []))
        for i in range(len(front_numbers) - 1):
            if front_numbers[i + 1] - front_numbers[i] == 1:
                consecutive_count += 1
                break

    consecutive_rate = consecutive_count / 100 * 100
    report.write(f"连号出现率: {consecutive_rate:.2f}%\n")

    # 计算奇偶比例
    odd_count = 0
    even_count = 0
    for draw in recent_100:
        front_numbers = draw.get('front_numbers', [])
        for num in front_numbers:
            if num % 2 == 0:
                even_count += 1
            else:
                odd_count += 1

    total_numbers = odd_count + even_count
    odd_rate = odd_count / total_numbers * 100
    even_rate = even_count / total_numbers * 100
    report.write(f"奇数比例: {odd_rate:.2f}%\n")
    report.write(f"偶数比例: {even_rate:.2f}%\n")

    # 计算大小比例（以18为界限）
    small_count = 0
    large_count = 0
    for draw in recent_100:
        front_numbers = draw.get('front_numbers', [])
        for num in front_numbers:
            if num <= 18:
                small_count += 1
            else:
                large_count += 1

    small_rate = small_count / total_numbers * 100
    large_rate = large_count / total_numbers * 100
    report.write(f"小号(1-18)比例: {small_rate:.2f}%\n")
    report.write(f"大号(19-35)比例: {large_rate:.2f}%\n")

    # 计算和值分布
    sum_values = []
    for draw in recent_100:
        front_numbers = draw.get('front_numbers', [])
        sum_values.append(sum(front_numbers))

    avg_sum = sum(sum_values) / len(sum_values)
    min_sum = min(sum_values)
    max_sum = max(sum_values)
    report.write(f"前区和值平均: {avg_sum:.2f}\n")
    report.write(f"前区和值范围: {min_sum} - {max_sum}\n")

    # 生成和值分布图
    plt.figure(figsize=(12, 6))
    plt.hist(sum_values, bins=20, color='purple', alpha=0.7)
    plt.axvline(x=avg_sum, color='red', linestyle='--', label=f'平均值: {avg_sum:.2f}')
    plt.title('最近100期大乐透前区和值分布')
    plt.xlabel('和值')
    plt.ylabel('频率')
    plt.grid(linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '前区和值分布_100期.png'))
    plt.close()

print(f"分析完成！报告已保存到 {report_file}")
print(f"图表已保存到 {output_dir} 目录")
