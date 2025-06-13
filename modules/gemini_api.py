import os
import google.generativeai as genai
from config import GEMINI_DEFAULT_PERSONA, GEMINI_MODEL_NAME

class GeminiHandler:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        self.initialized = False
        
    def initialize(self):
        """Gemini APIを初期化する"""
        if not self.api_key:
            print("エラー: Gemini APIキーが設定されていません。")
            return False
            
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL_NAME) 
            self.initialized = True
            return True
        except Exception as e:
            print(f"Gemini APIの初期化中にエラーが発生しました: {e}")
            return False
    
    async def generate_response(self, query: str):
        """ユーザーの質問に対してGemini APIを使用して応答を生成する"""
        if not self.initialized or not self.model:
            print("Gemini APIが初期化されていません。")
            return None, "Gemini APIが設定されていません。"
            
        try:
            # キャラクター設定をconfig.pyから読み込む
            prompt_with_personality = f"{GEMINI_DEFAULT_PERSONA}\n\nユーザーからの質問:\n{query}"
            gemini_response = await self.model.generate_content_async(prompt_with_personality)
            
            if gemini_response.text:
                return True, gemini_response.text
            elif gemini_response.prompt_feedback and gemini_response.prompt_feedback.block_reason:
                error_message = f"つむぎからの応答がブロックされました。理由: {gemini_response.prompt_feedback.block_reason}"
                return False, error_message
            else:
                error_message = "つむぎから有効な応答がありませんでした。"
                return False, error_message
                
        except Exception as e:
            print(f"Gemini APIリクエスト中にエラーが発生しました: {e}")
            return False, "申し訳ありません、処理中にエラーが発生しました。"
    
    async def generate_youtube_summary(self, youtube_url: str):
        """YouTube URLを使用してGemini APIで動画要約を生成する"""
        if not self.initialized or not self.model:
            print("Gemini APIが初期化されていません。")
            return False, "Gemini APIが設定されていません。"
            
        try:
            # YouTube動画の要約を生成するプロンプト
            summary_prompt = """この YouTube 動画の内容を日本語で要約してください。

            要約の要件:
            - 主要なポイントを3-5つの箇条書きで整理
            - 各ポイントは簡潔で分かりやすく
            - 動画の内容を的確に表現
            - 日本語で出力"""
            
            # YouTube URLを含むコンテンツでリクエスト
            content = [
                summary_prompt,
                {"file_data": {"file_uri": youtube_url}}
            ]
            
            response = await self.model.generate_content_async(content)
            
            if response.text:
                return True, response.text
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                error_message = f"応答がブロックされました。理由: {response.prompt_feedback.block_reason}"
                return False, error_message
            else:
                error_message = "有効な応答がありませんでした。"
                return False, error_message
                
        except Exception as e:
            print(f"YouTube動画要約中にエラーが発生しました: {e}")
            return False, "YouTube動画の処理中にエラーが発生しました。"
            
    def split_text_for_speech(self, text: str, max_length: int = 120):
        """音声合成用にテキストを適切なセグメントに分割する"""
        if not text:
            return []
            
        speech_segments = []
        current_segment = ""
        # 簡単な句読点での分割を試みる
        delimiters = "。、."
        buffer = ""
        
        for char in text:
            buffer += char
            if char in delimiters and len(buffer) > max_length * 0.7:  # ある程度長くなったら区切る
                speech_segments.append(buffer.strip())
                buffer = ""
            elif len(buffer) >= max_length:
                speech_segments.append(buffer.strip())
                buffer = ""
                
        if buffer.strip():
            speech_segments.append(buffer.strip())
            
        if not speech_segments and text.strip():  # 区切り文字がなく、全体が短い場合
            speech_segments.append(text.strip())
            
        return speech_segments 