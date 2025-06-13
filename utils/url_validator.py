import re
from urllib.parse import urlparse

class URLValidator:
    """URL検証のためのユーティリティクラス"""
    
    # YouTube URLのパターン
    YOUTUBE_PATTERNS = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """基本的なURL形式の検証"""
        if not url or not isinstance(url, str):
            return False
        
        try:
            result = urlparse(url.strip())
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """YouTube URLかどうかを検証"""
        if not URLValidator.is_valid_url(url):
            return False
        
        parsed = urlparse(url)
        return parsed.netloc.lower() in [
            'youtube.com', 'www.youtube.com', 
            'youtu.be', 'www.youtu.be',
            'm.youtube.com'
        ]
    
    @staticmethod
    def extract_youtube_video_id(url: str) -> str:
        """YouTube URLから動画IDを抽出（検証付き）"""
        if not URLValidator.is_youtube_url(url):
            return ""
        
        for pattern in URLValidator.YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                # 動画IDの形式を検証（11文字の英数字とハイフン、アンダースコア）
                if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                    return video_id
        
        return ""
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """URLをサニタイズ（基本的なクリーンアップ）"""
        if not url:
            return ""
        
        # 空白文字を除去
        url = url.strip()
        
        # 制御文字を除去
        url = ''.join(char for char in url if ord(char) >= 32)
        
        return url