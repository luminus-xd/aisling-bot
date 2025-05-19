import discord
from discord.ext import commands
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from discord import ui # uiモジュールをインポート

class SpotifyTrackView(ui.View):
    def __init__(self, tracks, visible_to_others: bool, timeout=180):
        super().__init__(timeout=timeout)
        self.tracks = tracks
        self.visible_to_others = visible_to_others # 表示設定を保持
        self.url_button = ui.Button(label="プレビューで表示", style=discord.ButtonStyle.green)
        self.url_button.callback = self.show_urls
        self.add_item(self.url_button)

    async def show_urls(self, interaction: discord.Interaction):
        if not self.tracks:
            await interaction.response.send_message("表示するプレビューがありません。", ephemeral=True)
            return

        urls = "\n".join([track['external_urls']['spotify'] for track in self.tracks])
        await interaction.response.send_message(f"**検索結果のSpotify URL:**\n{urls}", ephemeral=not self.visible_to_others)
        self.url_button.disabled = True
        await interaction.message.edit(view=self)


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
    @app_commands.describe(visible_to_others="結果を他の人にも表示するかどうか (デフォルト: True)")
    async def search_spotify(self, interaction: discord.Interaction, query: str, visible_to_others: bool = True):
        if not self.sp:
            await interaction.response.send_message("Spotify APIが初期化されていません。管理者にお問い合わせください。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=not visible_to_others)

        try:
            results = self.sp.search(q=query, limit=5, type='track', market='JP')
            tracks = results['tracks']['items']

            if not tracks:
                await interaction.followup.send("曲が見つかりませんでした。", ephemeral=True)
                return

            embed = discord.Embed(title=f"Spotify検索結果: '{query}'", color=discord.Color.green())
            for i, track_item in enumerate(tracks):
                track_name = track_item['name']
                artist_name = ", ".join([artist['name'] for artist in track_item['artists']])
                album_name = track_item['album']['name']
                track_url = track_item['external_urls']['spotify']
                embed.add_field(name=f"{i+1}. {track_name} - {artist_name}",
                                value=f"アルバム: {album_name}\\n"
                                      f"[Spotifyで聴く]({track_url})",
                                inline=False)
            
            view = SpotifyTrackView(tracks, visible_to_others=visible_to_others) # 表示設定をViewに渡す
            await interaction.followup.send(embed=embed, view=view, ephemeral=not visible_to_others)

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