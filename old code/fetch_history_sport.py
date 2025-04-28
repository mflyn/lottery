import requests
import json
from datetime import datetime
import time

class SportLotteryHistoryFetcher:
    def __init__(self):
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.sporttery.cn/',
            'Origin': 'https://www.sporttery.cn'
        }

    def fetch_history(self, num_periods=5000):
        """获取指定期数的历史开奖结果"""
        params = {
            "gameNo": "85",  # 85 代表大乐透
            "provinceId": "0",
            "pageSize": str(num_periods),
            "isVerify": "1",
            "pageNo": "1"
        }

        try:
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=self.headers, 
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return None

            data = response.json()
            if not data.get('success'):
                print(f"接口返回错误: {data.get('message', '未知错误')}")
                return None

            # 处理结果
            history_data = []
            for result in data['value']['list']:
                try:
                    # 解析号码
                    numbers = result['lotteryDrawResult'].split(' ')
                    front_numbers = [int(n) for n in numbers[:5]]
                    back_numbers = [int(n) for n in numbers[5:]]
                    
                    # 验证数据
                    if (len(front_numbers) != 5 or 
                        len(back_numbers) != 2 or
                        not all(1 <= n <= 35 for n in front_numbers) or 
                        not all(1 <= n <= 12 for n in back_numbers) or
                        len(set(front_numbers)) != 5 or
                        len(set(back_numbers)) != 2):
                        print(f"期号 {result.get('lotteryDrawNum')} 数据异常，已跳过")
                        continue

                    draw_info = {
                        'draw_num': result['lotteryDrawNum'],  # 期号
                        'draw_date': result['lotteryDrawTime'],  # 开奖日期
                        'front_numbers': sorted(front_numbers),  # 前区号码
                        'back_numbers': sorted(back_numbers),  # 后区号码
                        'prize_pool': result.get('poolBalanceAfterdraw', ''),  # 奖池金额
                        'sales': result.get('totalSaleAmount', ''),  # 本期销量
                        'first_prize_num': result.get('prizeLevelList', [{}])[0].get('stakeCount', 0),  # 一等奖注数
                        'first_prize_amount': result.get('prizeLevelList', [{}])[0].get('stakeAmount', 0)  # 一等奖金额
                    }
                    history_data.append(draw_info)
                except Exception as e:
                    print(f"处理期号 {result.get('lotteryDrawNum')} 时出错: {e}")
                    continue

            return history_data

        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {e}")
            return None
        except Exception as e:
            print(f"其他错误: {e}")
            return None

    def save_to_file(self, data, filename="sport_history.json"):
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
    fetcher = SportLotteryHistoryFetcher()
    print("开始获取大乐透历史开奖数据...")
    
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
