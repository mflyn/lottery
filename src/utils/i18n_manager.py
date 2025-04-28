import json
from pathlib import Path
from typing import Dict, Optional

class I18nManager:
    """国际化管理器"""
    def __init__(self):
        self.current_language = 'zh_CN'
        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        """加载所有翻译文件"""
        translation_dir = Path(__file__).parent / 'translations'
        for lang_file in translation_dir.glob('*.json'):
            lang_code = lang_file.stem
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations[lang_code] = json.load(f)

    def load_language(self, lang_code: str) -> bool:
        """加载指定语言"""
        if lang_code in self.translations:
            self.current_language = lang_code
            return True
        return False

    def get_text(self, key: str) -> str:
        """获取翻译文本"""
        try:
            return self.translations[self.current_language][key]
        except KeyError:
            return key

    def switch_language(self, language_code: str) -> bool:
        """切换语言"""
        if language_code not in self.translations:
            if not self.load_language(language_code):
                return False
        self.current_language = language_code
        return True
