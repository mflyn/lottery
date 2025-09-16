#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大乐透数据获取模块
"""

import requests
from typing import Dict, Optional
from .data_fetcher import LotteryDataFetcher

class DLTDataFetcher(LotteryDataFetcher):
    """大乐透数据获取类"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
    
    def fetch_latest(self) -> Optional[Dict]:
        """获取最新一期开奖数据"""
        params = {
            "gameNo": "85",
            "pageSize": "1",
            "pageNo": "1",
            "isVerify": "1"
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
                if data and 'value' in data and 'list' in data['value']:
                    return self._parse_draw_data(data['value']['list'][0])
        except Exception as e:
            print(f"获取数据失败: {e}")
        return None
    
    def fetch_by_term(self, term: str) -> Optional[Dict]:
        """根据期号获取开奖数据"""
        params = {
            "gameNo": "85",
            "pageSize": "1",
            "pageNo": "1",
            "issueNo": term,
            "isVerify": "1"
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
                if data and 'value' in data and 'list' in data['value']:
                    return self._parse_draw_data(data['value']['list'][0])
        except Exception as e:
            print(f"获取数据失败: {e}")
        return None

    def _parse_draw_data(self, raw_data: Dict) -> Dict:
        """解析开奖数据"""
        return {
            'term': raw_data.get('lotteryDrawNum'),
            'date': raw_data.get('lotteryDrawTime'),
            'front_numbers': [int(n) for n in raw_data.get('lotteryDrawResult', '').split(' ')[:5]],
            'back_numbers': [int(n) for n in raw_data.get('lotteryDrawResult', '').split(' ')[5:]]
        }