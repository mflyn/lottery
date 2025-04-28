#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
双色球数据获取模块
"""

import requests
from typing import Dict, List, Optional
from .data_fetcher import LotteryDataFetcher

class SSQDataFetcher(LotteryDataFetcher):
    """双色球数据获取类"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.cwl.gov.cn/kjxx/ssq/kjgg/'
        }
    
    def fetch_latest(self) -> Optional[Dict]:
        """获取最新一期开奖数据"""
        data = self.fetch_by_page(1, 1)
        if data and 'result' in data and len(data['result']) > 0:
            return self._parse_draw_data(data['result'][0])
        return None
    
    def fetch_by_term(self, term: str) -> Optional[Dict]:
        """根据期号获取开奖数据"""
        params = {
            "name": "ssq",
            "issueCount": term,
            "pageSize": "1",
            "pageNo": "1"
        }
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data and 'result' in data and len(data['result']) > 0:
                    return self._parse_draw_data(data['result'][0])
        except Exception as e:
            print(f"获取数据失败: {e}")
        return None

    def _parse_draw_data(self, raw_data: Dict) -> Dict:
        """解析开奖数据"""
        return {
            'term': raw_data.get('code'),
            'date': raw_data.get('date'),
            'red_numbers': [int(n) for n in raw_data.get('red', '').split(',')],
            'blue_number': int(raw_data.get('blue'))
        }