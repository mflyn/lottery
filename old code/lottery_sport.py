import random
import requests
from bs4 import BeautifulSoup

def generate_dlt_numbers():
    """
    根据中国体育彩票大乐透规则，随机生成一注号码：
    前区：从 1 到 35 中随机抽取 5 个数字（不重复）
    后区：从 1 到 12 中随机抽取 2 个数字（不重复）
    """
    front_area = random.sample(range(1, 36), 5)  # 前区号码
    back_area = random.sample(range(1, 13), 2)   # 后区号码
    return front_area, back_area

def main():
    # 总共生成 50000000 注号码
    num_groups = 50_000_000

    # 初始化字典，统计每个号码的出现次数
    front_counts = {num: 0 for num in range(1, 36)}
    back_counts = {num: 0 for num in range(1, 13)}

    # 循环生成号码，并更新统计数据
    for _ in range(num_groups):
        front, back = generate_dlt_numbers()
        for num in front:
            front_counts[num] += 1
        for num in back:
            back_counts[num] += 1

    # 根据出现次数排序，取出现最多的 5 个前区号码
    # 这里先按照出现次数降序排序，若次数相同，则按数字升序排序
    top5_front = sorted(front_counts.items(), key=lambda x: (-x[1], x[0]))[:5]
    # 同理，取出现最多的 2 个后区号码
    top2_back = sorted(back_counts.items(), key=lambda x: (-x[1], x[0]))[:2]

    # 从元组中提取号码，并进行自然排序
    final_front = sorted([num for num, count in top5_front])
    final_back = sorted([num for num, count in top2_back])
    
    # 输出最终结果
    print("前区号码：", final_front, "后区号码：", final_back)

if __name__ == '__main__':
    main()
