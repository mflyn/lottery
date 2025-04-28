import requests
import json
from datetime import datetime
import os

class DualColorBallChecker:
    def __init__(self):
        self.prize_rules = {
            "一等奖": {"red": 6, "blue": 1},
            "二等奖": {"red": 6, "blue": 0},
            "三等奖": {"red": 5, "blue": 1},
            "四等奖": {"red": 5, "blue": 0, "alt": {"red": 4, "blue": 1}},
            "五等奖": {"red": 4, "blue": 0, "alt": {"red": 3, "blue": 1}},
            "六等奖": {"red": 2, "blue": 1, "alt": {"red": 1, "blue": 1}, "alt2": {"red": 0, "blue": 1}}
        }

    def fetch_latest_result(self):
        """从福彩官网获取最新开奖结果"""
        url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        params = {
            "name": "ssq",  # ssq 代表双色球
            "pageSize": "1",
            "pageNo": "1",
            "issueCount": "",
            "issueStart": "",
            "issueEnd": "",
            "dayStart": "",
            "dayEnd": ""
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.cwl.gov.cn/kjxx/ssq/kjgg/',
            'Origin': 'https://www.cwl.gov.cn'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return None
            
            try:
                data = response.json()
                print("API返回的原始数据:")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:500] + "...")
                
                if data.get('message') != "查询成功" or not data.get('result'):
                    print(f"接口返回错误: {data.get('message', '未知错误')}")
                    return None
                
                result = data['result'][0]
                draw_num = result.get('code')  # 期号
                draw_date = result.get('date')  # 开奖日期
                
                # 修改红球解析逻辑：处理逗号分隔的字符串
                red_str = result.get('red', '')
                red_numbers = [int(n) for n in red_str.split(',')]
                
                # 修改蓝球解析逻辑：去掉前导零
                blue_number = int(result.get('blue', '0'))
                
                # 验证数据完整性
                if not all([draw_num, draw_date, len(red_numbers) == 6, blue_number]):
                    print("缺少必要的开奖信息")
                    return None
                
                # 验证双色球号码范围
                if not all(1 <= n <= 33 for n in red_numbers) or not (1 <= blue_number <= 16):
                    print(f"号码范围错误: 红球={red_numbers}, 蓝球={blue_number}")
                    return None
                
                # 验证红球是否有重复
                if len(set(red_numbers)) != 6:
                    print("红球号码有重复")
                    return None
                
                return {
                    'draw_num': draw_num,
                    'draw_date': draw_date,
                    'red_numbers': sorted(red_numbers),
                    'blue_number': blue_number
                }
                
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"原始响应内容: {response.text}")
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {e}")
            return None
        except Exception as e:
            print(f"其他错误: {e}")
            return None

    def check_win(self, my_red, my_blue, result_red, result_blue):
        """检查是否中奖"""
        red_matches = len(set(my_red) & set(result_red))
        blue_matches = 1 if my_blue == result_blue else 0
        
        for prize_level, rule in self.prize_rules.items():
            # 检查主要规则
            if red_matches == rule["red"] and blue_matches == rule["blue"]:
                return prize_level
            
            # 检查替代规则
            if "alt" in rule:
                alt_rule = rule["alt"]
                if red_matches == alt_rule["red"] and blue_matches == alt_rule["blue"]:
                    return prize_level
            
            # 检查第二替代规则（针对六等奖）
            if "alt2" in rule:
                alt2_rule = rule["alt2"]
                if red_matches == alt2_rule["red"] and blue_matches == alt2_rule["blue"]:
                    return prize_level
        
        return None

    def save_numbers(self, numbers, filename="my_numbers_dual.json"):
        """保存购买的号码"""
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "numbers": numbers
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_numbers(self, filename="my_numbers_dual.json"):
        """加载保存的号码"""
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("numbers", [])
        except json.JSONDecodeError as e:
            print(f"读取号码文件失败: {e}")
            return []
        except Exception as e:
            print(f"加载号码时出错: {e}")
            return []

def main():
    checker = DualColorBallChecker()
    
    # 获取最新开奖结果
    result = checker.fetch_latest_result()
    if not result:
        print("无法获取开奖结果，请检查网络连接")
        return

    print(f"\n第{result['draw_num']}期双色球开奖结果：")
    print(f"开奖日期：{result['draw_date']}")
    print(f"红球号码：{result['red_numbers']}")
    print(f"蓝球号码：{result['blue_number']}\n")

    # 加载保存的号码
    my_numbers = checker.load_numbers()
    if not my_numbers:
        print("未找到保存的号码")
        return

    # 读取本地号码的日期
    try:
        with open("my_numbers_dual.json", 'r', encoding='utf-8') as f:
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
            my_red = number["red"]
            my_blue = number["blue"]
            
            print(f"第{i}注号码：")
            print(f"红球：{my_red}")
            print(f"蓝球：{my_blue}")
            
            prize = checker.check_win(
                my_red, 
                my_blue, 
                result['red_numbers'], 
                result['blue_number']
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
