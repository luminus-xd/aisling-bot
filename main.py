import discord
from discord import app_commands
import os
import asyncio
# import requests # voicevox_core に置き換わるため、削除
import io
import google.generativeai as genai
from dotenv import load_dotenv
from config import GEMINI_DEFAULT_PERSONA, GEMINI_MODEL_NAME # config.py からインポート
from voicevox_core.asyncio import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

# .envファイルから環境変数を読み込む
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# VOICEVOX_SPEAKER_ID を VOICEVOX_STYLE_ID に変更
VOICEVOX_MODEL_ID = os.getenv("VOICEVOX_MODEL_ID", "0") # デフォルトを "0" (0.vvm) に
VOICEVOX_STYLE_ID = int(os.getenv("VOICEVOX_STYLE_ID", "8")) # デフォルトを 8 (ノーマルスタイル等を想定)

# VoiceVox Synthesizer の初期化
synthesizer = None

async def init_voicevox():
    global synthesizer
    try:
        # Dockerfileでコピーされた固定パスを使用
        open_jtalk_dict_dir = "/app/voicevox_files/open_jtalk_dic"

        print(f"Open JTalk辞書を {open_jtalk_dict_dir} から読み込みます。")

        # ONNXRuntimeのロード処理を個別にトライキャッチ
        try:
            print("ONNXRuntimeをロードします...")
            ort = await Onnxruntime.load_once()
            print("ONNXRuntimeのロードに成功しました")
        except Exception as e:
            print(f"ONNXRuntimeのロードに失敗しました: {e}")
            raise

        # OpenJTalkの初期化処理を個別にトライキャッチ
        try:
            print("OpenJTalkを初期化します...")
            ojt = await OpenJtalk.new(open_jtalk_dict_dir)
            print("OpenJTalkの初期化に成功しました")
        except Exception as e:
            print(f"OpenJTalkの初期化に失敗しました: {e}")
            raise
            
        # Synthesizerの作成
        synthesizer = Synthesizer(ort, ojt)
        
        # VOICEVOX_MODEL_ID を使って .vvm ファイルパスを決定
        vvm_model_path = f"/app/voicevox_files/models/{VOICEVOX_MODEL_ID}.vvm"

        if os.path.exists(vvm_model_path):
            print(f"モデルファイル {vvm_model_path} をロードします...")
            async with await VoiceModelFile.open(vvm_model_path) as model:
                await synthesizer.load_voice_model(model)
            print(f"モデル {vvm_model_path} をロードしました。")
            
            # メタ情報の取得とログ出力
            # try:
            #     loaded_metas = synthesizer.metas() 
            # except TypeError:
            #     loaded_metas = synthesizer.metas 
            # except Exception as e_meta:
            #     print(f"DEBUG: synthesizer.metas の呼び出し/アクセス中にエラー: {e_meta}")
            #     loaded_metas = [] 

            # if not loaded_metas:
            #     print("警告: ロードされたモデルからメタ情報を取得できませんでした。")
        else:
            print(f"警告: モデルファイルが {vvm_model_path} に見つかりません。音声合成は利用できません。")
            synthesizer = None
    except Exception as e:
        print(f"VOICEVOX Synthesizer の初期化中にエラーが発生しました: {e}")
        synthesizer = None

# Gemini APIの設定
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME) # configからモデル名を読み込む
else:
    print("エラー: Gemini APIキーが設定されていません。")
    gemini_model = None

# Discord Botのクライアントとコマンドツリーを作成
intents = discord.Intents.default()
intents.voice_states = True # on_voice_state_update を使用するために必要
# intents.message_content = True # メッセージコンテントIntentを有効にする場合 (現在未使用)
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# VoiceVox で音声合成を行う関数
async def synthesize_voice(text: str) -> bytes | None: # speaker_id 引数を削除
    """VOICEVOXを使用してテキストから音声データを生成する"""
    if not synthesizer:
        print("エラー: VOICEVOX Synthesizer が初期化されていません。")
        return None
    
    if not text:
        print("エラー: 読み上げるテキストが空です。")
        return None

    try:
        # 環境変数から取得した固定のスタイルIDを使用
        style_id_to_use = VOICEVOX_STYLE_ID 
        
        audio_query = await synthesizer.create_audio_query(text, style_id=style_id_to_use)
        wave_bytes = await synthesizer.synthesis(audio_query, style_id_to_use)

        return wave_bytes
    except Exception as e:
        # エラーの詳細情報をログに出力
        import traceback
        print(f"VOICEVOX 音声合成エラー: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

# ボイスチャンネルで音声を再生する関数
async def play_audio_in_vc(voice_client: discord.VoiceClient, audio_data: bytes):
    """ボイスチャンネルで音声データを再生する"""
    if not voice_client or not voice_client.is_connected():
        print("エラー: ボイスクライアントが無効です。")
        return

    try:
        # 音声データをBytesIOに変換
        audio_source = discord.FFmpegPCMAudio(io.BytesIO(audio_data), pipe=True)
        if not voice_client.is_playing():
            voice_client.play(audio_source, after=lambda e: print(f'再生終了: {e}' if e else ''))
            while voice_client.is_playing():
                await asyncio.sleep(1) # 再生が終わるまで待機
        else:
            # すでに再生中の場合のメッセージはコマンド側でインタラクションに返信
            # print("エラー: 現在他の音声を再生中です。") 
            pass # Interactionにメッセージを返すためここでは何もしない
    except Exception as e:
        print(f"音声再生中にエラーが発生しました: {e}")
        # エラーメッセージもコマンド側でインタラクションに返信

@client.event
async def on_ready():
    print(f'{client.user} としてDiscordにログインしました！')
    # VOICEVOXの初期化
    await init_voicevox()
    
    try:
        # 現在のギルドに対してコマンドを同期 (グローバル同期は時間がかかる場合がある)
        # guild_id = YOUR_GUILD_ID # テスト用のギルドIDを指定
        # await tree.sync(guild=discord.Object(id=guild_id))
        await tree.sync() # グローバルにコマンドを同期
        print("スラッシュコマンドを同期しました。")
    except Exception as e:
        print(f"コマンド同期中にエラーが発生しました: {e}")

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """ボイスチャンネルの状態が変化したときに呼び出されるイベント"""
    # Bot自身の状態変化は無視
    if member.id == client.user.id:
        return

    voice_client = member.guild.voice_client
    if voice_client and voice_client.is_connected():
        # Botが接続しているチャンネルを取得
        connected_channel = voice_client.channel
        
        # チャンネルにBot以外のユーザーが残っているか確認
        # Bot以外のメンバーのリストを作成
        human_members = [m for m in connected_channel.members if not m.bot]
        
        if not human_members: # Botしか残っていない場合
            print(f"{connected_channel.name} にBotしかいないため、自動切断します。")
            await voice_client.disconnect()
            # テキストチャンネルに通知メッセージを送信する
            last_interaction_channel = getattr(voice_client, "last_interaction_channel", None)
            if last_interaction_channel:
                try:
                    await last_interaction_channel.send("ボイスチャンネルに誰もいなくなったため、自動的に切断しました。")
                except discord.errors.Forbidden:
                    print("自動切断メッセージの送信に失敗しました（権限不足）。")
                except Exception as e:
                    print(f"自動切断メッセージ送信中に予期せぬエラー: {e}")

# --- スラッシュコマンドの定義 ---

@tree.command(name="hello", description="つむぎが挨拶を返します。")
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message(f'こんにちは、{interaction.user.name}さん！')

@tree.command(name="join", description="つむぎをボイスチャンネルに参加させます。")
async def join_command(interaction: discord.Interaction):
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
            # vc.last_interaction_channel = interaction.channel # 自動切断メッセージ用にチャンネルを保存
            await interaction.response.send_message(f'{channel.name} に接続しました。')
    else:
        await interaction.response.send_message("あなたが先にボイスチャンネルに参加してください。", ephemeral=True)

@tree.command(name="leave", description="つむぎをボイスチャンネルから切断します。")
async def leave_command(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("ボイスチャンネルから切断しました。")
    else:
        await interaction.response.send_message("つむぎはボイスチャンネルに参加していません。", ephemeral=True)

@tree.command(name="speak", description="指定されたテキストを読み上げます。")
@app_commands.describe(text_to_speak="読み上げるテキスト")
async def speak_command(interaction: discord.Interaction, text_to_speak: str):
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        await interaction.response.send_message("つむぎがボイスチャンネルに参加していません。`/join`コマンドで参加させてください。", ephemeral=True)
        return
    
    if not text_to_speak:
        await interaction.response.send_message("読み上げるテキストを入力してください。", ephemeral=True)
        return

    # 応答を保留 (thinking...)
    await interaction.response.defer()

    audio_data = await synthesize_voice(text_to_speak) # speaker_id引数を削除
    if audio_data:
        if voice_client.is_playing():
            await interaction.followup.send("現在他の音声を再生中です。少し待ってから再度お試しください。")
            return
        # voice_client.last_interaction_channel = interaction.channel # 自動切断メッセージ用にチャンネルを保存
        await interaction.followup.send(f'「{text_to_speak}」を読み上げます...') # followupで最初のメッセージを送信
        await play_audio_in_vc(voice_client, audio_data)
    else:
        await interaction.followup.send("音声の生成に失敗しました。")

@tree.command(name="ask", description="つむぎに質問し、応答をテキストと音声で返します。")
@app_commands.describe(query="つむぎへの質問内容")
async def ask_command(interaction: discord.Interaction, query: str):
    if not gemini_model:
        await interaction.response.send_message("Gemini APIが設定されていません。", ephemeral=True)
        return
    
    if not query:
        await interaction.response.send_message("質問内容を入力してください。", ephemeral=True)
        return

    await interaction.response.defer() # Geminiからの応答待ちのため、応答を保留

    try:
        # キャラクター設定をconfig.pyから読み込む
        prompt_with_personality = f"{GEMINI_DEFAULT_PERSONA}\n\nユーザーからの質問:\n{query}"
        gemini_response = await gemini_model.generate_content_async(prompt_with_personality)
        
        response_text = ""
        if gemini_response.text:
            response_text = gemini_response.text
            # 応答をテキストで送信
            max_length = 2000
            chunks = [response_text[i:i + max_length] for i in range(0, len(response_text), max_length)]
            first_chunk = True
            for chunk in chunks:
                if first_chunk:
                    await interaction.followup.send(chunk) # 最初のメッセージはfollowupで
                    first_chunk = False
                else:
                    await interaction.channel.send(chunk) # 2つ目以降の長いメッセージはchannel.send
        elif gemini_response.prompt_feedback and gemini_response.prompt_feedback.block_reason:
            error_message = f"つむぎからの応答がブロックされました。理由: {gemini_response.prompt_feedback.block_reason}"
            await interaction.followup.send(error_message)
            response_text = error_message 
        else:
            error_message = "つむぎから有効な応答がありませんでした。"
            await interaction.followup.send(error_message)
            response_text = error_message

        # ボイスチャンネルに参加していれば、応答を読み上げる
        if response_text and interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
            # 既に interaction.followup.send が呼ばれているので、ここでは channel.send を使うか、
            # もしくは、読み上げ開始のメッセージを別途送信する
            # await interaction.channel.send("Geminiの応答を読み上げます...") # 読み上げ開始の通知
            
            text_for_speech = response_text
            max_speech_len = 100 
            
            speech_segments = []
            current_segment = ""
            # 簡単な句読点での分割を試みる (より高度な分割も検討可能)
            delimiters = "。、."
            buffer = ""
            for char in text_for_speech:
                buffer += char
                if char in delimiters and len(buffer) > max_speech_len * 0.7: # ある程度長くなったら区切る
                    speech_segments.append(buffer.strip())
                    buffer = ""
                elif len(buffer) >= max_speech_len:
                    speech_segments.append(buffer.strip())
                    buffer = ""
            if buffer.strip():
                speech_segments.append(buffer.strip())
            
            if not speech_segments: # 区切り文字がなく、全体が短い場合
                 if text_for_speech.strip():
                    speech_segments.append(text_for_speech.strip())

            for i, segment in enumerate(speech_segments):
                if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
                    print("読み上げ中にボイスチャンネルから切断されました。")
                    break 
                
                if interaction.guild.voice_client.is_playing():
                    print("現在他の音声を再生中です。このセグメントの読み上げをスキップします。")
                    await asyncio.sleep(1) # 少し待つ
                    continue

                # print(f"セグメント {i+1}/{len(speech_segments)} を読み上げ中: 「{segment}」")
                audio_data = await synthesize_voice(segment) # speaker_id引数を削除
                if audio_data:
                    await play_audio_in_vc(interaction.guild.voice_client, audio_data)
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

if __name__ == "__main__":
    if DISCORD_BOT_TOKEN:
        client.run(DISCORD_BOT_TOKEN)
    else:
        print("エラー: Discord Botトークンが設定されていません。") 