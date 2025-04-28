#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大乐透开奖数据获取模块 - API版本
通过体彩API获取大乐透开奖数据
"""

import requests
import json
from typing import Dict, List, Optional


class DLTApiFetcher:
    """大乐透开奖数据API获取类"""
    
    def __init__(self):
        """初始化"""
        # 体彩API URL
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.sporttery.cn/',
            'Origin': 'https://www.sporttery.cn'
        }
    
    def fetch_by_page(self, page_no: int = 1, page_size: int = 30) -> Optional[Dict]:
        """
        获取指定页码的开奖数据
        
        参数:
            page_no: 页码，默认为1
            page_size: 每页数量，默认为30
        
        返回:
            开奖数据字典，如果获取失败则返回None
        """
        # 构建请求参数
        params = {
            "gameNo": "85",  # 85 代表大乐透
            "provinceId": "0",
            "pageSize": str(page_size),
            "isVerify": "1",
            "pageNo": str(page_no)
        }
        
        try:
            # 发送请求
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            # 解析JSON响应
            data = response.json()
            
            # 检查响应状态
            if data.get('success') and data.get('value') and data.get('value').get('list'):
                return data
            else:
                print(f"获取开奖数据失败: {data.get('message', '未知错误')}")
                return None
            
        except Exception as e:
            print(f"获取开奖数据异常: {e}")
            return None
    
    def fetch_by_term(self, term: str) -> Optional[Dict]:
        """
        根据期号获取开奖数据
        
        参数:
            term: 期号，格式如"21001"或"2021001"
        
        返回:
            开奖数据字典，如果未找到则返回None
        """
        # 标准化期号格式
        term = self._normalize_term(term)
        if not term:
            return None
        
        # 获取第一页数据
        data = self.fetch_by_page(page_no=1, page_size=30)
        if not data:
            return None
        
        # 在第一页中查找
        draw_list = data.get('value', {}).get('list', [])
        for draw in draw_list:
            if draw.get('lotteryDrawNum') == term or draw.get('lotteryDrawNum') == term[-5:]:
                return self._parse_draw_data(draw)
        
        # 如果第一页没有找到，尝试获取更多页
        total_page = data.get('value', {}).get('pages', 1)
        for page in range(2, min(total_page + 1, 10)):  # 最多查找10页
            data = self.fetch_by_page(page_no=page, page_size=30)
            if not data:
                continue
            
            draw_list = data.get('value', {}).get('list', [])
            for draw in draw_list:
                if draw.get('lotteryDrawNum') == term or draw.get('lotteryDrawNum') == term[-5:]:
                    return self._parse_draw_data(draw)
        
        return None
    
    def fetch_latest(self) -> Optional[Dict]:
        """
        获取最新一期开奖数据
        
        返回:
            最新一期开奖数据字典，如果获取失败则返回None
        """
        # 获取第一页第一条数据
        data = self.fetch_by_page(page_no=1, page_size=1)
        if not data or not data.get('value', {}).get('list', []):
            return None
        
        # 解析最新一期数据
        latest_draw = data.get('value', {}).get('list', [])[0]
        return self._parse_draw_data(latest_draw)
    
    def _parse_draw_data(self, draw: Dict) -> Dict:
        """
        解析开奖数据
        
        参数:
            draw: API返回的开奖数据字典
        
        返回:
            解析后的开奖数据字典
        """
        # 获取期号
        term = draw.get('lotteryDrawNum', '')
        
        # 获取开奖日期
        date = draw.get('lotteryDrawTime', '')
        
        # 获取开奖号码
        draw_code = draw.get('lotteryDrawResult', '')
        
        # 解析开奖号码
        numbers = draw_code.split()
        if len(numbers) >= 7:
            front_numbers = [int(num) for num in numbers[:5]]
            back_numbers = [int(num) for num in numbers[5:7]]
        else:
            front_numbers = []
            back_numbers = []
        
        # 返回数据字典
        return {
            "term": term,
            "date": date,
            "front_numbers": front_numbers,
            "back_numbers": back_numbers,
            "raw_data": draw  # 保留原始数据，以备需要
        }
    
    def _normalize_term(self, term: str) -> Optional[str]:
        """
        标准化期号格式
        
        参数:
            term: 期号，格式如"21001"或"2021001"
        
        返回:
            标准化后的期号，如果格式不正确则返回None
        """
        # 移除所有非数字字符
        term = ''.join(filter(str.isdigit, term))
        
        # 检查期号长度
        if len(term) == 5:  # 短格式，如"21001"
            return term
        elif len(term) == 7:  # 长格式，如"2021001"
            return term
        else:
            return None


# 测试代码
if __name__ == "__main__":
    fetcher = DLTApiFetcher()
    
    # 测试获取最新一期开奖数据
    latest = fetcher.fetch_latest()
    if latest:
        print("最新一期开奖数据:")
        print(f"期号: {latest['term']}")
        print(f"日期: {latest['date']}")
        print(f"前区号码: {latest['front_numbers']}")
        print(f"后区号码: {latest['back_numbers']}")
    else:
        print("获取最新一期开奖数据失败")
    
    # 测试获取特定期号的开奖数据
    term = "23001"  # 可以修改为你想查询的期号
    result = fetcher.fetch_by_term(term)
    if result:
        print(f"\n期号 {term} 的开奖数据:")
        print(f"日期: {result['date']}")
        print(f"前区号码: {result['front_numbers']}")
        print(f"后区号码: {result['back_numbers']}")
    else:
        print(f"\n未找到期号 {term} 的开奖数据")
