#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大乐透开奖数据获取模块
从500彩票网获取大乐透开奖数据
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Tuple, Optional


class DLTDataFetcher:
    """大乐透开奖数据获取类"""
    
    def __init__(self):
        """初始化"""
        # 500彩票网大乐透历史开奖数据URL
        self.base_url = "http://datachart.500.com/dlt/history/newinc/history.php"
        
        # 请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
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
        
        # 构建请求URL
        url = f"{self.base_url}?start={term}&end={term}"
        
        try:
            # 发送请求
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'  # 确保编码正确
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找开奖数据表格
            tbody = soup.find('tbody', id="tdata")
            if not tbody:
                return None
            
            # 查找对应期号的行
            rows = tbody.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if not cells:
                    continue
                
                # 获取期号
                row_term = cells[0].text.strip()
                if row_term == term or row_term == term[-5:]:  # 兼容不同期号格式
                    # 提取开奖数据
                    return self._parse_row_data(cells)
            
            return None
            
        except Exception as e:
            print(f"获取开奖数据失败: {e}")
            return None
    
    def fetch_latest(self) -> Optional[Dict]:
        """
        获取最新一期开奖数据
        
        返回:
            最新一期开奖数据字典，如果获取失败则返回None
        """
        try:
            # 发送请求
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'  # 确保编码正确
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找开奖数据表格
            tbody = soup.find('tbody', id="tdata")
            if not tbody:
                return None
            
            # 获取第一行（最新一期）
            first_row = tbody.find('tr')
            if not first_row:
                return None
            
            cells = first_row.find_all('td')
            if not cells:
                return None
            
            # 提取开奖数据
            return self._parse_row_data(cells)
            
        except Exception as e:
            print(f"获取最新开奖数据失败: {e}")
            return None
    
    def _parse_row_data(self, cells) -> Dict:
        """
        解析行数据
        
        参数:
            cells: 表格行中的单元格列表
        
        返回:
            开奖数据字典
        """
        # 获取期号
        term = cells[0].text.strip()
        
        # 获取开奖日期
        date = cells[1].text.strip()
        
        # 获取前区号码
        front_numbers = []
        for i in range(2, 7):
            front_numbers.append(int(cells[i].text.strip()))
        
        # 获取后区号码
        back_numbers = []
        for i in range(7, 9):
            back_numbers.append(int(cells[i].text.strip()))
        
        # 返回数据字典
        return {
            "term": term,
            "date": date,
            "front_numbers": front_numbers,
            "back_numbers": back_numbers
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
        term = re.sub(r'\D', '', term)
        
        # 检查期号长度
        if len(term) == 5:  # 短格式，如"21001"
            return term
        elif len(term) == 7:  # 长格式，如"2021001"
            return term
        else:
            return None


# 测试代码
if __name__ == "__main__":
    fetcher = DLTDataFetcher()
    
    # 测试获取特定期号的开奖数据
    term = "21001"
    result = fetcher.fetch_by_term(term)
    if result:
        print(f"期号: {result['term']}")
        print(f"日期: {result['date']}")
        print(f"前区号码: {result['front_numbers']}")
        print(f"后区号码: {result['back_numbers']}")
    else:
        print(f"未找到期号 {term} 的开奖数据")
    
    # 测试获取最新一期开奖数据
    latest = fetcher.fetch_latest()
    if latest:
        print("\n最新一期:")
        print(f"期号: {latest['term']}")
        print(f"日期: {latest['date']}")
        print(f"前区号码: {latest['front_numbers']}")
        print(f"后区号码: {latest['back_numbers']}")
    else:
        print("获取最新一期开奖数据失败")
