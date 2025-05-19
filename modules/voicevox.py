from voicevox_core.asyncio import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
import os
import io
import discord
import traceback

class VoiceVoxHandler:
    def __init__(self):
        self.synthesizer = None
        # 環境変数から設定を読み込む
        self.model_id = os.getenv("VOICEVOX_MODEL_ID", "0")  # デフォルトを "0" (0.vvm) に
        self.style_id = int(os.getenv("VOICEVOX_STYLE_ID", "8"))  # デフォルトを 8 (ノーマルスタイル等を想定)
    
    async def initialize(self):
        """VoiceVox Synthesizerを初期化する"""
        try:
            # Dockerfileでコピーされた固定パスを使用
            open_jtalk_dict_dir = "/app/voicevox_files/open_jtalk_dic"
            print(f"Open JTalk辞書を {open_jtalk_dict_dir} から読み込みます。")

            # ONNXRuntimeのロード処理
            try:
                print("ONNXRuntimeをロードします...")
                ort = await Onnxruntime.load_once()
                print("ONNXRuntimeのロードに成功しました")
            except Exception as e:
                print(f"ONNXRuntimeのロードに失敗しました: {e}")
                raise

            # OpenJTalkの初期化処理
            try:
                print("OpenJTalkを初期化します...")
                ojt = await OpenJtalk.new(open_jtalk_dict_dir)
                print("OpenJTalkの初期化に成功しました")
            except Exception as e:
                print(f"OpenJTalkの初期化に失敗しました: {e}")
                raise
                
            # Synthesizerの作成
            self.synthesizer = Synthesizer(ort, ojt)
            
            # VOICEVOX_MODEL_IDを使って.vvmファイルパスを決定
            vvm_model_path = f"/app/voicevox_files/models/{self.model_id}.vvm"

            if os.path.exists(vvm_model_path):
                print(f"モデルファイル {vvm_model_path} をロードします...")
                async with await VoiceModelFile.open(vvm_model_path) as model:
                    await self.synthesizer.load_voice_model(model)
                print(f"モデル {vvm_model_path} をロードしました。")
            else:
                print(f"警告: モデルファイルが {vvm_model_path} に見つかりません。音声合成は利用できません。")
                self.synthesizer = None
            
            return self.synthesizer is not None
        except Exception as e:
            print(f"VOICEVOX Synthesizerの初期化中にエラーが発生しました: {e}")
            self.synthesizer = None
            return False
    
    async def synthesize_voice(self, text: str) -> bytes | None:
        """VOICEVOXを使用してテキストから音声データを生成する"""
        if not self.synthesizer:
            print("エラー: VOICEVOX Synthesizerが初期化されていません。")
            return None
        
        if not text:
            print("エラー: 読み上げるテキストが空です。")
            return None

        try:
            # 環境変数から取得した固定のスタイルIDを使用
            style_id_to_use = self.style_id
            
            audio_query = await self.synthesizer.create_audio_query(text, style_id=style_id_to_use)
            wave_bytes = await self.synthesizer.synthesis(audio_query, style_id_to_use)

            return wave_bytes
        except Exception as e:
            # エラーの詳細情報をログに出力
            print(f"VOICEVOX音声合成エラー: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    async def play_audio_in_vc(self, voice_client: discord.VoiceClient, audio_data: bytes):
        """ボイスチャンネルで音声データを再生する"""
        if not voice_client or not voice_client.is_connected():
            print("エラー: ボイスクライアントが無効です。")
            return False

        try:
            # 音声データをBytesIOに変換
            audio_source = discord.FFmpegPCMAudio(io.BytesIO(audio_data), pipe=True)
            
            if not voice_client.is_playing():
                voice_client.play(audio_source, after=lambda e: print(f'再生終了: {e}' if e else ''))
                return True
            else:
                # すでに再生中の場合
                return False
        except Exception as e:
            print(f"音声再生中にエラーが発生しました: {e}")
            return False 