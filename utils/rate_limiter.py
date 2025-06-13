import asyncio
from typing import Dict, List
import time

class RateLimiter:
    """Discord API レート制限を管理するクラス"""
    
    def __init__(self, max_requests: int = 5, time_window: float = 1.0):
        """
        Args:
            max_requests: 時間窓内での最大リクエスト数
            time_window: 時間窓の長さ（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """レート制限をチェックし、必要に応じて待機する"""
        async with self._lock:
            current_time = time.time()
            
            # 時間窓外の古いリクエストを削除
            self.requests = [req_time for req_time in self.requests 
                           if current_time - req_time < self.time_window]
            
            # レート制限に達している場合は待機
            if len(self.requests) >= self.max_requests:
                # 最も古いリクエストから時間窓が経過するまで待機
                oldest_request = self.requests[0]
                wait_time = self.time_window - (current_time - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # 再度古いリクエストをクリーンアップ
                    current_time = time.time()
                    self.requests = [req_time for req_time in self.requests 
                                   if current_time - req_time < self.time_window]
            
            # 現在のリクエストを記録
            self.requests.append(current_time)

# グローバルなレート制限インスタンス
discord_message_limiter = RateLimiter(max_requests=5, time_window=5.0)  # 5秒間に5メッセージまで