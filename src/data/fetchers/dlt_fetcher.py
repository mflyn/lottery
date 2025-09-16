from typing import List, Dict
import requests
from datetime import datetime, timedelta
from .base_fetcher import BaseLotteryFetcher

class DLTFetcher(BaseLotteryFetcher):
    """大乐透数据获取器"""
    
    def __init__(self):
        super().__init__()
        self.lottery_type = "dlt"
        self.base_url = "https://www.lottery.gov.cn/dlt"
    
    def fetch_latest(self) -> Dict:
        """获取最新一期数据"""
        try:
            # 先检查缓存
            cache_data = self._load_from_cache("dlt_latest.json")
            if cache_data and self._is_cache_valid(cache_data):
                return cache_data
            
            # 获取最新数据
            response = requests.get(f"{self.base_url}/latest")
            data = self._parse_response(response.text)
            
            # 保存到缓存和数据库
            self._save_to_cache(data, "dlt_latest.json")
            self._save_to_db(data, self.lottery_type)
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取大乐透最新数据失败: {str(e)}")
            raise
    
    def fetch_history(self, start_date: str, end_date: str) -> List[Dict]:
        """获取历史数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
        """
        try:
            results = []
            current_date = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")
                cache_file = f"dlt_history_{date_str}.json"
                
                # 检查缓存
                cache_data = self._load_from_cache(cache_file)
                if cache_data:
                    results.extend(cache_data)
                else:
                    # 获取数据
                    response = requests.get(
                        f"{self.base_url}/history",
                        params={"date": date_str}
                    )
                    data = self._parse_response(response.text)
                    
                    # 保存到缓存和数据库
                    self._save_to_cache(data, cache_file)
                    self._save_to_db(data, self.lottery_type)
                    
                    results.extend(data)
                
                current_date += timedelta(days=1)
            
            return results
            
        except Exception as e:
            self.logger.error(f"获取大乐透历史数据失败: {str(e)}")
            raise
    
    def _parse_response(self, html: str) -> Dict:
        """解析响应数据"""
        # TODO: 实现具体的解析逻辑
        # 解析页面数据
        pass
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """检查缓存是否有效"""
        cache_time = datetime.fromisoformat(cache_data['updated_at'])
        return datetime.now() - cache_time < timedelta(hours=1)