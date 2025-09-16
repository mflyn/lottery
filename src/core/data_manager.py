import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import time
from .config_manager import get_config_manager
from .network_client import get_network_client
from .validation import DataValidator, DataCleaner
from .api_parsers import get_parser

class LotteryDataManager:
    """彩票数据管理器"""

    def __init__(self, data_path: Optional[str] = None):
        """初始化数据管理器

        Args:
            data_path: 数据文件路径，如果为None则使用配置中的路径
        """
        self.config_manager = get_config_manager()
        
        # 使用配置管理器获取数据路径
        if data_path is None:
            data_path = self.config_manager.get_data_path()
        
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # 从配置获取支持的彩票类型
        self.LOTTERY_TYPES = {}
        for lottery_type in self.config_manager.get('lottery.supported_types', ['ssq', 'dlt']):
            config = self.config_manager.get_lottery_config(lottery_type)
            self.LOTTERY_TYPES[lottery_type] = config.get('name', lottery_type.upper())

        # 数据文件路径 (改为 JSON)
        self.data_files = {
            lottery_type: self.data_path / f'{lottery_type}_history.json'
            for lottery_type in self.LOTTERY_TYPES.keys()
        }
        
        # 从配置获取日期限制
        self.date_limit = pd.to_datetime(self.config_manager.get('data.date_limit', '2020-01-01'))
        
        # 初始化验证器和清洗器
        self.validators = {
            lottery_type: DataValidator(lottery_type) 
            for lottery_type in self.LOTTERY_TYPES.keys()
        }
        self.cleaners = {
            lottery_type: DataCleaner(lottery_type)
            for lottery_type in self.LOTTERY_TYPES.keys()
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
                     df = df[df['draw_date'] >= self.date_limit].copy() # 使用 .copy() 避免 SettingWithCopyWarning
                     filtered_count = len(df)
                     if original_count > filtered_count:
                         self.logger.info(f"日期过滤: {original_count} -> {filtered_count} 条记录")
                # <-------------------

                # 转换 'numbers' 列（如果存在且需要的话，但优选直接使用号码列表列）
                if 'numbers' in df.columns and lottery_type == 'ssq' and 'red_numbers' not in df.columns:
                    # 尝试从 'numbers' 列恢复号码列表
                     try:
                         split_nums = df['numbers'].str.split(',', expand=True)
                         if split_nums.shape[1] == 7:
                             df['red_numbers'] = split_nums.iloc[:, :6].apply(lambda row: [int(n) for n in row], axis=1)
                             df['blue_number'] = split_nums.iloc[:, 6].astype(int) # 注意这里是单个数字，非列表
                         else:
                             self.logger.warning("ssq numbers 列格式不为 7 位")
                     except Exception as e:
                         self.logger.error(f"从 ssq numbers 列恢复失败: {e}")
                elif 'numbers' in df.columns and lottery_type == 'dlt' and 'front_numbers' not in df.columns:
                     try:
                         split_nums = df['numbers'].str.split(',', expand=True)
                         if split_nums.shape[1] == 7:
                             df['front_numbers'] = split_nums.iloc[:, :5].apply(lambda row: [int(n) for n in row], axis=1)
                             df['back_numbers'] = split_nums.iloc[:, 5:].apply(lambda row: [int(n) for n in row], axis=1)
                         else:
                             self.logger.warning("dlt numbers 列格式不为 7 位")
                     except Exception as e:
                         self.logger.error(f"从 dlt numbers 列恢复失败: {e}")

                # 确保数值列是数值类型
                numeric_cols = ['sales', 'prize_pool']
                for col in numeric_cols:
                     if col in df.columns:
                         df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                # <-------------------------------------

                # 数据验证和清洗
                if not df.empty:
                    try:
                        # 先进行数据清洗
                        df, cleaning_report = self.cleaners[lottery_type].clean_data(
                            df, auto_fix=True, remove_invalid=True
                        )
                        
                        # 记录清洗结果
                        if cleaning_report['data_quality']['data_quality_score'] < 95:
                            self.logger.warning(
                                f"{lottery_type} 数据质量评分: "
                                f"{cleaning_report['data_quality']['data_quality_score']:.1f}%"
                            )
                        
                        # 最终验证
                        validation_result = self.validators[lottery_type].validate(df)
                        if not validation_result['valid']:
                            self.logger.warning(
                                f"{lottery_type} 数据验证发现 {validation_result['summary']['error_count']} 个错误"
                            )
                            
                    except Exception as e:
                        self.logger.error(f"数据验证和清洗失败: {str(e)}")

                # 为分析器添加展开的号码列
                if not df.empty:
                    df = self._expand_number_columns(df, lottery_type)

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

    def _fetch_online_data_as_list(self, lottery_type: str, page_size: int = None) -> Optional[List[Dict]]:
        """获取在线数据并直接返回解析后的字典列表

        Args:
            lottery_type: 彩票类型 ('ssq'/'dlt')
            page_size: 获取的记录条数，如果为None则使用配置中的默认值

        Returns:
            包含最新数据的字典列表，获取失败则返回 None
        """
        # 从配置获取参数
        if page_size is None:
            page_size = self.config_manager.get('api.page_size', 30)
        
        # 获取备选API列表
        backup_apis = self.config_manager.get(f'api.backup_apis.{lottery_type}', [])
        
        # 尝试每个API源
        for api_index, api_config in enumerate(backup_apis):
            api_name = api_config.get('name', f'API{api_index + 1}')
            self.logger.info(f"尝试使用 {api_name} 获取 {lottery_type} 数据...")
            
            try:
                result = self._fetch_from_single_api(api_config, lottery_type, page_size)
                if result:
                    self.logger.info(f"成功从 {api_name} 获取到 {len(result)} 条数据")
                    return result
                else:
                    self.logger.warning(f"{api_name} 返回空数据，尝试下一个API源")
                    
            except Exception as e:
                self.logger.error(f"从 {api_name} 获取数据失败: {str(e)}")
                continue
        
        # 所有API都失败了
        self.logger.error(f"所有 {lottery_type} API源都无法获取数据")
        return None
    
    def _fetch_from_single_api(self, api_config: Dict, lottery_type: str, page_size: int) -> Optional[List[Dict]]:
        """从单个API源获取数据
        
        Args:
            api_config: API配置
            lottery_type: 彩票类型
            page_size: 页面大小
            
        Returns:
            解析后的数据列表
        """
        api_type = api_config.get('type', 'unknown')
        base_url = api_config.get('url')
        base_params = api_config.get('params', {}).copy()
        headers = api_config.get('headers', {})
        
        if not base_url:
            self.logger.error(f"API配置缺少URL: {api_config}")
            return None
        
        # 获取网络客户端
        network_client = get_network_client()
        
        # 获取解析器
        parser = get_parser(api_type)
        
        # 根据API类型调整参数
        if api_type == 'sporttery':
            return self._fetch_sporttery_data(network_client, parser, base_url, base_params, headers, lottery_type, page_size)
        elif api_type in ['500wan', 'sina', 'netease']:
            return self._fetch_simple_api_data(network_client, parser, base_url, base_params, headers, lottery_type, page_size)
        elif api_type == 'cwl':
            return self._fetch_cwl_data(network_client, parser, base_url, base_params, headers, lottery_type, page_size)
        else:
            self.logger.error(f"不支持的API类型: {api_type}")
            return None
    
    def _fetch_sporttery_data(self, network_client, parser, base_url: str, params: Dict, headers: Dict, 
                             lottery_type: str, page_size: int) -> Optional[List[Dict]]:
        """获取体彩网数据（支持分页）"""
        max_pages = self.config_manager.get('api.max_pages', 100)
        all_items = []
        page_no = 1
        fetch_delay = 1
        
        # 更新页面大小参数
        params['pageSize'] = str(page_size)
        
        while page_no <= max_pages:
            params['pageNo'] = str(page_no)
            
            try:
                data = network_client.get_json(base_url, params=params, headers=headers)
                parsed_items = parser.parse(data, lottery_type)
                
                if not parsed_items:
                    if page_no == 1:
                        # 第一页就没数据，可能是API问题
                        self.logger.warning("体彩网API第一页返回空数据")
                        return None
                    else:
                        # 后续页面没数据，正常结束
                        break
                
                all_items.extend(parsed_items)
                
                # 检查日期限制
                if parsed_items:
                    last_item_date_str = parsed_items[-1].get('draw_date', '')
                    try:
                        last_item_dt = pd.to_datetime(last_item_date_str)
                        if last_item_dt < self.date_limit:
                            break
                    except ValueError:
                        pass
                
                # 检查是否还有更多页面
                if isinstance(data, dict) and data.get('success'):
                    total_count = data.get('value', {}).get('total', 0)
                    page_size_param = int(params.get('pageSize', 30))
                    if total_count > 0 and page_size_param > 0:
                        total_pages = (total_count + page_size_param - 1) // page_size_param
                        if page_no >= total_pages:
                            break
                
                page_no += 1
                if page_no <= max_pages:
                    time.sleep(fetch_delay)
                    
            except Exception as e:
                self.logger.error(f"获取体彩网第 {page_no} 页数据失败: {str(e)}")
                if page_no == 1:
                    return None  # 第一页失败直接返回
                else:
                    break  # 后续页面失败则结束
        
        return all_items if all_items else None
    
    def _fetch_simple_api_data(self, network_client, parser, base_url: str, params: Dict, headers: Dict,
                              lottery_type: str, page_size: int) -> Optional[List[Dict]]:
        """获取简单API数据（单次请求）"""
        try:
            # 更新数量参数
            if 'limit' in params:
                params['limit'] = str(page_size)
            elif 'num' in params:
                params['num'] = str(page_size)
            elif 'count' in params:
                params['count'] = str(page_size)
            
            # 根据API类型选择请求方式
            if base_url.endswith('.json'):
                data = network_client.get_json(base_url, params=params, headers=headers)
            else:
                response = network_client.get(base_url, params=params, headers=headers)
                data = response.text
            
            parsed_items = parser.parse(data, lottery_type)
            return parsed_items if parsed_items else None
            
        except Exception as e:
            self.logger.error(f"获取简单API数据失败: {str(e)}")
            return None
    
    def _fetch_cwl_data(self, network_client, parser, base_url: str, params: Dict, headers: Dict,
                       lottery_type: str, page_size: int) -> Optional[List[Dict]]:
        """获取福彩网数据（支持分页）"""
        max_pages = self.config_manager.get('api.max_pages', 100)
        all_items = []
        page_no = 1
        fetch_delay = 1
        
        # 更新页面大小参数
        params['pageSize'] = str(page_size)
        
        while page_no <= max_pages:
            params['pageNo'] = str(page_no)
            
            try:
                data = network_client.get_json(base_url, params=params, headers=headers)
                parsed_items = parser.parse(data, lottery_type)
                
                if not parsed_items:
                    if page_no == 1:
                        self.logger.warning("福彩网API第一页返回空数据")
                        return None
                    else:
                        break
                
                all_items.extend(parsed_items)
                
                # 检查日期限制
                if parsed_items:
                    last_item_date_str = parsed_items[-1].get('draw_date', '')
                    try:
                        last_item_dt = pd.to_datetime(last_item_date_str)
                        if last_item_dt < self.date_limit:
                            break
                    except ValueError:
                        pass
                
                # 检查是否还有更多页面
                if isinstance(data, dict) and data.get('state') == 0:
                    # 福彩网的分页逻辑可能需要根据实际API调整
                    if len(parsed_items) < int(params.get('pageSize', 30)):
                        break  # 返回数据少于请求数量，说明没有更多数据
                
                page_no += 1
                if page_no <= max_pages:
                    time.sleep(fetch_delay)
                    
            except Exception as e:
                self.logger.error(f"获取福彩网第 {page_no} 页数据失败: {str(e)}")
                if page_no == 1:
                    return None
                else:
                    break
        
        return all_items if all_items else None
    


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
        except ValueError:
            return False

        # 验证期号格式
        if not data['issue'].astype(str).str.match(r'^\d{8}$').all():
            return False

        return True

    def validate_data(self, lottery_type: str, data: pd.DataFrame = None) -> Dict[str, Any]:
        """验证数据质量
        
        Args:
            lottery_type: 彩票类型
            data: 要验证的数据，如果为None则验证历史数据
            
        Returns:
            验证报告
        """
        if lottery_type not in self.LOTTERY_TYPES:
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
        
        try:
            if data is None:
                data = self.get_history_data(lottery_type)
            
            if data.empty:
                return {
                    'valid': False,
                    'message': '没有数据可供验证',
                    'total_issues': 0,
                    'errors': [],
                    'warnings': [],
                    'infos': []
                }
            
            # 执行验证
            validation_result = self.validators[lottery_type].validate(data)
            
            # 添加数据统计信息
            validation_result['data_stats'] = {
                'total_records': len(data),
                'date_range': {
                    'start': data['draw_date'].min().strftime('%Y-%m-%d') if 'draw_date' in data.columns else None,
                    'end': data['draw_date'].max().strftime('%Y-%m-%d') if 'draw_date' in data.columns else None
                },
                'latest_issue': data['draw_num'].iloc[0] if 'draw_num' in data.columns and not data.empty else None
            }
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'message': f'验证过程出错: {str(e)}',
                'total_issues': 1,
                'errors': [{'rule': 'validation_error', 'message': str(e)}],
                'warnings': [],
                'infos': []
            }
    
    def clean_data(self, lottery_type: str, data: pd.DataFrame = None, 
                   auto_fix: bool = True, remove_invalid: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """清洗数据
        
        Args:
            lottery_type: 彩票类型
            data: 要清洗的数据，如果为None则清洗历史数据
            auto_fix: 是否自动修复
            remove_invalid: 是否移除无效记录
            
        Returns:
            (清洗后的数据, 清洗报告)
        """
        if lottery_type not in self.LOTTERY_TYPES:
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
        
        try:
            if data is None:
                data = self.get_history_data(lottery_type)
            
            if data.empty:
                return data, {
                    'cleaning_stats': {'total_records': 0, 'cleaned_records': 0},
                    'message': '没有数据可供清洗'
                }
            
            # 执行清洗
            cleaned_data, cleaning_report = self.cleaners[lottery_type].clean_data(
                data, auto_fix=auto_fix, remove_invalid=remove_invalid
            )
            
            return cleaned_data, cleaning_report
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {str(e)}", exc_info=True)
            return data, {
                'cleaning_stats': {'total_records': len(data), 'cleaned_records': 0},
                'error': str(e)
            }

    def _expand_number_columns(self, df: pd.DataFrame, lottery_type: str) -> pd.DataFrame:
        """将列表格式的号码展开为单独的列，供分析器使用"""
        try:
            if lottery_type == 'ssq':
                # 展开红球号码
                if 'red_numbers' in df.columns:
                    red_expanded = pd.DataFrame(df['red_numbers'].tolist(), 
                                              columns=[f'red_{i+1}' for i in range(6)],
                                              index=df.index)
                    df = pd.concat([df, red_expanded], axis=1)
                
                # 蓝球已经是单个数字，重命名即可
                if 'blue_number' in df.columns:
                    df['blue_1'] = df['blue_number']
                    
            elif lottery_type == 'dlt':
                # 展开前区号码
                if 'front_numbers' in df.columns:
                    front_expanded = pd.DataFrame(df['front_numbers'].tolist(),
                                                columns=[f'front_{i+1}' for i in range(5)],
                                                index=df.index)
                    df = pd.concat([df, front_expanded], axis=1)
                
                # 展开后区号码
                if 'back_numbers' in df.columns:
                    back_expanded = pd.DataFrame(df['back_numbers'].tolist(),
                                               columns=[f'back_{i+1}' for i in range(2)],
                                               index=df.index)
                    df = pd.concat([df, back_expanded], axis=1)
                    
        except Exception as e:
            self.logger.error(f"展开号码列失败: {e}")
            
        return df

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
