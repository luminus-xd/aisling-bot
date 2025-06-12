import discord
from discord.ext import commands
from discord import app_commands
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter
import re
from modules.gemini_api import GeminiHandler

class YouTubeCog(commands.Cog):
    def __init__(self, bot, gemini_handler: GeminiHandler, voice_handler=None):
        self.bot = bot
        self.gemini_handler = gemini_handler
        self.voice_handler = voice_handler
        
    def extract_video_id(self, url: str) -> str:
        """YouTube URLから動画IDを抽出する"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""
    
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
            
            # 長すぎる場合は切り詰める（Gemini APIの制限を考慮）
            if len(transcript_text) > 50000:
                transcript_text = transcript_text[:50000] + "...(以下省略)"
                
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
            
        # 動画IDを抽出
        video_id = self.extract_video_id(url)
        if not video_id:
            await interaction.response.send_message("有効なYouTube URLを入力してください。", ephemeral=True)
            return
            
        await interaction.response.defer()  # 処理時間がかかるため応答を保留
        
        try:
            # 字幕を取得
            success, transcript = await self.get_transcript(video_id)
            if not success:
                await interaction.followup.send(f"字幕の取得に失敗しました: {transcript}")
                return
                
            # Gemini APIで要約を生成
            summary_prompt = f"""以下のYouTube動画の字幕を日本語で要約してください。

要約の要件:
- 主要なポイントを3-5つの箇条書きで整理
- 各ポイントは簡潔で分かりやすく
- 動画の内容を的確に表現
- 日本語で出力

字幕内容:
{transcript}"""

            success, summary = await self.gemini_handler.generate_response(summary_prompt)
            
            if success and summary:
                # 応答をテキストで送信
                embed = discord.Embed(
                    title="YouTube動画要約",
                    description=summary,
                    color=discord.Color.red(),
                    url=url
                )
                embed.set_footer(text=f"動画ID: {video_id}")
                
                max_length = 4096  # Discord embedの制限
                if len(summary) > max_length:
                    # 長すぎる場合は分割
                    chunks = [summary[i:i + max_length] for i in range(0, len(summary), max_length)]
                    embed.description = chunks[0]
                    await interaction.followup.send(embed=embed)
                    
                    for chunk in chunks[1:]:
                        await interaction.channel.send(chunk)
                else:
                    await interaction.followup.send(embed=embed)
                    
                # ボイスチャンネルに参加していれば、要約を読み上げる
                if interaction.guild.voice_client and interaction.guild.voice_client.is_connected() and self.voice_handler:
                    speech_segments = self.gemini_handler.split_text_for_speech(summary)
                    
                    for segment in speech_segments:
                        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
                            break
                            
                        if interaction.guild.voice_client.is_playing():
                            import asyncio
                            await asyncio.sleep(0.5)
                            continue
                            
                        audio_data = await self.voice_handler.synthesize_voice(segment)
                        if audio_data:
                            await self.voice_handler.play_audio_in_vc(interaction.guild.voice_client, audio_data)
                            
            else:
                await interaction.followup.send("要約の生成に失敗しました。")
                
        except Exception as e:
            print(f"YouTube要約処理中にエラーが発生しました: {e}")
            await interaction.followup.send(f"処理中にエラーが発生しました: {str(e)}")