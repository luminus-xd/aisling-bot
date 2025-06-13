import discord
import asyncio

class BotEventHandler:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self._disconnect_lock = asyncio.Lock()  # 競合状態を防ぐためのロック
        
    async def setup_event_handlers(self):
        """ボットのイベントハンドラを設定する"""
        # on_readyイベントはmain.pyで処理する必要があるため、ここでは他のイベントのみ設定
        self.bot.event(self.on_voice_state_update)
        
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """ボイスチャンネルの状態が変化したときに呼び出されるイベント"""
        # Bot自身の状態変化は無視
        if member.id == self.bot.user.id:
            return

        # 複数の音声状態変化が同時に発生する場合の競合状態を防ぐ
        async with self._disconnect_lock:
            voice_client = member.guild.voice_client
            
            # ボイスクライアントが存在し、接続されているかチェック
            if not voice_client or not voice_client.is_connected():
                return
            
            # Botが接続しているチャンネルを取得
            connected_channel = voice_client.channel
            if not connected_channel:
                return
            
            # チャンネルにBot以外のユーザーが残っているか確認
            try:
                # Bot以外のメンバーのリストを作成（再度接続状態をチェック）
                human_members = [m for m in connected_channel.members if not m.bot]
                
                if not human_members:  # Botしか残っていない場合
                    print(f"{connected_channel.name} にBotしかいないため、自動切断します。")
                    
                    # 切断前に再度接続状態を確認
                    if voice_client.is_connected():
                        await voice_client.disconnect()
                        
                        # テキストチャンネルに通知メッセージを送信する
                        await self._send_disconnect_notification(voice_client)
                        
            except Exception as e:
                print(f"ボイス状態更新処理中にエラーが発生しました: {e}")
    
    async def _send_disconnect_notification(self, voice_client):
        """自動切断の通知メッセージを送信する"""
        last_interaction_channel = getattr(voice_client, "last_interaction_channel", None)
        if last_interaction_channel:
            try:
                await last_interaction_channel.send("ボイスチャンネルに誰もいなくなったため、自動的に切断しました。")
            except discord.errors.Forbidden:
                print("自動切断メッセージの送信に失敗しました（権限不足）。")
            except discord.errors.HTTPException as e:
                print(f"自動切断メッセージ送信中にHTTPエラー: {e}")
            except Exception as e:
                print(f"自動切断メッセージ送信中に予期せぬエラー: {e}") 