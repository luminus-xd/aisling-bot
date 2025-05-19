import discord
from discord.ext import commands
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

class SpotifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            print("エラー: Spotifyの認証情報が設定されていません。")
            self.sp = None
        else:
            try:
                auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                print("Spotify APIの初期化に成功しました。")
            except Exception as e:
                print(f"Spotify APIの初期化中にエラーが発生しました: {e}")
                self.sp = None

    @app_commands.command(name="search_spotify", description="Spotifyで曲を検索します。")
    @app_commands.describe(query="検索する曲名やアーティスト名")
    async def search_spotify(self, interaction: discord.Interaction, query: str):
        if not self.sp:
            await interaction.response.send_message("Spotify APIが初期化されていません。管理者にお問い合わせください。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True) # 処理に時間がかかる場合があるためdefer

        try:
            results = self.sp.search(q=query, limit=5, type='track', market='JP') # 日本のマーケットで検索、5件まで
            tracks = results['tracks']['items']

            if not tracks:
                await interaction.followup.send("曲が見つかりませんでした。", ephemeral=True)
                return

            embed = discord.Embed(title=f"Spotify検索結果: '{query}'", color=discord.Color.green())
            for i, track in enumerate(tracks):
                track_name = track['name']
                artist_name = ", ".join([artist['name'] for artist in track['artists']])
                album_name = track['album']['name']
                track_url = track['external_urls']['spotify']
                embed.add_field(name=f"{i+1}. {track_name} - {artist_name}", 
                                value=f"アルバム: {album_name}\n"
                                      f"[Spotifyで聴く]({track_url})", 
                                inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=False) # 結果は全員に見えるようにする

        except spotipy.SpotifyException as e:
            print(f"Spotify API検索エラー: {e}")
            await interaction.followup.send("Spotifyでの検索中にエラーが発生しました。", ephemeral=True)
        except Exception as e:
            print(f"予期せぬエラー: {e}")
            await interaction.followup.send("検索中に予期せぬエラーが発生しました。", ephemeral=True)


async def setup(bot: commands.Bot):
    cog = SpotifyCog(bot)
    await bot.add_cog(cog)
    # グローバルコマンドとして登録する場合は、treeへの追加もここで行うか、
    # main.py側でtree.add_command(cog.search_spotify, guild=None) のようにする
    # ここではCogのロードのみに留め、コマンドの同期はmain.pyに任せるのが一般的
    print("SpotifyCogが読み込まれました。") 