import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

class LotteryChecker:
    def __init__(self):
        # 根据官方规则更新中奖规则
        self.prize_rules = [
            {"level": "一等奖", "front": 5, "back": 2},
            {"level": "二等奖", "front": 5, "back": 1},
            {"level": "三等奖", "front": 5, "back": 0},
            {"level": "四等奖", "front": 4, "back": 2},
            {"level": "五等奖", "front": 4, "back": 1},
            {"level": "六等奖", "front": 3, "back": 2},
            {"level": "七等奖", "front": 4, "back": 0},
            {"level": "八等奖", "front": 3, "back": 1},  # 八等奖第一种情况
            {"level": "八等奖", "front": 2, "back": 2},  # 八等奖第二种情况
            {"level": "九等奖", "front": 3, "back": 0},  # 九等奖第一种情况
            {"level": "九等奖", "front": 1, "back": 2},  # 九等奖第二种情况
            {"level": "九等奖", "front": 2, "back": 1},  # 九等奖第三种情况
            {"level": "九等奖", "front": 0, "back": 2}   # 九等奖第四种情况
        ]

    def fetch_latest_result(self):
        """从体彩官网获取最新开奖结果"""
        # 更新为新的 API 地址
        url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=85&provinceId=0&pageSize=1&isVerify=1&pageNo=1"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.sporttery.cn/',
            'Origin': 'https://www.sporttery.cn'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")

            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return None

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"原始响应内容: {response.text}")
                return None

            if data.get('success'):
                result = data['value']['list'][0]
                draw_num = result['lotteryDrawNum']
                draw_date = result['lotteryDrawTime']
                # 分割号码字符串
                numbers = result['lotteryDrawResult'].split(' ')
                front_numbers = [int(n) for n in numbers[:5]]
                back_numbers = [int(n) for n in numbers[5:]]
                return {
                    'draw_num': draw_num,
                    'draw_date': draw_date,
                    'front_numbers': front_numbers,
                    'back_numbers': back_numbers
                }
            else:
                print(f"接口返回错误: {data.get('message')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {e}")
            return None
        except Exception as e:
            print(f"其他错误: {e}")
            return None

    def check_win(self, my_front, my_back, result_front, result_back):
        """检查是否中奖"""
        # 计算前区和后区匹配数
        front_matches = len(set(my_front) & set(result_front))
        back_matches = len(set(my_back) & set(result_back))

        # 检查每个奖级规则
        for rule in self.prize_rules:
            if front_matches == rule["front"] and back_matches == rule["back"]:
                return rule["level"]

        return None

    def save_numbers(self, numbers, filename="my_numbers_sport.json"):  # 修改默认文件名
        """保存购买的号码"""
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "numbers": numbers
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_numbers(self, filename="my_numbers_sport.json"):  # 修改默认文件名
        """加载保存的号码"""
        if not os.path.exists(filename):
            return []
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data["numbers"]

def main():
    checker = LotteryChecker()

    # 获取最新开奖结果
    result = checker.fetch_latest_result()
    if not result:
        print("无法获取开奖结果，请检查网络连接")
        return

    print(f"\n第{result['draw_num']}期大乐透开奖结果：")
    print(f"开奖日期：{result['draw_date']}")
    print(f"前区号码：{result['front_numbers']}")
    print(f"后区号码：{result['back_numbers']}\n")

    # 加载保存的号码
    my_numbers = checker.load_numbers()
    if not my_numbers:
        print("未找到保存的号码")
        return

    # 读取本地号码的日期并进行比较
    try:
        with open("my_numbers_sport.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            local_date = datetime.strptime(data["date"], "%Y-%m-%d")
            draw_date = datetime.strptime(result['draw_date'][:10], "%Y-%m-%d")  # 只取日期部分

            # 比较日期
            if local_date != draw_date:
                print(f"警告：本地号码日期（{local_date.strftime('%Y-%m-%d')}）与开奖日期（{draw_date.strftime('%Y-%m-%d')}）不匹配")
                user_input = input("是否继续查询？(y/n): ")
                if user_input.lower() != 'y':
                    print("查询已取消")
                    return
                print()  # 打印空行，增加可读性
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"读取本地号码日期时出错: {e}")
        return
    except FileNotFoundError:
        print("未找到本地号码文件")
        return

    # 检查每注号码是否中奖
    for i, number in enumerate(my_numbers, 1):
        try:
            my_front = number["front"]
            my_back = number["back"]

            print(f"第{i}注号码：")
            print(f"前区：{my_front}")
            print(f"后区：{my_back}")

            prize = checker.check_win(
                my_front,
                my_back,
                result['front_numbers'],
                result['back_numbers']
            )

            if prize:
                print(f"恭喜中得{prize}！")
            else:
                print("未中奖")
            print()
        except KeyError as e:
            print(f"第{i}注号码格式错误: {e}")
        except Exception as e:
            print(f"处理第{i}注号码时出错: {e}")

if __name__ == "__main__":
    main()
