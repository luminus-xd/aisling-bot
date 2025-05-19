import discord

class BotEventHandler:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        
    async def setup_event_handlers(self):
        """ボットのイベントハンドラを設定する"""
        # on_readyイベントはmain.pyで処理する必要があるため、ここでは他のイベントのみ設定
        self.bot.event(self.on_voice_state_update)
        
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """ボイスチャンネルの状態が変化したときに呼び出されるイベント"""
        # Bot自身の状態変化は無視
        if member.id == self.bot.user.id:
            return

        voice_client = member.guild.voice_client
        if voice_client and voice_client.is_connected():
            # Botが接続しているチャンネルを取得
            connected_channel = voice_client.channel
            
            # チャンネルにBot以外のユーザーが残っているか確認
            # Bot以外のメンバーのリストを作成
            human_members = [m for m in connected_channel.members if not m.bot]
            
            if not human_members:  # Botしか残っていない場合
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