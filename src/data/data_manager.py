from typing import Dict, List, Optional, Any
import pandas as pd
import requests
import json
import threading
import time
from datetime import datetime, timedelta
from src.utils.logger import Logger
from src.data.fetchers.dlt_fetcher import DLTFetcher
from src.data.fetchers.ssq_fetcher import SSQFetcher

class DataManager:
    """数据管理器"""
    def __init__(self):
        self.data = None

    def load_lottery_data(self, lottery_type: str, start_date: Optional[str] = None) -> pd.DataFrame:
        """加载彩票数据"""
        try:
            filepath = f"data/{lottery_type}_data.csv"
            data = pd.read_csv(filepath)
            if start_date:
                data = data[data['date'] >= start_date]
            return data
        except Exception as e:
            print(f"加载数据失败: {str(e)}")
            return pd.DataFrame()

    def fetch_online_data(self, lottery_type: str, limit: int = 1) -> Optional[pd.DataFrame]:
        """获取在线数据
        
        Args:
            lottery_type: 彩票类型
            limit: 获取条数
        Returns:
            DataFrame或None
        """
        try:
            url = f"https://api.lottery.example.com/{lottery_type}/latest?limit={limit}"
            response = requests.get(url)
            response.raise_for_status()
            return pd.DataFrame(response.json())
        except Exception as e:
            print(f"获取在线数据失败: {str(e)}")
            return None

    def export_data(self, data: pd.DataFrame, filename: str) -> bool:
        """导出数据到文件"""
        try:
            data.to_csv(filename, index=False)
            return True
        except Exception as e:
            print(f"导出数据失败: {str(e)}")
            return False

    def load_json_data(self, filename: str) -> Dict:
        """加载JSON数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {filename} not found")
        except Exception as e:
            print(f"加载JSON数据失败: {str(e)}")
            return {}

    def save_json_data(self, data: Dict[str, Any], filepath: str) -> bool:
        """保存JSON数据"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存JSON数据失败: {str(e)}")
            return False

    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据"""
        required_columns = ['date', 'red_1', 'red_2', 'red_3', 'red_4', 'red_5', 'red_6', 'blue']
        return all(col in data.columns for col in required_columns)

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """预处理数据"""
        if data is None or data.empty:
            return pd.DataFrame()
        
        # 基础预处理
        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date', ascending=False)
        
        return data

class LotteryDataManager:
    """彩票数据管理器"""
    
    def __init__(self):
        self.logger = Logger()
        self.fetchers = {
            'dlt': DLTFetcher(),
            'ssq': SSQFetcher()
        }
        self.update_interval = 3600  # 1小时更新一次
        self._stop_flag = False
        self._update_thread = None
    
    def start_auto_update(self):
        """启动自动更新"""
        if self._update_thread is None:
            self._stop_flag = False
            self._update_thread = threading.Thread(
                target=self._auto_update_task,
                daemon=True
            )
            self._update_thread.start()
    
    def stop_auto_update(self):
        """停止自动更新"""
        self._stop_flag = True
        if self._update_thread:
            self._update_thread.join()
            self._update_thread = None
    
    def _auto_update_task(self):
        """自动更新任务"""
        while not self._stop_flag:
            try:
                # 更新所有彩种最新数据
                for lottery_type, fetcher in self.fetchers.items():
                    fetcher.fetch_latest()
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"自动更新失败: {str(e)}")
                time.sleep(300)  # 发生错误时等待5分钟后重试
    
    def get_latest_data(self, lottery_type: str) -> Dict:
        """获取最新数据"""
        fetcher = self.fetchers.get(lottery_type)
        if not fetcher:
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
        return fetcher.fetch_latest()
    
    def get_history_data(self, 
                        lottery_type: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[Dict]:
        """获取历史数据"""
        fetcher = self.fetchers.get(lottery_type)
        if not fetcher:
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
            
        # 默认获取最近30天数据
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start = datetime.now() - timedelta(days=30)
            start_date = start.strftime("%Y-%m-%d")
            
        return fetcher.fetch_history(start_date, end_date)
