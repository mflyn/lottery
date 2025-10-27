#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
网络客户端
统一处理网络请求，包含重试机制和错误处理
"""

import requests
import logging
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config_manager import get_config_manager

class NetworkError(Exception):
    """网络错误基类"""
    pass

class TimeoutError(NetworkError):
    """超时错误"""
    pass

class ConnectionError(NetworkError):
    """连接错误"""
    pass

class HTTPError(NetworkError):
    """HTTP错误"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code

class NetworkClient:
    """网络客户端"""
    
    def __init__(self):
        """初始化网络客户端"""
        self.config_manager = get_config_manager()
        self.logger = logging.getLogger(__name__)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建配置好的会话"""
        session = requests.Session()
        
        # 获取网络配置
        network_config = self.config_manager.get_network_config()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=network_config.get('max_retry', 3),
            backoff_factor=network_config.get('retry_delay', 1),
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认请求头
        session.headers.update({
            'User-Agent': network_config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[float] = None,
            stream: bool = False) -> requests.Response:
        """发送GET请求

        Args:
            url: 请求URL
            params: 请求参数
            headers: 请求头
            timeout: 超时时间
            stream: 是否流式传输

        Returns:
            响应对象

        Raises:
            NetworkError: 网络相关错误
        """
        return self._request('GET', url, params=params, headers=headers, timeout=timeout, stream=stream)
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None,
             json: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None,
             timeout: Optional[float] = None) -> requests.Response:
        """发送POST请求
        
        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 请求头
            timeout: 超时时间
            
        Returns:
            响应对象
            
        Raises:
            NetworkError: 网络相关错误
        """
        return self._request('POST', url, data=data, json=json, 
                           headers=headers, timeout=timeout)
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            响应对象
            
        Raises:
            NetworkError: 网络相关错误
        """
        # 获取超时配置
        if 'timeout' not in kwargs or kwargs['timeout'] is None:
            kwargs['timeout'] = self.config_manager.get('network.timeout', 30)
        
        # 合并请求头
        if 'headers' in kwargs and kwargs['headers']:
            headers = self.session.headers.copy()
            headers.update(kwargs['headers'])
            kwargs['headers'] = headers
        
        # 设置SSL验证
        kwargs['verify'] = self.config_manager.get('network.verify_ssl', True)
        
        try:
            self.logger.debug(f"发送 {method} 请求到: {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            self.logger.debug(f"请求成功: {response.status_code}")
            return response
            
        except requests.exceptions.Timeout as e:
            error_msg = f"请求超时: {url}"
            self.logger.error(error_msg)
            raise TimeoutError(error_msg) from e
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"连接错误: {url}"
            self.logger.error(error_msg)
            raise ConnectionError(error_msg) from e
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {url}"
            self.logger.error(error_msg)
            raise HTTPError(error_msg, e.response.status_code) from e
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {url} - {str(e)}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg) from e
    
    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None,
                 timeout: Optional[float] = None) -> Dict[str, Any]:
        """发送GET请求并返回JSON数据
        
        Args:
            url: 请求URL
            params: 请求参数
            headers: 请求头
            timeout: 超时时间
            
        Returns:
            JSON数据字典
            
        Raises:
            NetworkError: 网络相关错误
        """
        response = self.get(url, params=params, headers=headers, timeout=timeout)
        
        try:
            return response.json()
        except ValueError as e:
            error_msg = f"JSON解析失败: {url}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg) from e
    
    def download_file(self, url: str, file_path: str,
                      chunk_size: int = 8192,
                      progress_callback: Optional[callable] = None) -> bool:
        """下载文件

        Args:
            url: 文件URL
            file_path: 保存路径
            chunk_size: 块大小
            progress_callback: 进度回调函数

        Returns:
            是否下载成功

        Raises:
            TimeoutError: 下载超时
            ConnectionError: 连接失败
            HTTPError: HTTP错误
            NetworkError: 其他网络错误
        """
        try:
            self.logger.info(f"开始下载文件: {url}")
            response = self.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # 确保目标目录存在
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # 使用临时文件，下载完成后再重命名
            temp_file = file_path_obj.with_suffix(file_path_obj.suffix + '.tmp')

            try:
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if progress_callback and total_size > 0:
                                progress = downloaded / total_size
                                progress_callback(progress)

                # 下载完成，重命名临时文件
                if file_path_obj.exists():
                    file_path_obj.unlink()
                temp_file.rename(file_path_obj)

                self.logger.info(f"文件下载成功: {file_path} ({downloaded} 字节)")
                return True

            except IOError as e:
                # 文件写入错误
                self.logger.error(f"文件写入失败: {file_path} - {e}")
                if temp_file.exists():
                    temp_file.unlink()
                raise NetworkError(f"文件写入失败: {e}") from e

        except requests.exceptions.Timeout as e:
            self.logger.error(f"下载超时: {url} - {e}")
            raise TimeoutError(f"下载超时: {url}") from e

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"连接失败: {url} - {e}")
            raise ConnectionError(f"连接失败: {url}") from e

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            self.logger.error(f"HTTP错误: {url} - 状态码: {status_code} - {e}")
            raise HTTPError(f"HTTP错误: {url}", status_code) from e

        except NetworkError:
            # 重新抛出我们自己的网络错误
            raise

        except Exception as e:
            self.logger.error(f"文件下载失败: {url} - {str(e)}")
            raise NetworkError(f"文件下载失败: {url} - {str(e)}") from e
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# 全局网络客户端实例
_network_client = None

def get_network_client() -> NetworkClient:
    """获取全局网络客户端实例"""
    global _network_client
    if _network_client is None:
        _network_client = NetworkClient()
    return _network_client 