import requests
import json
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class DualColorBallHistoryFetcher:
    def __init__(self):
        self.base_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.cwl.gov.cn/kjxx/ssq/kjgg/',
            'Origin': 'https://www.cwl.gov.cn'
        }

    def fetch_history(self, num_periods=5000):
        """获取指定期数的历史开奖结果"""
        params = {
            "name": "ssq",  # ssq 代表双色球
            "pageSize": str(num_periods),
            "pageNo": "1",
            "issueCount": "",
            "issueStart": "",
            "issueEnd": "",
            "dayStart": "",
            "dayEnd": ""
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=20
            )

            print(f"--- 获取 {lottery_type} 原始响应 ---")
            print(response.text) # 打印完整响应内容
            print("--- 原始响应结束 ---")
            response.raise_for_status()
            data = response.json()

            if data.get('message') != "查询成功" or not data.get('result'):
                print(f"接口返回错误: {data.get('message', '未知错误')}")
                return None

            # 处理结果
            history_data = []
            for result in data['result']:
                try:
                    # 解析红球
                    red_str = result.get('red', '')
                    red_numbers = [int(n) for n in red_str.split(',')]

                    # 解析蓝球
                    blue_number = int(result.get('blue', '0'))

                    # 验证数据
                    if (len(red_numbers) != 6 or
                        not all(1 <= n <= 33 for n in red_numbers) or
                        not (1 <= blue_number <= 16) or
                        len(set(red_numbers)) != 6):
                        print(f"期号 {result.get('code')} 数据异常，已跳过")
                        continue

                    draw_info = {
                        'draw_num': result.get('code'),  # 期号
                        'draw_date': result.get('date'),  # 开奖日期
                        'red_numbers': sorted(red_numbers),  # 红球号码
                        'blue_number': blue_number,  # 蓝球号码
                        'prize_pool': result.get('poolmoney'),  # 奖池金额
                        'sales': result.get('sales'),  # 本期销量
                        'first_prize_num': result.get('prizegrades', [])[0].get('num', 0),  # 一等奖注数
                        'first_prize_amount': result.get('prizegrades', [])[0].get('money', 0)  # 一等奖金额
                    }
                    history_data.append(draw_info)
                except Exception as e:
                    print(f"处理期号 {result.get('code')} 时出错: {e}")
                    continue

            return history_data

        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {e}")
            return None
        except Exception as e:
            print(f"其他错误: {e}")
            return None

    def save_to_file(self, data, filename="dual_history.json"):
        """保存数据到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'total_periods': len(data),
                    'data': data
                }, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到 {filename}")
            return True
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return False

def main():
    fetcher = DualColorBallHistoryFetcher()
    print("开始获取双色球历史开奖数据...")

    # 获取历史数据 - 设置一个足够大的数字以获取所有可能的历史数据
    history_data = fetcher.fetch_history(5000)
    if not history_data:
        print("获取数据失败")
        return

    print(f"成功获取 {len(history_data)} 期开奖数据")

    # 保存到文件
    fetcher.save_to_file(history_data)

if __name__ == "__main__":
    main()