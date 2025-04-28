import requests
import json
from datetime import datetime
import time
import sys
import os

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

    def fetch_history_page(self, page_no=1, page_size=100):
        """获取指定页码的历史开奖结果"""
        params = {
            "gameNo": "85",  # 85 代表大乐透
            "provinceId": "0",
            "pageSize": str(page_size),
            "isVerify": "1",
            "pageNo": str(page_no)
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
                return None, 0

            data = response.json()
            if not data.get('success'):
                print(f"接口返回错误: {data.get('message', '未知错误')}")
                return None, 0

            # 获取总页数
            total_count = data['value'].get('total', 0)
            total_pages = (total_count + page_size - 1) // page_size

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
                        'first_prize_num': result.get('prizeLevelList', [{}])[0].get('stakeCount', '0'),  # 一等奖注数
                        'first_prize_amount': result.get('prizeLevelList', [{}])[0].get('stakeAmount', '---')  # 一等奖金额
                    }
                    history_data.append(draw_info)
                except Exception as e:
                    print(f"处理期号 {result.get('lotteryDrawNum')} 时出错: {e}")
                    continue

            return history_data, total_pages

        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {e}")
            return None, 0
        except Exception as e:
            print(f"其他错误: {e}")
            return None, 0

    def fetch_all_history(self, max_pages=50, page_size=100, delay=1, resume_from=1):
        """获取所有历史开奖结果，通过分页方式"""
        all_data = []
        page_no = resume_from
        total_pages = 1  # 初始值，会在第一次请求后更新
        max_retries = 3  # 最大重试次数

        print(f"开始获取大乐透历史数据，每页 {page_size} 条，最多获取 {max_pages} 页...")
        print(f"从第 {resume_from} 页开始获取")

        # 创建临时文件夹保存中间结果
        temp_dir = "temp_sport_data"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        while page_no <= min(max_pages, total_pages):
            print(f"正在获取第 {page_no} 页数据...")

            # 检查是否已有缓存
            temp_file = os.path.join(temp_dir, f"page_{page_no}.json")
            if os.path.exists(temp_file):
                try:
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        page_data = json.load(f)
                        print(f"从缓存加载第 {page_no} 页数据，共 {len(page_data)} 条")
                        all_data.extend(page_data)
                        page_no += 1
                        continue
                except Exception as e:
                    print(f"读取缓存文件失败: {e}，将重新获取")

            # 重试机制
            retries = 0
            success = False

            while retries < max_retries and not success:
                try:
                    page_data, new_total_pages = self.fetch_history_page(page_no, page_size)

                    if page_data is None:
                        retries += 1
                        print(f"获取第 {page_no} 页数据失败，第 {retries}/{max_retries} 次重试...")
                        time.sleep(delay * (retries + 1))  # 失败时等待时间递增
                    else:
                        success = True
                except Exception as e:
                    retries += 1
                    print(f"获取第 {page_no} 页数据时发生异常: {e}，第 {retries}/{max_retries} 次重试...")
                    time.sleep(delay * (retries + 1))

            if not success:
                print(f"获取第 {page_no} 页数据失败，已达到最大重试次数，跳过此页")
                page_no += 1
                continue

            all_data.extend(page_data)
            print(f"已获取 {len(page_data)} 条数据，当前总计: {len(all_data)} 条")

            # 保存中间结果
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, ensure_ascii=False, indent=2)
                print(f"已保存第 {page_no} 页数据到缓存")
            except Exception as e:
                print(f"保存缓存文件失败: {e}")

            # 更新总页数
            if page_no == 1:
                total_pages = new_total_pages
                print(f"检测到总共有 {total_pages} 页数据")

            # 防止请求过于频繁
            if page_no < min(max_pages, total_pages):
                print(f"等待 {delay} 秒后继续...")
                time.sleep(delay)

            # 显示进度
            progress = (page_no / min(max_pages, total_pages)) * 100
            print(f"当前进度: {progress:.2f}% ({page_no}/{min(max_pages, total_pages)})")

            page_no += 1

        return all_data

    def save_to_file(self, data, filename="sport_history_full.json"):
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

    def fetch_by_draw_num_range(self, start_draw=7, end_draw=None):
        """通过期号范围获取历史数据"""
        # 先获取最新一期的期号
        latest_data, _ = self.fetch_history_page(1, 1)
        if not latest_data:
            print("无法获取最新期号")
            return None

        latest_draw_num = int(latest_data[0]['draw_num'])
        print(f"最新期号: {latest_draw_num}")

        if end_draw is None or int(end_draw) > latest_draw_num:
            end_draw = latest_draw_num

        start_draw = int(start_draw)
        end_draw = int(end_draw)

        if start_draw > end_draw:
            print("起始期号不能大于结束期号")
            return None

        print(f"准备获取期号范围: {start_draw} - {end_draw}")

        # 使用分页方式获取所有数据
        all_data = self.fetch_all_history(max_pages=100)
        if not all_data:
            print("获取数据失败")
            return None

        # 筛选指定期号范围的数据
        filtered_data = [item for item in all_data if start_draw <= int(item['draw_num']) <= end_draw]
        print(f"筛选后的数据条数: {len(filtered_data)}")

        return filtered_data

def main():
    fetcher = SportLotteryHistoryFetcher()
    print("开始获取大乐透历史开奖数据...")

    # 解析命令行参数
    resume_from = 1
    max_pages = 100
    page_size = 100
    delay = 2

    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        try:
            resume_from = int(sys.argv[1])
            print(f"将从第 {resume_from} 页继续获取数据")
        except ValueError:
            print(f"无效的页码参数: {sys.argv[1]}，将从第 1 页开始")

    # 方法1: 获取所有可用的历史数据（通过分页）
    history_data = fetcher.fetch_all_history(
        max_pages=max_pages,
        page_size=page_size,
        delay=delay,
        resume_from=resume_from
    )

    # 方法2: 通过期号范围获取（大乐透从07001期开始）
    # history_data = fetcher.fetch_by_draw_num_range(7001)

    if not history_data:
        print("获取数据失败")
        return

    print(f"成功获取 {len(history_data)} 期开奖数据")

    # 保存到文件
    fetcher.save_to_file(history_data)

if __name__ == "__main__":
    main()
