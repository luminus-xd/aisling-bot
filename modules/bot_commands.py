import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from modules.voicevox import VoiceVoxHandler
from modules.gemini_api import GeminiHandler
from cogs.spotify_cog import SpotifyCog

class BasicCommandsCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        
    @app_commands.command(name="hello", description="つむぎが挨拶を返します。")
    async def hello_command(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'こんにちは、{interaction.user.name}さん！')
        
    @app_commands.command(name="join", description="つむぎをボイスチャンネルに参加させます。")
    async def join_command(self, interaction: discord.Interaction):
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            voice_client = interaction.guild.voice_client
            if voice_client:
                if voice_client.channel != channel:
                    await voice_client.move_to(channel)
                    await interaction.response.send_message(f'{channel.name} に移動しました。')
                else:
                    await interaction.response.send_message(f'既に {channel.name} に接続しています。', ephemeral=True)
            else:
                vc = await channel.connect()
                # 自動切断メッセージ用にチャンネルを保存する属性を設定
                setattr(vc, "last_interaction_channel", interaction.channel)
                await interaction.response.send_message(f'{channel.name} に接続しました。')
        else:
            await interaction.response.send_message("あなたが先にボイスチャンネルに参加してください。", ephemeral=True)
            
    @app_commands.command(name="leave", description="つむぎをボイスチャンネルから切断します。")
    async def leave_command(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("ボイスチャンネルから切断しました。")
        else:
            await interaction.response.send_message("つむぎはボイスチャンネルに参加していません。", ephemeral=True)

    @app_commands.command(name="help", description="利用可能なコマンドの一覧を表示します。")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="つむぎボット ヘルプ", description="利用可能なコマンドの一覧です。", color=discord.Color.blue())
        
        # BasicCommandsCog
        embed.add_field(name="基本コマンド", value=" ", inline=False)
        embed.add_field(name="`/hello`", value="つむぎが挨拶を返します。", inline=True)
        embed.add_field(name="`/join`", value="つむぎをボイスチャンネルに参加させます。", inline=True)
        embed.add_field(name="`/leave`", value="つむぎをボイスチャンネルから切断します。", inline=True)
        
        # VoiceCommandsCog
        embed.add_field(name="音声コマンド", value=" ", inline=False)
        embed.add_field(name="`/speak [テキスト]`", value="指定されたテキストを読み上げます。", inline=True)
        
        # AICommandsCog
        embed.add_field(name="質問コマンド", value=" ", inline=False)
        embed.add_field(name="`/ask [質問]`", value="つむぎに質問し、応答をテキストと音声で返します。", inline=True)
        
        # SpotifyCog
        embed.add_field(name="音楽コマンド", value=" ", inline=False)
        embed.add_field(name="`/search_spotify [曲名/アーティスト]`", value="Spotifyで曲を検索します。", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class VoiceCommandsCog(commands.Cog):
    def __init__(self, bot: discord.Client, voice_handler: VoiceVoxHandler):
        self.bot = bot
        self.voice_handler = voice_handler
        
    @app_commands.command(name="speak", description="指定されたテキストを読み上げます。")
    @app_commands.describe(text_to_speak="読み上げるテキスト")
    async def speak_command(self, interaction: discord.Interaction, text_to_speak: str):
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("つむぎがボイスチャンネルに参加していません。`/join`コマンドで参加させてください。", ephemeral=True)
            return
        
        if not text_to_speak:
            await interaction.response.send_message("読み上げるテキストを入力してください。", ephemeral=True)
            return

        # 応答を保留 (thinking...)
        await interaction.response.defer()

        audio_data = await self.voice_handler.synthesize_voice(text_to_speak)
        if audio_data:
            if voice_client.is_playing():
                await interaction.followup.send("現在他の音声を再生中です。少し待ってから再度お試しください。")
                return
                
            # 自動切断メッセージ用にチャンネルを保存
            setattr(voice_client, "last_interaction_channel", interaction.channel)
            await interaction.followup.send(f'「{text_to_speak}」を読み上げます...')
            success = await self.voice_handler.play_audio_in_vc(voice_client, audio_data)
            if not success:
                await interaction.followup.send("音声の再生に失敗しました。")
        else:
            await interaction.followup.send("音声の生成に失敗しました。")


class AICommandsCog(commands.Cog):
    def __init__(self, bot: discord.Client, gemini_handler: GeminiHandler, voice_handler: VoiceVoxHandler):
        self.bot = bot
        self.gemini_handler = gemini_handler
        self.voice_handler = voice_handler
        
    @app_commands.command(name="ask", description="つむぎに質問し、応答をテキストと音声で返します。")
    @app_commands.describe(query="つむぎへの質問内容")
    async def ask_command(self, interaction: discord.Interaction, query: str):
        if not query:
            await interaction.response.send_message("質問内容を入力してください。", ephemeral=True)
            return

        await interaction.response.defer()  # Geminiからの応答待ちのため、応答を保留

        try:
            success, response_text = await self.gemini_handler.generate_response(query)
            
            if response_text:
                # 応答をテキストで送信
                max_length = 2000
                chunks = [response_text[i:i + max_length] for i in range(0, len(response_text), max_length)]
                first_chunk = True
                for chunk in chunks:
                    if first_chunk:
                        await interaction.followup.send(chunk)  # 最初のメッセージはfollowupで
                        first_chunk = False
                    else:
                        await interaction.channel.send(chunk)  # 2つ目以降の長いメッセージはchannel.send
            else:
                await interaction.followup.send("つむぎから応答がありませんでした。")
                return

            # ボイスチャンネルに参加していれば、応答を読み上げる
            if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
                speech_segments = self.gemini_handler.split_text_for_speech(response_text)
                
                for i, segment in enumerate(speech_segments):
                    if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
                        print("読み上げ中にボイスチャンネルから切断されました。")
                        break
                    
                    if interaction.guild.voice_client.is_playing():
                        print("現在他の音声を再生中です。このセグメントの読み上げをスキップします。")
                        await asyncio.sleep(1)  # 少し待つ
                        continue

                    audio_data = await self.voice_handler.synthesize_voice(segment)
                    if audio_data:
                        success = await self.voice_handler.play_audio_in_vc(interaction.guild.voice_client, audio_data)
                        if not success:
                            await interaction.channel.send(f"セグメント「{segment[:20]}...」の音声再生に失敗しました。")
                            break
                        if i < len(speech_segments) - 1:
                            await asyncio.sleep(0.5)
                    else:
                        await interaction.channel.send(f"セグメント「{segment[:20]}...」の音声生成に失敗しました。")
                        break

        except Exception as e:
            print(f"Gemini APIリクエストまたは音声合成中にエラーが発生しました: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"申し訳ありません、処理中にエラーが発生しました。 {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"申し訳ありません、処理中にエラーが発生しました。 {e}")


def setup_cogs(bot: discord.Client, voice_handler: VoiceVoxHandler, gemini_handler: GeminiHandler, tree: app_commands.CommandTree):
    """コマンドツリーにCogを登録する"""
    # 一度コマンドツリーをクリアする（同じコマンドが重複登録されないように）
    tree.clear_commands(guild=None)
    
    basic_cog = BasicCommandsCog(bot)
    voice_cog = VoiceCommandsCog(bot, voice_handler)
    ai_cog = AICommandsCog(bot, gemini_handler, voice_handler)
    spotify_cog = SpotifyCog(bot)

    # BasicCommandsCogのコマンドを追加
    print("BasicCommandsCogのコマンドを追加中...")
    tree.add_command(basic_cog.hello_command)
    tree.add_command(basic_cog.join_command)
    tree.add_command(basic_cog.leave_command)
    tree.add_command(basic_cog.help_command)
    
    # VoiceCommandsCogのコマンドを追加
    print("VoiceCommandsCogのコマンドを追加中...")
    tree.add_command(voice_cog.speak_command)
    
    # AICommandsCogのコマンドを追加
    print("AICommandsCogのコマンドを追加中...")
    tree.add_command(ai_cog.ask_command)

    # SpotifyCogのコマンドを追加
    print("SpotifyCogのコマンドを追加中...")
    tree.add_command(spotify_cog.search_spotify)
    
    print("すべてのコマンドをコマンドツリーに追加しました。") 