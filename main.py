import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from modules.voicevox import VoiceVoxHandler
from modules.gemini_api import GeminiHandler
from modules.bot_commands import setup_cogs
from modules.bot_events import BotEventHandler

# .envファイルから環境変数を読み込む
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Discord Botのクライアントを作成
intents = discord.Intents.default()
intents.voice_states = True  # on_voice_state_updateを使用するために必要
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ハンドラーの初期化
voice_handler = VoiceVoxHandler()
gemini_handler = GeminiHandler()
event_handler = BotEventHandler(client)

@client.event
async def on_ready():
    print(f'{client.user} としてDiscordにログインしました！')
    
    # VOICEVOXの初期化
    initialized = await voice_handler.initialize()
    if initialized:
        print("VOICEVOXの初期化に成功しました。")
    else:
        print("VOICEVOXの初期化に失敗しました。")
    
    # Gemini APIの初期化
    if gemini_handler.initialize():
        print("Gemini APIの初期化に成功しました。")
    else:
        print("Gemini APIの初期化に失敗しました。")
    
    # イベントハンドラーの設定
    await event_handler.setup_event_handlers()
    
    try:
        # コマンドの設定
        print("コマンドを設定しています...")
        setup_cogs(client, voice_handler, gemini_handler, client.tree)
        
        # コマンドツリーの状態を確認
        commands = client.tree.get_commands()
        print(f"コマンドツリーに登録されているコマンド数: {len(commands)}")
        for cmd in commands:
            print(f"登録済みコマンド: {cmd.name}")
        
        # グローバルにコマンドを同期（全サーバーに適用）
        print("スラッシュコマンドを同期しています...")
        synced = await client.tree.sync()
        print(f"同期完了: {len(synced)}個のコマンドを同期しました")
        for cmd in synced:
            print(f"同期されたコマンド: {cmd.name}")
    except Exception as e:
        print(f"コマンド同期中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if DISCORD_BOT_TOKEN:
        client.run(DISCORD_BOT_TOKEN)
    else:
        print("エラー: Discord Botトークンが設定されていません。") 