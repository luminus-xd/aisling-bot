# つむぎ - Discord AI Bot

日本語を話すDiscord Bot。AI会話、音声読み上げ、音楽検索機能を提供します。

## 機能

- **AI会話**: Google Gemini APIを使用した自然な日本語会話
- **音声読み上げ**: VoiceVoxによる日本語音声合成
- **音楽検索**: Spotify APIを使用した楽曲検索
- **YouTube要約**: YouTube動画の内容を要約

## コマンド

| コマンド | 説明 |
|----------|------|
| `/ask [質問]` | AIに質問（音声読み上げ付き） |
| `/join` | ボイスチャンネルに参加 |
| `/leave` | ボイスチャンネルから退出 |
| `/speak [テキスト]` | テキストを音声で読み上げ |
| `/search_spotify [検索語]` | Spotifyで楽曲検索 |
| `/youtube_summarize [URL]` | YouTube動画を要約 |

## セットアップ

### 必要なもの

- Discord Bot Token
- Google Gemini API Key
- VoiceVoxモデルファイル（`.vvm`）
- Spotify Client ID/Secret（オプション）

### 環境変数

```env
DISCORD_BOT_TOKEN=your_discord_token
GEMINI_API_KEY=your_gemini_key
VOICEVOX_MODEL_ID=0
VOICEVOX_STYLE_ID=8
SPOTIPY_CLIENT_ID=your_spotify_id
SPOTIPY_CLIENT_SECRET=your_spotify_secret
```

### Docker実行

```bash
# ビルド
docker build -t tsumugi-bot .

# 実行
docker run --env-file .env tsumugi-bot
```

### ローカル開発

```bash
# 依存関係インストール
pip install -r requirements.txt

# 実行
python main.py
```

## Bot権限設定

Discord Developer Portalで以下の権限を設定：

**OAuth2 Scopes:**
- `bot`
- `applications.commands`

**Bot Permissions:**
- Send Messages
- Embed Links
- Connect
- Speak

## 注意事項

- VoiceVoxモデルファイルは`voicevox_files/models/`に配置
- APIキーは`.env`ファイルで管理（`.gitignore`に追加済み）
- スラッシュコマンドの反映には数分かかる場合があります

## キャラクター

「つむぎ」は埼玉県出身の高校生という設定で、親しみやすい関西弁で話します。

## クレジット

- **音声合成**: [VOICEVOX: 春日部つむぎ](https://voicevox.hiroshiba.jp/)