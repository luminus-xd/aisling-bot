import discord
from discord.ext import commands
from discord import app_commands
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter
import re
from modules.gemini_api import GeminiHandler
from utils.url_validator import URLValidator

class YouTubeCog(commands.Cog):
    def __init__(self, bot, gemini_handler: GeminiHandler, voice_handler=None):
        self.bot = bot
        self.gemini_handler = gemini_handler
        self.voice_handler = voice_handler
        
    def extract_video_id(self, url: str) -> str:
        """YouTube URLから動画IDを抽出する（検証強化版）"""
        # URLをサニタイズ
        url = URLValidator.sanitize_url(url)
        
        # YouTube URLの検証とID抽出
        return URLValidator.extract_youtube_video_id(url)
    
    def get_youtube_thumbnail_url(self, video_id: str) -> str:
        """YouTube動画IDからサムネイルURLを生成する"""
        # 高画質サムネイル（maxresdefault）を優先
        # 利用できない場合は自動的に標準画質（hqdefault）にフォールバック
        return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    
    async def get_transcript(self, video_id: str) -> tuple[bool, str]:
        """YouTube動画の字幕を取得する"""
        try:
            # まず日本語字幕を試す
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
            except NoTranscriptFound:
                # 日本語字幕がない場合は英語を試す
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                except NoTranscriptFound:
                    # 英語もない場合は利用可能な任意の言語を使用
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    
            formatter = TextFormatter()
            transcript_text = formatter.format_transcript(transcript_list)
            
            # 長すぎる場合は切り詰める（50分程度の動画まで対応: 300,000文字）
            if len(transcript_text) > 300000:
                transcript_text = transcript_text[:300000] + "...(以下省略)"
                
            return True, transcript_text
            
        except TranscriptsDisabled:
            return False, "この動画は字幕が無効になっています。"
        except NoTranscriptFound:
            return False, "この動画には字幕が見つかりませんでした。"
        except Exception as e:
            return False, f"字幕の取得中にエラーが発生しました: {str(e)}"
    
    @app_commands.command(name="summarize_youtube", description="YouTube動画のリンクから要約を生成します。")
    @app_commands.describe(url="要約するYouTube動画のURL")
    async def summarize_youtube(self, interaction: discord.Interaction, url: str):
        if not url:
            await interaction.response.send_message("YouTube動画のURLを入力してください。", ephemeral=True)
            return
            
        # URLの基本検証
        if not URLValidator.is_valid_url(url):
            await interaction.response.send_message("有効なURLを入力してください。", ephemeral=True)
            return
        
        # YouTube URLかどうか検証
        if not URLValidator.is_youtube_url(url):
            await interaction.response.send_message("YouTube URLを入力してください。", ephemeral=True)
            return
        
        # 動画IDを抽出
        video_id = self.extract_video_id(url)
        if not video_id:
            await interaction.response.send_message("有効なYouTube動画URLを入力してください。", ephemeral=True)
            return
            
        try:
            await interaction.response.defer()  # 処理時間がかかるため応答を保留
        except discord.errors.NotFound:
            # Interactionがタイムアウトした場合の処理
            print("Interaction timeout detected, attempting to send message directly")
            try:
                await interaction.channel.send("YouTube動画の要約処理を開始します...")
            except:
                return
        
        try:
            # まず字幕を取得を試行
            transcript_success, transcript = await self.get_transcript(video_id)
            
            if transcript_success:
                # 字幕が取得できた場合は従来の方法で要約
                summary_prompt = f"""以下のYouTube動画の字幕を日本語で要約してください。

                要約の要件:
                - 主要なポイントを3-5つの箇条書きで整理
                - 各ポイントは簡潔で分かりやすく
                - 動画の内容を的確に表現
                - 日本語で出力

                字幕内容:
                {transcript}"""

                success, summary = await self.gemini_handler.generate_response(summary_prompt)
                summary_method = "字幕"
            else:
                # 字幕が取得できない場合はYouTube URLを直接使用
                print(f"字幕取得失敗、URL直接処理に切り替え: {transcript}")
                success, summary = await self.gemini_handler.generate_youtube_summary(url)
                summary_method = "動画"
            
            if success and summary:
                # 応答をテキストで送信
                embed = discord.Embed(
                    title="YouTube動画要約(動画リンク)",
                    description=summary,
                    color=discord.Color.red(),
                    url=url
                )
                # サムネイル画像を設定
                thumbnail_url = self.get_youtube_thumbnail_url(video_id)
                embed.set_image(url=thumbnail_url)
                embed.set_footer(text=f"動画ID: {video_id} | 要約方法: {summary_method}ベース")
                
                max_length = 4096  # Discord embedの制限
                if len(summary) > max_length:
                    # 長すぎる場合は分割
                    chunks = [summary[i:i + max_length] for i in range(0, len(summary), max_length)]
                    embed.description = chunks[0]
                    
                    # Interactionが有効かチェックして送信
                    try:
                        await interaction.followup.send(embed=embed)
                    except discord.errors.NotFound:
                        # Interactionが無効な場合は直接チャンネルに送信
                        await interaction.channel.send(embed=embed)
                    
                    # レート制限回避のため間隔を空けて送信
                    import asyncio
                    for chunk in chunks[1:]:
                        await asyncio.sleep(1)  # 1秒間隔で送信
                        await interaction.channel.send(chunk)
                else:
                    # Interactionが有効かチェックして送信
                    try:
                        await interaction.followup.send(embed=embed)
                    except discord.errors.NotFound:
                        # Interactionが無効な場合は直接チャンネルに送信
                        await interaction.channel.send(embed=embed)
                    
                # ボイスチャンネルに参加していれば、要約を読み上げる
                if interaction.guild.voice_client and interaction.guild.voice_client.is_connected() and self.voice_handler:
                    speech_segments = self.gemini_handler.split_text_for_speech(summary)
                    
                    for segment in speech_segments:
                        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
                            break
                            
                        if interaction.guild.voice_client.is_playing():
                            import asyncio
                            await asyncio.sleep(1)  # レート制限考慮で少し長めに待機
                            continue
                            
                        audio_data = await self.voice_handler.synthesize_voice(segment)
                        if audio_data:
                            await self.voice_handler.play_audio_in_vc(interaction.guild.voice_client, audio_data)
                            await asyncio.sleep(0.5)  # 音声セグメント間に間隔を設ける
                            
            else:
                try:
                    await interaction.followup.send("要約の生成に失敗しました。")
                except discord.errors.NotFound:
                    await interaction.channel.send("要約の生成に失敗しました。")
                
        except Exception as e:
            print(f"YouTube要約処理中にエラーが発生しました: {e}")
            
            # Discord API レート制限エラーの場合
            error_message = ""
            if "429" in str(e) or "Too Many Requests" in str(e):
                error_message = "現在Discord APIのレート制限により一時的に利用できません。しばらく待ってから再度お試しください。"
            elif "HTTPException" in str(e):
                error_message = "Discord APIとの通信でエラーが発生しました。しばらく待ってから再度お試しください。"
            else:
                error_message = f"処理中にエラーが発生しました: {str(e)}"
                
            # Interactionが有効かチェックして送信
            try:
                await interaction.followup.send(error_message)
            except discord.errors.NotFound:
                await interaction.channel.send(error_message)