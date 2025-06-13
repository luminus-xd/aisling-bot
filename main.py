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
    
    # ステータスメッセージの設定
    activity = discord.Activity(type=discord.ActivityType.competing, name="カレー調理")
    await client.change_presence(activity=activity)
    
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
        setup_cogs(client, voice_handler, gemini_handler, tree)
        
        # コマンドツリーの状態を確認
        commands = tree.get_commands()
        print(f"コマンドツリーに登録されているコマンド数: {len(commands)}")
        for cmd in commands:
            print(f"登録済みコマンド: {cmd.name}")
        
        # グローバルにコマンドを同期（全サーバーに適用）
        print("スラッシュコマンドを同期しています...")
        synced = await tree.sync()
        print(f"同期完了: {len(synced)}個のコマンドを同期しました")
        for cmd in synced:
            print(f"同期されたコマンド: {cmd.name}")
    except Exception as e:
        print(f"コマンド同期中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def validate_environment():
    """環境変数の検証を行う"""
    errors = []
    
    if not DISCORD_BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN が設定されていません。")
    elif len(DISCORD_BOT_TOKEN.strip()) < 50:  # Discord トークンの最小長をチェック
        errors.append("DISCORD_BOT_TOKEN が無効な形式です。")
    
    if not os.getenv("GEMINI_API_KEY"):
        errors.append("GEMINI_API_KEY が設定されていません。")
    
    # VOICEVOX設定の検証
    model_id = os.getenv("VOICEVOX_MODEL_ID", "0")
    if not model_id.isdigit():
        errors.append("VOICEVOX_MODEL_ID は数字である必要があります。")
    
    style_id = os.getenv("VOICEVOX_STYLE_ID", "8")
    try:
        int(style_id)
    except ValueError:
        errors.append("VOICEVOX_STYLE_ID は数字である必要があります。")
    
    return errors

if __name__ == "__main__":
    # 環境変数の検証
    validation_errors = validate_environment()
    if validation_errors:
        print("環境変数エラー:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\n.envファイルを確認してください。")
        exit(1)
    
    try:
        client.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("エラー: Discord Botトークンが無効です。正しいトークンを設定してください。")
        exit(1)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        exit(1) 