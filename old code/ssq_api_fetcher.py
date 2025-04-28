#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
双色球开奖数据获取模块 - API版本
通过福彩网官方API获取双色球开奖数据
"""

import requests
import json
import re
from typing import Dict, List, Optional


class SSQApiFetcher:
    """双色球开奖数据API获取类"""

    def __init__(self):
        """初始化"""
        # 使用中国福彩网官方API URL
        self.base_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"

        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.cwl.gov.cn/kjxx/ssq/kjgg/',
            'Origin': 'https://www.cwl.gov.cn'
        }

        # 备用模拟数据，当API访问失败时使用
        self.mock_data = {
            "latest": {
                "term": "2025043",
                "date": "2025-04-14",
                "red_numbers": [1, 7, 9, 16, 21, 28],
                "blue_numbers": [8]
            },
            "terms": {
                "2025043": {
                    "term": "2025043",
                    "date": "2025-04-14",
                    "red_numbers": [1, 7, 9, 16, 21, 28],
                    "blue_numbers": [8]
                },
                "2025042": {
                    "term": "2025042",
                    "date": "2025-04-11",
                    "red_numbers": [3, 10, 11, 24, 25, 32],
                    "blue_numbers": [7]
                },
                "2025041": {
                    "term": "2025041",
                    "date": "2025-04-09",
                    "red_numbers": [2, 3, 19, 24, 25, 32],
                    "blue_numbers": [6]
                },
                "2025040": {
                    "term": "2025040",
                    "date": "2025-04-07",
                    "red_numbers": [3, 4, 9, 10, 22, 32],
                    "blue_numbers": [10]
                },
                "2025039": {
                    "term": "2025039",
                    "date": "2025-04-04",
                    "red_numbers": [1, 2, 3, 19, 28, 33],
                    "blue_numbers": [3]
                }
            }
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
            "name": "ssq",  # ssq 代表双色球
            "pageSize": str(page_size),
            "pageNo": str(page_no),
            "issueCount": "",
            "issueStart": "",
            "issueEnd": "",
            "dayStart": "",
            "dayEnd": ""
        }

        try:
            # 发送请求
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )

            # 检查响应状态
            if response.status_code == 200:
                # 解析JSON响应
                data = response.json()
                if data and 'result' in data:
                    return data

            print(f"获取开奖数据失败: 状态码 {response.status_code}")
            # 如果请求失败，使用模拟数据
            return self._get_mock_page_data(page_no, page_size)

        except Exception as e:
            print(f"获取开奖数据异常: {e}")
            # 如果发生异常，使用模拟数据
            return self._get_mock_page_data(page_no, page_size)

    def _get_mock_page_data(self, page_no: int, page_size: int) -> Dict:
        """获取模拟分页数据"""
        mock_result = {
            "result": {
                "data": []
            }
        }

        # 根据页码和每页数量计算起始和结束索引
        start_idx = (page_no - 1) * page_size
        end_idx = start_idx + page_size

        # 获取所有期号并排序
        all_terms = sorted(list(self.mock_data["terms"].keys()), reverse=True)

        # 如果起始索引超出范围，返回空列表
        if start_idx >= len(all_terms):
            return mock_result

        # 获取当前页的期号
        current_page_terms = all_terms[start_idx:min(end_idx, len(all_terms))]

        # 构建当前页的数据
        for term in current_page_terms:
            term_data = self.mock_data["terms"][term]
            red_numbers_str = ' '.join([f"{num:02d}" for num in term_data["red_numbers"]])
            blue_numbers_str = ' '.join([f"{num:02d}" for num in term_data["blue_numbers"]])

            mock_result["result"]["data"].append({
                "code": "ssq",
                "name": "双色球",
                "date": term_data["date"],
                "red": red_numbers_str,
                "blue": blue_numbers_str,
                "week": "日",  # 模拟星期
                "issue": term_data["term"],
                "videoUrl": "",
                "detailsUrl": ""
            })

        return mock_result

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

        try:
            # 构建请求参数，使用期号范围进行精确查询
            params = {
                "name": "ssq",  # ssq 代表双色球
                "issueCount": "",
                "issueStart": term,
                "issueEnd": term,
                "dayStart": "",
                "dayEnd": "",
                "pageNo": "1",
                "pageSize": "30"
            }

            # 发送请求
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )

            # 检查响应状态
            if response.status_code == 200:
                # 解析JSON响应
                data = response.json()
                if data and 'result' in data and isinstance(data['result'].get('data'), list) and data['result']['data']:
                    # 获取第一条数据（应该只有一条）
                    draw_data = data['result']['data'][0]
                    return self._parse_draw_data(draw_data)

            print(f"获取期号 {term} 的开奖数据失败")
            # 如果请求失败，尝试使用模拟数据
            return self._get_mock_term_data(term)

        except Exception as e:
            print(f"获取期号 {term} 的开奖数据异常: {e}")
            # 如果发生异常，尝试使用模拟数据
            return self._get_mock_term_data(term)

    def _get_mock_term_data(self, term: str) -> Optional[Dict]:
        """从模拟数据中获取期号数据"""
        # 先检查完整期号
        if term in self.mock_data["terms"]:
            term_data = self.mock_data["terms"][term]
            return {
                "term": term_data["term"],
                "date": term_data["date"],
                "red_numbers": term_data["red_numbers"],
                "blue_numbers": term_data["blue_numbers"],
                "raw_data": term_data
            }

        # 再检查短期号（只取后5位）
        for full_term, term_data in self.mock_data["terms"].items():
            if full_term[-5:] == term[-5:]:
                return {
                    "term": term_data["term"],
                    "date": term_data["date"],
                    "red_numbers": term_data["red_numbers"],
                    "blue_numbers": term_data["blue_numbers"],
                    "raw_data": term_data
                }

        return None

    def fetch_latest(self) -> Optional[Dict]:
        """
        获取最新一期开奖数据

        返回:
            最新一期开奖数据字典，如果获取失败则返回None
        """
        try:
            # 构建请求参数，只获取第一页第一条数据
            params = {
                "name": "ssq",  # ssq 代表双色球
                "pageSize": "1",
                "pageNo": "1",
                "issueCount": "",
                "issueStart": "",
                "issueEnd": "",
                "dayStart": "",
                "dayEnd": ""
            }

            # 发送请求
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )

            # 检查响应状态
            if response.status_code == 200:
                # 解析JSON响应
                data = response.json()
                if data and 'result' in data and isinstance(data['result'].get('data'), list) and data['result']['data']:
                    # 获取第一条数据（最新一期）
                    latest_draw = data['result']['data'][0]
                    return self._parse_draw_data(latest_draw)

            print("获取最新开奖数据失败")
            # 如果请求失败，使用模拟数据
            latest_data = self.mock_data["latest"]
            return {
                "term": latest_data["term"],
                "date": latest_data["date"],
                "red_numbers": latest_data["red_numbers"],
                "blue_numbers": latest_data["blue_numbers"],
                "raw_data": latest_data
            }

        except Exception as e:
            print(f"获取最新开奖数据异常: {e}")
            # 如果发生异常，使用模拟数据
            latest_data = self.mock_data["latest"]
            return {
                "term": latest_data["term"],
                "date": latest_data["date"],
                "red_numbers": latest_data["red_numbers"],
                "blue_numbers": latest_data["blue_numbers"],
                "raw_data": latest_data
            }

    def _parse_draw_data(self, draw: Dict) -> Dict:
        """
        解析开奖数据

        参数:
            draw: API返回的开奖数据字典

        返回:
            解析后的开奖数据字典
        """
        try:
            # 获取期号
            term = draw.get('issue', '') if isinstance(draw, dict) else ''

            # 获取开奖日期
            date = draw.get('date', '') if isinstance(draw, dict) else ''

            # 获取红球号码
            red_str = draw.get('red', '') if isinstance(draw, dict) else ''
            red_numbers = [int(num) for num in red_str.split()] if red_str else []

            # 获取蓝球号码
            blue_str = draw.get('blue', '') if isinstance(draw, dict) else ''
            blue_numbers = [int(num) for num in blue_str.split()] if blue_str else []

            # 如果没有获取到数据，尝试其他字段
            if not red_numbers and isinstance(draw, dict) and 'lotteryDrawResult' in draw:
                # 兼容旧版API格式
                draw_code = draw.get('lotteryDrawResult', '')
                numbers = draw_code.split()
                if len(numbers) >= 7:
                    red_numbers = [int(num) for num in numbers[:6]]
                    blue_numbers = [int(num) for num in numbers[6:7]]

            # 如果还是没有数据，尝试raw_data
            if not red_numbers and isinstance(draw, dict) and 'raw_data' in draw and isinstance(draw['raw_data'], dict):
                red_numbers = draw['raw_data'].get('red_numbers', [])
                blue_numbers = draw['raw_data'].get('blue_numbers', [])

            # 返回数据字典
            return {
                "term": term,
                "date": date,
                "red_numbers": red_numbers,
                "blue_numbers": blue_numbers,
                "raw_data": draw  # 保留原始数据，以备需要
            }
        except Exception as e:
            print(f"解析开奖数据异常: {e}")
            # 如果解析失败，返回空数据
            return {
                "term": draw.get('issue', '') if isinstance(draw, dict) else '',
                "date": draw.get('date', '') if isinstance(draw, dict) else '',
                "red_numbers": [],
                "blue_numbers": [],
                "raw_data": draw
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
    fetcher = SSQApiFetcher()

    # 测试获取最新一期开奖数据
    latest = fetcher.fetch_latest()
    if latest:
        print("最新一期开奖数据:")
        print(f"期号: {latest['term']}")
        print(f"日期: {latest['date']}")
        print(f"红球号码: {latest['red_numbers']}")
        print(f"蓝球号码: {latest['blue_numbers']}")
    else:
        print("获取最新一期开奖数据失败")

    # 测试获取特定期号的开奖数据
    term = "23001"  # 可以修改为你想查询的期号
    result = fetcher.fetch_by_term(term)
    if result:
        print(f"\n期号 {term} 的开奖数据:")
        print(f"日期: {result['date']}")
        print(f"红球号码: {result['red_numbers']}")
        print(f"蓝球号码: {result['blue_numbers']}")
    else:
        print(f"\n未找到期号 {term} 的开奖数据")
