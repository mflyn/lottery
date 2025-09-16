#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API数据解析器
处理不同API源的数据格式解析
"""

import re
import logging
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

class APIParser:
    """API数据解析器基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, data: Any, lottery_type: str) -> List[Dict]:
        """解析API数据
        
        Args:
            data: API返回的原始数据
            lottery_type: 彩票类型
            
        Returns:
            解析后的数据列表
        """
        raise NotImplementedError

class SportteryParser(APIParser):
    """体彩网API解析器"""
    
    def parse(self, data: Any, lottery_type: str) -> List[Dict]:
        """解析体彩网API数据"""
        try:
            if not isinstance(data, dict):
                return []
            
            if not data.get('success') or 'value' not in data:
                self.logger.warning(f"体彩网API返回失败: {data.get('message', '未知错误')}")
                return []
            
            items = data['value'].get('list', [])
            parsed_data = []
            
            for item in items:
                try:
                    if lottery_type == 'dlt':
                        parsed_item = self._parse_dlt_item(item)
                    elif lottery_type == 'ssq':
                        parsed_item = self._parse_ssq_item(item)
                    else:
                        continue
                    
                    if parsed_item:
                        parsed_data.append(parsed_item)
                        
                except Exception as e:
                    self.logger.error(f"解析体彩网单条数据失败: {e}")
                    continue
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析体彩网API数据失败: {e}")
            return []
    
    def _parse_dlt_item(self, item: Dict) -> Optional[Dict]:
        """解析大乐透数据项"""
        draw_num = item.get('lotteryDrawNum')
        draw_date = item.get('lotteryDrawTime', '').split()[0]
        numbers_str = item.get('lotteryDrawResult', '')
        
        if not all([draw_num, draw_date, numbers_str]):
            return None
        
        numbers_list = numbers_str.split()
        if len(numbers_list) < 7:
            return None
        
        front_numbers = sorted([int(n) for n in numbers_list[:5]])
        back_numbers = sorted([int(n) for n in numbers_list[5:7]])
        
        return {
            'draw_num': draw_num,
            'draw_date': draw_date,
            'front_numbers': front_numbers,
            'back_numbers': back_numbers,
            'prize_pool': item.get('poolBalanceAfterdraw', '0'),
            'sales': item.get('totalSaleAmount', '0'),
            'first_prize_num': item.get('firstPrizeNum', '0'),
            'first_prize_amount': item.get('firstPrizeAmount', '0')
        }
    
    def _parse_ssq_item(self, item: Dict) -> Optional[Dict]:
        """解析双色球数据项"""
        # 体彩网通常不提供双色球数据，这里预留接口
        return None

class WanParser(APIParser):
    """500彩票网API解析器"""
    
    def parse(self, data: Any, lottery_type: str) -> List[Dict]:
        """解析500彩票网数据"""
        try:
            if isinstance(data, str):
                # HTML格式数据
                return self._parse_html_data(data, lottery_type)
            elif isinstance(data, dict):
                # JSON格式数据
                return self._parse_json_data(data, lottery_type)
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"解析500彩票网数据失败: {e}")
            return []
    
    def _parse_html_data(self, html: str, lottery_type: str) -> List[Dict]:
        """解析HTML格式数据"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            parsed_data = []
            
            if lottery_type == 'dlt':
                # 查找大乐透数据表格
                table = soup.find('table', {'class': 'kj_tablelist02'})
                if not table:
                    return []
                
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 10:
                        continue
                    
                    try:
                        draw_num = cells[0].get_text().strip()
                        draw_date = cells[1].get_text().strip()
                        
                        # 提取号码
                        front_numbers = []
                        back_numbers = []
                        
                        # 前区号码通常在第2-6列
                        for i in range(2, 7):
                            num = int(cells[i].get_text().strip())
                            front_numbers.append(num)
                        
                        # 后区号码通常在第7-8列
                        for i in range(7, 9):
                            num = int(cells[i].get_text().strip())
                            back_numbers.append(num)
                        
                        parsed_data.append({
                            'draw_num': draw_num,
                            'draw_date': draw_date,
                            'front_numbers': sorted(front_numbers),
                            'back_numbers': sorted(back_numbers),
                            'prize_pool': '0',
                            'sales': '0',
                            'first_prize_num': '0',
                            'first_prize_amount': '0'
                        })
                        
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"解析500彩票网行数据失败: {e}")
                        continue
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析500彩票网HTML数据失败: {e}")
            return []
    
    def _parse_json_data(self, data: Dict, lottery_type: str) -> List[Dict]:
        """解析JSON格式数据"""
        # 500彩票网的JSON格式解析
        return []

class SinaParser(APIParser):
    """新浪彩票API解析器"""
    
    def parse(self, data: Any, lottery_type: str) -> List[Dict]:
        """解析新浪彩票数据"""
        try:
            if not isinstance(data, dict):
                return []
            
            if data.get('code') != 0:
                self.logger.warning(f"新浪API返回错误: {data.get('msg', '未知错误')}")
                return []
            
            items = data.get('data', {}).get('list', [])
            parsed_data = []
            
            for item in items:
                try:
                    if lottery_type == 'dlt':
                        parsed_item = self._parse_dlt_item(item)
                    elif lottery_type == 'ssq':
                        parsed_item = self._parse_ssq_item(item)
                    else:
                        continue
                    
                    if parsed_item:
                        parsed_data.append(parsed_item)
                        
                except Exception as e:
                    self.logger.error(f"解析新浪单条数据失败: {e}")
                    continue
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析新浪API数据失败: {e}")
            return []
    
    def _parse_dlt_item(self, item: Dict) -> Optional[Dict]:
        """解析大乐透数据项"""
        draw_num = item.get('issue')
        draw_date = item.get('date')
        numbers = item.get('numbers', [])
        
        if not all([draw_num, draw_date, numbers]) or len(numbers) < 7:
            return None
        
        front_numbers = sorted([int(n) for n in numbers[:5]])
        back_numbers = sorted([int(n) for n in numbers[5:7]])
        
        return {
            'draw_num': draw_num,
            'draw_date': draw_date,
            'front_numbers': front_numbers,
            'back_numbers': back_numbers,
            'prize_pool': item.get('pool', '0'),
            'sales': item.get('sales', '0'),
            'first_prize_num': '0',
            'first_prize_amount': '0'
        }
    
    def _parse_ssq_item(self, item: Dict) -> Optional[Dict]:
        """解析双色球数据项"""
        draw_num = item.get('issue')
        draw_date = item.get('date')
        numbers = item.get('numbers', [])
        
        if not all([draw_num, draw_date, numbers]) or len(numbers) < 7:
            return None
        
        red_numbers = sorted([int(n) for n in numbers[:6]])
        blue_number = int(numbers[6])
        
        return {
            'draw_num': draw_num,
            'draw_date': draw_date,
            'red_numbers': red_numbers,
            'blue_number': blue_number,
            'prize_pool': item.get('pool', '0'),
            'sales': item.get('sales', '0'),
            'first_prize_num': '0',
            'first_prize_amount': '0'
        }

class NeteaseParser(APIParser):
    """网易彩票API解析器"""
    
    def parse(self, data: Any, lottery_type: str) -> List[Dict]:
        """解析网易彩票数据"""
        try:
            if isinstance(data, str):
                # HTML格式数据
                return self._parse_html_data(data, lottery_type)
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"解析网易彩票数据失败: {e}")
            return []
    
    def _parse_html_data(self, html: str, lottery_type: str) -> List[Dict]:
        """解析HTML格式数据"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            parsed_data = []
            
            if lottery_type == 'dlt':
                # 查找大乐透数据
                # 网易彩票的具体HTML结构需要根据实际页面调整
                table = soup.find('table', {'class': 'award_table'})
                if not table:
                    return []
                
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 8:
                        continue
                    
                    try:
                        draw_num = cells[0].get_text().strip()
                        draw_date = cells[1].get_text().strip()
                        
                        # 提取号码（具体位置需要根据实际页面调整）
                        numbers_text = cells[2].get_text().strip()
                        numbers = re.findall(r'\d+', numbers_text)
                        
                        if len(numbers) >= 7:
                            front_numbers = sorted([int(n) for n in numbers[:5]])
                            back_numbers = sorted([int(n) for n in numbers[5:7]])
                            
                            parsed_data.append({
                                'draw_num': draw_num,
                                'draw_date': draw_date,
                                'front_numbers': front_numbers,
                                'back_numbers': back_numbers,
                                'prize_pool': '0',
                                'sales': '0',
                                'first_prize_num': '0',
                                'first_prize_amount': '0'
                            })
                        
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"解析网易彩票行数据失败: {e}")
                        continue
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析网易彩票HTML数据失败: {e}")
            return []

class CWLParser(APIParser):
    """福彩网API解析器"""
    
    def parse(self, data: Any, lottery_type: str) -> List[Dict]:
        """解析福彩网数据"""
        try:
            if not isinstance(data, dict):
                return []
            
            if data.get('state') != 0:
                self.logger.warning(f"福彩网API返回失败: {data.get('message', '未知错误')}")
                return []
            
            items = data.get('result', [])
            parsed_data = []
            
            for item in items:
                try:
                    if lottery_type == 'ssq':
                        parsed_item = self._parse_ssq_item(item)
                    else:
                        continue
                    
                    if parsed_item:
                        parsed_data.append(parsed_item)
                        
                except Exception as e:
                    self.logger.error(f"解析福彩网单条数据失败: {e}")
                    continue
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析福彩网API数据失败: {e}")
            return []
    
    def _parse_ssq_item(self, item: Dict) -> Optional[Dict]:
        """解析双色球数据项"""
        draw_num = item.get('code')
        draw_date_raw = item.get('date', '')
        draw_date = draw_date_raw.split('(')[0] if '(' in draw_date_raw else draw_date_raw
        red_str = item.get('red', '')
        blue_str = item.get('blue', '')
        
        if not all([draw_num, draw_date, red_str, blue_str]):
            return None
        
        try:
            red_numbers = sorted([int(n) for n in red_str.split(',')])
            blue_number = int(blue_str)
            
            if len(red_numbers) != 6:
                return None
            
            return {
                'draw_num': draw_num,
                'draw_date': draw_date,
                'red_numbers': red_numbers,
                'blue_number': blue_number,
                'prize_pool': item.get('poolmoney', '0'),
                'sales': item.get('sales', '0'),
                'first_prize_num': item.get('onebonus', '0'),
                'first_prize_amount': item.get('onemoney', '0')
            }
            
        except (ValueError, TypeError):
            return None

class SimpleAPIParser(APIParser):
    """通用简单API解析器"""
    
    def parse(self, data: Any, lottery_type: str) -> List[Dict]:
        """解析简单API数据"""
        try:
            if isinstance(data, str):
                # 尝试解析HTML内容
                return self._parse_html_data(data, lottery_type)
            elif isinstance(data, dict):
                # 尝试解析JSON数据
                return self._parse_json_data(data, lottery_type)
            else:
                self.logger.warning(f"不支持的数据格式: {type(data)}")
                return []
        except Exception as e:
            self.logger.error(f"解析简单API数据失败: {e}")
            return []
    
    def _parse_html_data(self, html_content: str, lottery_type: str) -> List[Dict]:
        """解析HTML数据"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            if lottery_type == 'dlt':
                # 解析大乐透HTML数据
                # 查找表格行
                rows = soup.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        try:
                            # 尝试提取期号、日期、号码
                            date_text = cells[0].get_text(strip=True)
                            issue_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            numbers_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            
                            # 简单的号码格式检查
                            if len(numbers_text) >= 10 and any(char.isdigit() for char in numbers_text):
                                # 尝试解析号码
                                numbers = re.findall(r'\d+', numbers_text)
                                if len(numbers) >= 7:
                                    front_numbers = sorted([int(n) for n in numbers[:5]])
                                    back_numbers = sorted([int(n) for n in numbers[5:7]])
                                    
                                    results.append({
                                        'draw_num': issue_text,
                                        'draw_date': date_text,
                                        'front_numbers': front_numbers,
                                        'back_numbers': back_numbers,
                                        'prize_pool': '0',
                                        'sales': '0',
                                        'first_prize_num': '0',
                                        'first_prize_amount': '0'
                                    })
                        except (ValueError, IndexError):
                            continue
            
            return results
        except Exception as e:
            self.logger.error(f"解析HTML数据失败: {e}")
            return []
    
    def _parse_json_data(self, json_data: dict, lottery_type: str) -> List[Dict]:
        """解析JSON数据"""
        try:
            results = []
            
            # 尝试不同的JSON结构
            data_list = []
            if 'data' in json_data:
                data_list = json_data['data']
            elif 'result' in json_data:
                data_list = json_data['result']
            elif 'list' in json_data:
                data_list = json_data['list']
            elif isinstance(json_data, list):
                data_list = json_data
            
            if not isinstance(data_list, list):
                return []
            
            for item in data_list:
                if not isinstance(item, dict):
                    continue
                
                try:
                    if lottery_type == 'dlt':
                        # 尝试提取大乐透数据
                        draw_num = item.get('issue', item.get('period', item.get('draw_num', '')))
                        draw_date = item.get('date', item.get('draw_date', ''))
                        
                        # 尝试不同的号码字段
                        numbers_str = item.get('numbers', item.get('result', item.get('winning_numbers', '')))
                        
                        if numbers_str and draw_num:
                            numbers = re.findall(r'\d+', str(numbers_str))
                            if len(numbers) >= 7:
                                front_numbers = sorted([int(n) for n in numbers[:5]])
                                back_numbers = sorted([int(n) for n in numbers[5:7]])
                                
                                results.append({
                                    'draw_num': str(draw_num),
                                    'draw_date': str(draw_date),
                                    'front_numbers': front_numbers,
                                    'back_numbers': back_numbers,
                                    'prize_pool': str(item.get('prize_pool', '0')),
                                    'sales': str(item.get('sales', '0')),
                                    'first_prize_num': str(item.get('first_prize_num', '0')),
                                    'first_prize_amount': str(item.get('first_prize_amount', '0'))
                                })
                except (ValueError, KeyError):
                    continue
            
            return results
        except Exception as e:
            self.logger.error(f"解析JSON数据失败: {e}")
            return []

# 解析器工厂
def get_parser(api_type: str) -> APIParser:
    """获取对应的API解析器
    
    Args:
        api_type: API类型
        
    Returns:
        对应的解析器实例
    """
    parsers = {
        'sporttery': SportteryParser,
        '500wan': WanParser,
        'sina': SinaParser,
        'netease': NeteaseParser,
        'cwl': CWLParser,
        'simple': SimpleAPIParser
    }
    
    parser_class = parsers.get(api_type, SimpleAPIParser)  # 默认使用SimpleAPIParser
    return parser_class() 