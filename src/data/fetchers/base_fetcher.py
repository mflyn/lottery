from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import sqlite3
from src.utils.logger import Logger

class BaseLotteryFetcher(ABC):
    """彩票数据获取器基类"""
    
    def __init__(self):
        self.logger = Logger()
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = "data/lottery.db"
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lottery_data (
                lottery_type TEXT,
                draw_date TEXT,
                draw_number TEXT,
                numbers TEXT,
                prize_info TEXT,
                updated_at TEXT,
                PRIMARY KEY (lottery_type, draw_number)
            )
        """)
        
        conn.commit()
        conn.close()
    
    @abstractmethod
    def fetch_latest(self) -> Dict:
        """获取最新一期数据"""
        pass
    
    @abstractmethod
    def fetch_history(self, start_date: str, end_date: str) -> List[Dict]:
        """获取历史数据"""
        pass
    
    def _save_to_cache(self, data: Dict, cache_file: str):
        """保存数据到缓存"""
        cache_path = self.cache_dir / cache_file
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_from_cache(self, cache_file: str) -> Optional[Dict]:
        """从缓存加载数据"""
        cache_path = self.cache_dir / cache_file
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_to_db(self, data: Dict, lottery_type: str):
        """保存数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO lottery_data 
            (lottery_type, draw_date, draw_number, numbers, prize_info, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            lottery_type,
            data['draw_date'],
            data['draw_number'],
            json.dumps(data['numbers']),
            json.dumps(data.get('prize_info', {})),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()