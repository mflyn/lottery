import json

class I18nManager:
    def __init__(self):
        self.current_language = 'zh_CN'
        self.translations = {}
        
    def load_language(self, language_code):
        """加载语言包"""
        try:
            # 从JSON文件加载语言包
            file_path = f'src/core/i18n/lang/{language_code}.json'
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.current_language = language_code
            return True
        except FileNotFoundError:
            return False
            
    def get_text(self, key):
        """获取翻译文本"""
        return self.translations.get(key, key)
