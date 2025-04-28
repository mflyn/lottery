import pandas as pd
import numpy as np
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path
import time

# 定义日期限制
DATE_LIMIT = pd.to_datetime('2020-01-01')

class LotteryDataManager:
    """彩票数据管理器"""
    
    def __init__(self, data_path: str):
        """初始化数据管理器
        
        Args:
            data_path: 数据文件路径
        """
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # 支持的彩票类型
        self.LOTTERY_TYPES = {
            'ssq': '双色球',
            'dlt': '大乐透'
        }
        
        # 数据文件路径 (改为 JSON)
        self.data_files = {
            'ssq': self.data_path / 'ssq_history.json',
            'dlt': self.data_path / 'dlt_history.json'
        }

    def get_history_data(self, lottery_type: str, periods: Optional[int] = None) -> pd.DataFrame:
        """获取历史数据 (从 JSON 文件读取)
        
        Args:
            lottery_type: 彩票类型 ('ssq'/'dlt')
            periods: 获取期数，None表示获取所有历史数据
            
        Returns:
            历史数据DataFrame，包含 'data' 键下的列表数据
        """
        if lottery_type not in self.LOTTERY_TYPES:
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
            
        try:
            file_path = self.data_files[lottery_type]
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                # 假设 JSON 文件结构为 {'data': [...], 'fetch_time': ..., 'total_periods': ...}
                data_list = raw_data.get('data', [])
                if not data_list:
                     return pd.DataFrame()

                df = pd.DataFrame(data_list)

                # --- 确保核心列存在并进行必要转换 --- >
                required_cols = {
                    'ssq': ['draw_num', 'draw_date', 'red_numbers', 'blue_number', 'sales', 'prize_pool'],
                    'dlt': ['draw_num', 'draw_date', 'front_numbers', 'back_numbers', 'sales', 'prize_pool']
                }
                if not all(col in df.columns for col in required_cols[lottery_type]):
                    self.logger.error(f"{file_path} 缺少必需的列。预期: {required_cols[lottery_type]}, 实际: {list(df.columns)}")
                    # 尝试保留共有列，但可能导致后续分析失败
                    common_cols = list(set(df.columns) & set(required_cols[lottery_type]))
                    if not common_cols:
                        return pd.DataFrame()
                    df = df[common_cols]
                    # return pd.DataFrame() # 或者直接返回空，更安全

                # --- 统一 date 字段格式并排序 --- >
                if 'draw_date' in df.columns:
                     try:
                         df['draw_date'] = pd.to_datetime(df['draw_date'].astype(str).str[:10])
                         # 按日期降序排序 (最新在前)
                         df = df.sort_values('draw_date', ascending=False)
                     except Exception as e:
                          self.logger.error(f"处理 draw_date 列时出错: {e}, 将尝试继续但不排序。")
                else:
                     self.logger.warning(f"{file_path} 缺少 'draw_date' 列，无法排序和过滤日期。")
                     # 如果没有日期列，无法按日期过滤，可以选择返回全部或报错
                     # return pd.DataFrame() # 或者返回空 DataFrame

                # --- 添加日期过滤 --- >
                if 'draw_date' in df.columns:
                     original_count = len(df)
                     df = df[df['draw_date'] >= DATE_LIMIT].copy() # 使用 .copy() 避免 SettingWithCopyWarning
                     filtered_count = len(df)
                # <-------------------

                # 转换 'numbers' 列（如果存在且需要的话，但优选直接使用号码列表列）
                if 'numbers' in df.columns and lottery_type == 'ssq' and 'red_numbers' not in df.columns:
                    # 尝试从 'numbers' 列恢复号码列表
                     try:
                         split_nums = df['numbers'].str.split(',', expand=True)
                         if split_nums.shape[1] == 7:
                             df['red_numbers'] = split_nums.iloc[:, :6].apply(lambda row: [int(n) for n in row], axis=1)
                             df['blue_number'] = split_nums.iloc[:, 6].astype(int) # 注意这里是单个数字，非列表
                         else: self.logger.warning("ssq numbers 列格式不为 7 位")
                     except Exception as e: self.logger.error(f"从 ssq numbers 列恢复失败: {e}")
                elif 'numbers' in df.columns and lottery_type == 'dlt' and 'front_numbers' not in df.columns:
                     try:
                         split_nums = df['numbers'].str.split(',', expand=True)
                         if split_nums.shape[1] == 7:
                             df['front_numbers'] = split_nums.iloc[:, :5].apply(lambda row: [int(n) for n in row], axis=1)
                             df['back_numbers'] = split_nums.iloc[:, 5:].apply(lambda row: [int(n) for n in row], axis=1)
                         else: self.logger.warning("dlt numbers 列格式不为 7 位")
                     except Exception as e: self.logger.error(f"从 dlt numbers 列恢复失败: {e}")

                # 确保数值列是数值类型
                numeric_cols = ['sales', 'prize_pool']
                for col in numeric_cols:
                     if col in df.columns:
                         df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                # <-------------------------------------

                if periods:
                    df = df.head(periods)

                return df
            else:
                self.logger.warning(f"数据文件不存在: {file_path}")
                return pd.DataFrame()
                
        except json.JSONDecodeError as e:
             self.logger.error(f"读取 JSON 文件失败: {file_path}, 错误: {e}")
             return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"获取历史数据失败: {str(e)}")
            return pd.DataFrame()

    def update_data(self, lottery_type: str) -> bool:
        """更新最新数据 (保存为 JSON)
        
        Args:
            lottery_type: 彩票类型
            
        Returns:
            更新是否成功
        """
        try:
            # 获取在线最新数据 (已经是处理好的字典列表)
            new_data_list = self._fetch_online_data_as_list(lottery_type)
            if new_data_list is None: # 注意区分 None (获取失败) 和 [] (无新数据)
                return False

            # 读取现有数据
            file_path = self.data_files[lottery_type]
            existing_data_list = []
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_raw_data = json.load(f)
                    existing_data_list = existing_raw_data.get('data', [])
                except json.JSONDecodeError:
                    self.logger.warning(f"现有 JSON 文件格式错误: {file_path}，将覆盖。")
                except Exception as e:
                    self.logger.error(f"读取现有 JSON 文件时出错: {e}，将尝试覆盖。")

            # 合并数据并去重 (基于字典列表操作)
            combined_data_dict = {item['draw_num']: item for item in existing_data_list}
            new_items_added = 0
            for item in new_data_list:
                if item['draw_num'] not in combined_data_dict:
                    combined_data_dict[item['draw_num']] = item
                    new_items_added += 1

            if new_items_added == 0 and new_data_list is not None: # 检查是否真的获取了数据但无新内容
                 self.logger.info(f"没有新的 {lottery_type} 数据需要更新。")
                 return True # 认为更新成功，因为没有新数据

            final_data_list = list(combined_data_dict.values())

            # 按期号降序排序 (期号通常是年份+序号，可以转数字比较)
            try:
                 final_data_list.sort(key=lambda x: int(x['draw_num']), reverse=True)
            except (ValueError, TypeError):
                 self.logger.warning("部分期号无法转换为整数进行排序，将按字符串排序。")
                 final_data_list.sort(key=lambda x: x['draw_num'], reverse=True)

            # 准备保存的数据结构
            output_data = {
                'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_periods': len(final_data_list),
                'data': final_data_list
            }

            # 保存更新后的数据到 JSON 文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"数据更新成功: {lottery_type}，新增 {new_items_added} 条记录，总计 {len(final_data_list)} 条。")
            return True

        except Exception as e:
            self.logger.error(f"更新数据失败: {str(e)}", exc_info=True) # 打印 traceback
            return False

    def _fetch_online_data_as_list(self, lottery_type: str, page_size: int = 30) -> Optional[List[Dict]]:
        """获取在线数据并直接返回解析后的字典列表 (参考旧代码)
        
        Args:
            lottery_type: 彩票类型 ('ssq'/'dlt')
            page_size: 获取的记录条数，默认为30
            
        Returns:
            包含最新数据的字典列表，获取失败则返回 None
        """
        if lottery_type == 'ssq':
            base_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
            params = {
                "name": "ssq",
                "pageSize": str(page_size), # 获取最近 page_size 期
                "pageNo": "1",
                "systemType": "0"
            }
            headers = { # 使用旧代码中的 Headers
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Referer': 'https://www.cwl.gov.cn/kjxx/ssq/kjgg/',
                'Origin': 'https://www.cwl.gov.cn'
            }
        elif lottery_type == 'dlt':
            base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
            params = {
                "gameNo": "85",
                "provinceId": "0",
                "pageSize": str(page_size),
                "isVerify": "1",
                "pageNo": "1"
            }
            headers = { # 使用旧代码中的 Headers
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Referer': 'https://www.sporttery.cn/',
                'Origin': 'https://www.sporttery.cn'
            }
        else:
            self.logger.error(f"不支持的彩票类型: {lottery_type}")
            return None

        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()

            extracted_data_list = []
            if lottery_type == 'ssq':
                if data.get('message') == "查询成功" and 'result' in data and isinstance(data['result'], list):
                    for item in data['result']:
                        try:
                            draw_num = item.get('code')
                            draw_date = item.get('date', '').split()[0] # 取日期部分
                            red_str = item.get('red', '')
                            blue_str = item.get('blue', '')
                            prize_pool_str = item.get('poolmoney', '0')
                            sales_str = item.get('sales', '0')

                            # --- 添加日期检查 --- >
                            try:
                                draw_dt = pd.to_datetime(draw_date)
                                if draw_dt < DATE_LIMIT:
                                     continue # 跳过早于限制日期的记录
                            except ValueError:
                                 self.logger.warning(f"SSQ 期号 {draw_num} 日期格式无法解析: {draw_date}，已跳过。")
                                 continue
                            # <-------------------

                            if not all([draw_num, draw_date, red_str, blue_str]):
                                self.logger.warning(f"SSQ 期号 {draw_num} 数据不完整，已跳过: {item}")
                                continue

                            red_numbers = sorted([int(n) for n in red_str.split(',')])
                            blue_number = int(blue_str)

                            # 号码验证 (参考旧代码)
                            if (len(red_numbers) != 6 or
                                not all(1 <= n <= 33 for n in red_numbers) or
                                not (1 <= blue_number <= 16) or
                                len(set(red_numbers)) != 6):
                                self.logger.warning(f"SSQ 期号 {draw_num} 号码验证失败，已跳过: red={red_numbers}, blue={blue_number}")
                                continue

                            # 获取奖级信息 (参考旧代码)
                            prizegrades = item.get('prizegrades', [])
                            first_prize_num = prizegrades[0].get('typenum', '0') if prizegrades else '0' # 旧代码用 num?
                            first_prize_amount = prizegrades[0].get('typemoney', '0') if prizegrades else '0' # 旧代码用 money?

                            extracted_data_list.append({
                                'draw_num': draw_num,
                                'draw_date': draw_date,
                                'red_numbers': red_numbers, # 直接存储列表
                                'blue_number': blue_number, # 直接存储数字
                                'prize_pool': prize_pool_str, # 保持字符串，后续处理
                                'sales': sales_str,         # 保持字符串，后续处理
                                'first_prize_num': first_prize_num,
                                'first_prize_amount': first_prize_amount
                                # 可以根据需要添加其他奖级信息
                            })
                        except (ValueError, TypeError, KeyError, IndexError) as e:
                            self.logger.error(f"解析 SSQ item {item.get('code')} 时出错: {e}", exc_info=True)
                            continue
                else:
                     self.logger.warning(f"在线获取 SSQ 数据失败: API 响应状态或消息不正确。State: {data.get('state')}, Message: {data.get('message')}")
                     return None # API 返回错误，获取失败

            elif lottery_type == 'dlt':
                # --- DLT 分页获取逻辑 --- >
                page_no = 1
                total_pages = 1 # 初始假设至少有1页
                all_dlt_items = []
                max_pages_to_fetch = 100 # 设置一个最大页数限制，防止无限循环
                fetch_delay = 1 # 每页请求间隔秒数
                stop_fetching = False # 标记是否因日期过早而停止

                while page_no <= total_pages and page_no <= max_pages_to_fetch:
                    params['pageNo'] = str(page_no)
                    try:
                        response = requests.get(base_url, params=params, headers=headers, timeout=20)
                        response.raise_for_status()
                        data = response.json()

                        if data.get('success') and 'value' in data and 'list' in data['value']:
                            page_items = data['value']['list']
                            if not page_items and page_no > 1: # 如果不是第一页且返回为空，说明获取完毕
                                break

                            all_dlt_items.extend(page_items)

                            # --- 添加日期检查，如果本页最旧的数据已早于限制，则停止 --- >
                            if page_items:
                                 last_item_date_str = page_items[-1].get('lotteryDrawTime', '').split()[0]
                                 try:
                                     last_item_dt = pd.to_datetime(last_item_date_str)
                                     if last_item_dt < DATE_LIMIT:
                                          stop_fetching = True
                                 except ValueError:
                                      self.logger.warning(f"DLT 无法解析页面 {page_no} 最后一条记录的日期: {last_item_date_str}")
                            # <-----------------------------------------------------------

                            # 更新总页数 (只在第一页或 total_pages 仍为初始值时更新)
                            if page_no == 1 or total_pages == 1:
                                total_count = data['value'].get('total', 0)
                                page_size_from_param = int(params.get('pageSize', 30))
                                if total_count > 0 and page_size_from_param > 0:
                                     total_pages = (total_count + page_size_from_param - 1) // page_size_from_param

                            page_no += 1
                            # 添加延时防止请求过快
                            if page_no <= total_pages and page_no <= max_pages_to_fetch and not stop_fetching:
                                 time.sleep(fetch_delay)
                            elif stop_fetching:
                                 break # 如果日期过早，跳出循环

                        else:
                            self.logger.warning(f"在线获取 DLT 数据失败 (Page {page_no}): success={data.get('success')}, message={data.get('message')}")
                            break # 单页失败则停止

                    except requests.exceptions.RequestException as e:
                        self.logger.error(f"获取 DLT 第 {page_no} 页网络请求失败: {str(e)}")
                        break # 网络错误则停止
                    except (json.JSONDecodeError, KeyError, Exception) as e:
                        self.logger.error(f"解析 DLT 第 {page_no} 页数据或发生其他错误: {str(e)}", exc_info=True)
                        break # 解析错误则停止
                # <--- DLT 分页结束 ---

                # --- 解析所有获取到的 DLT items --- >
                for item in all_dlt_items:
                     try:
                        draw_num = item.get('lotteryDrawNum')
                        draw_date = item.get('lotteryDrawTime', '').split()[0] # 取日期部分
                        numbers_str = item.get('lotteryDrawResult', '')
                        numbers_list = numbers_str.split()
                        prize_pool_str = item.get('poolBalanceAfterdraw', '0')
                        sales_str = item.get('totalSaleAmount', '0')

                        # --- 添加日期检查 (虽然分页处已检查，这里再加一层保险) --- >
                        try:
                            draw_dt = pd.to_datetime(draw_date)
                            if draw_dt < DATE_LIMIT:
                                 continue
                        except ValueError:
                             self.logger.warning(f"DLT 期号 {draw_num} 日期格式无法解析: {draw_date}，已跳过。")
                             continue
                        # <-------------------

                        if not all([draw_num, draw_date, len(numbers_list) >= 7]):
                            self.logger.warning(f"DLT 期号 {draw_num} 数据不完整，已跳过: {item}")
                            continue

                        front_numbers = sorted([int(n) for n in numbers_list[:5]])
                        back_numbers = sorted([int(n) for n in numbers_list[5:7]])

                        # 号码验证 (参考旧代码)
                        if (len(front_numbers) != 5 or len(back_numbers) != 2 or
                            not all(1 <= n <= 35 for n in front_numbers) or
                            not all(1 <= n <= 12 for n in back_numbers) or
                            len(set(front_numbers)) != 5 or len(set(back_numbers)) != 2):
                            self.logger.warning(f"DLT 期号 {draw_num} 号码验证失败，已跳过: front={front_numbers}, back={back_numbers}")
                            continue

                        # 获取奖级信息 (参考旧代码)
                        prize_levels = item.get('prizeLevelList', [])
                        first_prize_num = prize_levels[0].get('stakeCount', '0') if prize_levels else '0'
                        first_prize_amount = prize_levels[0].get('stakeAmount', '0') if prize_levels else '0'

                        extracted_data_list.append({
                            'draw_num': draw_num,
                            'draw_date': draw_date,
                            'front_numbers': front_numbers, # 直接存储列表
                            'back_numbers': back_numbers,   # 直接存储列表
                            'prize_pool': prize_pool_str,
                            'sales': sales_str,
                            'first_prize_num': first_prize_num,
                            'first_prize_amount': first_prize_amount
                        })
                     except (ValueError, TypeError, KeyError, IndexError) as e:
                         self.logger.error(f"解析 DLT item {item.get('lotteryDrawNum')} 时出错: {e}", exc_info=True)
                         continue
                # <--- 解析结束 ---
            else:
                 return None # 不支持的彩票类型

            if not extracted_data_list:
                 self.logger.info(f"从在线 API 获取到 {lottery_type} 的 0 条有效新数据。")
                 # return [] # 返回空列表表示无新数据，而非获取失败 (让调用者判断)
                 # 改为返回None，因为 update_data 会处理 None 和 [] 的情况
                 # 如果返回[]，update_data 可能会错误地认为更新成功但无新数据
                 # 还是返回 [] 比较好，表示请求成功但内容为空或无法解析
                 return []

            return extracted_data_list

        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取 {lottery_type} 在线数据网络请求失败: {str(e)}")
            return None # 网络错误，获取失败
        except (json.JSONDecodeError, KeyError, Exception) as e:
            self.logger.error(f"解析 {lottery_type} 在线数据或发生其他错误: {str(e)}", exc_info=True)
            if 'response' in locals():
                 self.logger.debug(f"原始响应内容: {response.text[:500]}...")
            return None # 解析错误，获取失败

    def get_issue_data(self, lottery_type: str, issue: str) -> Optional[Dict]:
        """从本地历史数据中获取指定期号的数据 (从 JSON 读取)
        
        Args:
            lottery_type: 彩票类型 ('ssq'/'dlt')
            issue: 要查询的期号
            
        Returns:
            包含该期号数据的字典 (特别是号码列表)，如果未找到则返回 None
        """
        file_path = self.data_files[lottery_type]
        if not file_path.exists():
            self.logger.warning(f"本地 {lottery_type} 数据文件不存在: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            data_list = raw_data.get('data', [])

            for item in data_list:
                if item.get('draw_num') == issue:
                    # 确保返回的号码是列表形式
                    if lottery_type == 'ssq' and isinstance(item.get('red_numbers'), list) and isinstance(item.get('blue_number'), int):
                         # 构造 'numbers' 字符串给 GUI (如果需要的话)
                         item['numbers'] = ",".join(map(str, sorted(item['red_numbers']))) + "," + str(item['blue_number'])
                         return item
                    elif lottery_type == 'dlt' and isinstance(item.get('front_numbers'), list) and isinstance(item.get('back_numbers'), list):
                         item['numbers'] = ",".join(map(str, sorted(item['front_numbers']))) + "," + ",".join(map(str, sorted(item['back_numbers'])))
                         return item
                    else:
                         self.logger.warning(f"期号 {issue} 数据格式不符合预期 (号码非列表): {item}")
                         # 可以尝试从 'numbers' 字段恢复，如果存在
                         if 'numbers' in item:
                              return item
                         else:
                              return None # 格式不对，返回 None

            self.logger.info(f"在本地数据中未找到 {lottery_type} 期号 {issue}")
            return None

        except json.JSONDecodeError as e:
             self.logger.error(f"读取或解析 JSON 文件失败: {file_path}, 错误: {e}")
             return None
        except Exception as e:
            self.logger.error(f"查找期号 {issue} 时发生错误: {e}")
            return None

    def export_data(self, lottery_type: str, file_path: str, format: str = 'json') -> bool:
        """导出数据 (优先导出为 JSON)
        Args:
            format: 支持 'json', 'csv', 'excel'
        """
        file_path_obj = Path(file_path)
        try:
            # 直接复制 JSON 文件
            if format == 'json':
                 source_file = self.data_files[lottery_type]
                 if source_file.exists():
                     import shutil
                     shutil.copyfile(source_file, file_path_obj)
                     return True
                 else:
                     self.logger.warning(f"源 JSON 文件不存在: {source_file}")
                     return False
            else:
                # 对于其他格式，先加载为 DataFrame 再导出
                df = self.get_history_data(lottery_type)
                if df.empty:
                    self.logger.warning(f"无法加载 {lottery_type} 数据进行导出。")
                    return False
                if format == 'csv':
                    df.to_csv(file_path_obj, index=False, encoding='utf-8-sig') # 使用 utf-8-sig 避免 Excel 中文乱码
                elif format == 'excel':
                    df.to_excel(file_path_obj, index=False, engine='openpyxl') # 需要安装 openpyxl
                else:
                    raise ValueError(f"不支持的导出格式: {format}")
                return True
        except ImportError:
             if format == 'excel':
                 self.logger.error("导出 Excel 需要安装 'openpyxl' 库 (pip install openpyxl)。")
             return False
        except Exception as e:
            self.logger.error(f"导出数据到 {file_path} ({format}) 失败: {str(e)}")
            return False

    def import_data(self, file_path: str, lottery_type: str) -> bool:
        """导入数据 (支持 JSON, CSV, Excel)
        Args:
            file_path: 导入文件路径
            lottery_type: 彩票类型
        Returns:
            导入是否成功
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            self.logger.error(f"导入文件不存在: {file_path}")
            return False

        try:
            imported_data_list = []
            if file_path.endswith('.json'):
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    imported_raw_data = json.load(f)
                # 假设导入的 JSON 也有 'data' 键
                imported_data_list = imported_raw_data.get('data', [])
                if not imported_data_list and isinstance(imported_raw_data, list):
                     # 如果直接是列表，则使用整个列表
                     imported_data_list = imported_raw_data
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path_obj)
                # 需要将 DataFrame 转换为字典列表，并处理号码列
                # TODO: 实现 CSV 到字典列表的转换，确保号码格式正确
                self.logger.warning("从 CSV 导入数据的功能暂未完全实现号码格式转换。")
                imported_data_list = df.to_dict('records')
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path_obj)
                # TODO: 实现 Excel 到字典列表的转换
                self.logger.warning("从 Excel 导入数据的功能暂未完全实现号码格式转换。")
                imported_data_list = df.to_dict('records')
            else:
                raise ValueError("不支持的导入文件格式")

            if not imported_data_list:
                 self.logger.warning(f"从 {file_path} 未能解析出数据列表。")
                 return False

            # TODO: 添加更严格的数据格式验证 _validate_data_format

            # 合并现有数据 (与 update_data 逻辑类似)
            target_file_path = self.data_files[lottery_type]
            existing_data_list = []
            if target_file_path.exists():
                try:
                    with open(target_file_path, 'r', encoding='utf-8') as f:
                        existing_raw_data = json.load(f)
                    existing_data_list = existing_raw_data.get('data', [])
                except Exception as e:
                    self.logger.warning(f"读取现有数据文件 {target_file_path} 出错: {e}，将覆盖。")

            combined_data_dict = {item['draw_num']: item for item in existing_data_list}
            imported_count = 0
            for item in imported_data_list:
                # 基本检查，确保有期号
                if isinstance(item, dict) and 'draw_num' in item:
                    if item['draw_num'] not in combined_data_dict:
                        # TODO: 更严格的格式校验，确保存入的数据包含所有必需字段和正确类型
                        combined_data_dict[item['draw_num']] = item
                        imported_count += 1
                else:
                    self.logger.warning(f"跳过无效的导入数据项: {item}")

            final_data_list = list(combined_data_dict.values())
            final_data_list.sort(key=lambda x: x.get('draw_num', '0'), reverse=True)

            output_data = {
                'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_periods': len(final_data_list),
                'data': final_data_list
            }

            with open(target_file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"成功从 {file_path} 导入 {imported_count} 条新记录到 {target_file_path}。")
            return True

        except Exception as e:
            self.logger.error(f"导入数据失败: {str(e)}", exc_info=True)
            return False

    def _validate_data_format(self, data: pd.DataFrame, lottery_type: str) -> bool:
        """验证数据格式"""
        required_columns = {
            'ssq': ['date', 'issue', 'numbers', 'prize_pool', 'sales'],
            'dlt': ['date', 'issue', 'numbers', 'prize_pool', 'sales']
        }
        
        # 检查必需列
        if not all(col in data.columns for col in required_columns[lottery_type]):
            return False
            
        # 验证日期格式
        try:
            pd.to_datetime(data['date'])
        except:
            return False
            
        # 验证期号格式
        if not data['issue'].astype(str).str.match(r'^\d{8}$').all():
            return False
            
        return True

    def get_statistics(self, lottery_type: str, start_date: Optional[str] = None) -> Dict[str, Any]:
        """获取统计数据
        
        Args:
            lottery_type: 彩票类型
            start_date: 开始日期，None表示所有历史数据
            
        Returns:
            统计结果字典
        """
        try:
            data = self.get_history_data(lottery_type)
            if data.empty:
                return {}
                
            if start_date:
                data = data[data['date'] >= start_date]
                
            # 计算基础统计数据
            stats = {
                'total_periods': len(data),
                'total_sales': data['sales'].sum(),
                'avg_sales': data['sales'].mean(),
                'total_prize': data['prize_pool'].sum(),
                'avg_prize': data['prize_pool'].mean(),
                'last_updated': data['date'].max().strftime('%Y-%m-%d'),
                'first_period': data['date'].min().strftime('%Y-%m-%d')
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取统计数据失败: {str(e)}")
            return {}
