#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
彩票数据获取器
"""

import requests
from typing import Dict, Optional

class DLTDataFetcher:
    """大乐透数据获取器"""
    
    def __init__(self):
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        
    def fetch_history(self, page: int = 1, page_size: int = 50) -> Dict:
        """获取历史开奖数据"""
        params = {
            'gameNo': 85,  # 大乐透的游戏编号
            'pageSize': page_size,
            'pageNo': page,
            'isVerify': 1
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data['success']:
                result = data['value']
                
                # 处理数据
                items = []
                for item in result['list']:
                    # 解析号码
                    numbers = item['lotteryDrawResult'].split()
                    front_numbers = [int(x) for x in numbers[:5]]
                    back_numbers = [int(x) for x in numbers[5:]]
                    
                    items.append({
                        'draw_num': item['lotteryDrawNum'],
                        'draw_date': item['lotteryDrawTime'],
                        'front_numbers': sorted(front_numbers),
                        'back_numbers': sorted(back_numbers),
                        'prize_pool': int(float(item['poolBalanceAmt'])),
                        'sales': int(float(item['totalSaleAmount']))
                    })
                
                return {
                    'items': items,
                    'total_pages': (result['total'] + page_size - 1) // page_size
                }
            else:
                raise Exception(data['message'])
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"数据处理失败: {str(e)}")
            
    def search_history(self, draw_num: Optional[str] = None, draw_date: Optional[str] = None) -> Dict:
        """搜索历史开奖数据"""
        # 这里简化处理,实际可能需要调用不同的API
        data = self.fetch_history(page=1, page_size=100)
        items = data['items']
        
        # 根据条件筛选
        if draw_num:
            items = [item for item in items if draw_num in item['draw_num']]
        if draw_date:
            items = [item for item in items if draw_date in item['draw_date']]
            
        return {
            'items': items,
            'total_pages': 1
        }

class SSQDataFetcher:
    """双色球数据获取器"""
    
    def __init__(self):
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        
    def fetch_history(self, page: int = 1, page_size: int = 50) -> Dict:
        """获取历史开奖数据"""
        params = {
            'gameNo': 1,  # 双色球的游戏编号
            'pageSize': page_size,
            'pageNo': page,
            'isVerify': 1
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data['success']:
                result = data['value']
                
                # 处理数据
                items = []
                for item in result['list']:
                    # 解析号码
                    numbers = item['lotteryDrawResult'].split()
                    red_numbers = [int(x) for x in numbers[:6]]
                    blue_numbers = [int(x) for x in numbers[6:]]
                    
                    items.append({
                        'draw_num': item['lotteryDrawNum'],
                        'draw_date': item['lotteryDrawTime'],
                        'red_numbers': sorted(red_numbers),
                        'blue_numbers': sorted(blue_numbers),
                        'prize_pool': int(float(item['poolBalanceAmt'])),
                        'sales': int(float(item['totalSaleAmount']))
                    })
                
                return {
                    'items': items,
                    'total_pages': (result['total'] + page_size - 1) // page_size
                }
            else:
                raise Exception(data['message'])
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"数据处理失败: {str(e)}")
            
    def search_history(self, draw_num: Optional[str] = None, draw_date: Optional[str] = None) -> Dict:
        """搜索历史开奖数据"""
        # 这里简化处理,实际可能需要调用不同的API
        data = self.fetch_history(page=1, page_size=100)
        items = data['items']
        
        # 根据条件筛选
        if draw_num:
            items = [item for item in items if draw_num in item['draw_num']]
        if draw_date:
            items = [item for item in items if draw_date in item['draw_date']]
            
        return {
            'items': items,
            'total_pages': 1
        }
