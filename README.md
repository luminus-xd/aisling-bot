# Gemini & VoiceVox Discord Bot

このBotは、Discord上でGemini APIを利用して質問応答を行い、`voicevox_core` ライブラリを利用してその応答を音声で読み上げることを目的としたPython製のBotです。
KoyebなどのDockerベースのプラットフォームへのデプロイを想定しています。

## 特徴

-   DiscordのチャットでBotにスラッシュコマンドを使って指示できます。
-   Gemini APIを利用して、質問に対する回答を生成します。
-   Geminiの回答を `voicevox_core` を利用して音声で読み上げます。

## 必要なもの

-   Python 3.8以上 (Dockerfileでは `python:3.10-bookworm` を使用)
-   Discord Botトークン
-   Gemini APIキー
-   `ffmpeg` (音声再生に必要。Dockerfileに含まれます)
-   **VoiceVoxモデルファイル (`.vvm`)** (Open JTalk辞書はDockerfile内で自動ダウンロードされます)
-   **Spotify APIキー (オプション)**: Spotify検索機能を使用する場合に必要です。
    -   `SPOTIPY_CLIENT_ID`
    -   `SPOTIPY_CLIENT_SECRET`

## Botの権限とスコープ

BotをDiscordサーバーに導入する際には、以下のOAuth2スコープとBot権限を設定してください。

### OAuth2スコープ

-   `bot`: Botとしてサーバーに参加するために必須です。
-   `applications.commands`: スラッシュコマンドを登録・利用するために必須です。

### Bot権限 (インテント)

Botの動作には以下の権限が必要です。Bot招待URL生成時にこれらの権限を選択してください。

-   **必須の権限:**
    -   `Send Messages` / `メッセージを送信`: テキストチャンネルでの応答に必要です。
    -   `Embed Links` / `埋め込みリンク`: 検索結果などの情報をきれいに表示するために使用します。
    -   `Connect` / `接続`: ボイスチャンネルへの接続に必要です。
    -   `Speak` / `発言`: ボイスチャンネルでの音声読み上げに必要です。
-   **推奨される権限 (特定の機能に必要):**
    -   `Read Message History` / `メッセージ履歴を読む`: Botが過去のメッセージをコンテキストとして利用する場合。 (現在の基本的なスラッシュコマンドのみの場合は必須ではないことが多いです)
    -   `Use External Emojis` / `外部の絵文字の使用`: カスタム絵文字を使用する場合。

**インテントの設定:**
Botのコード (`main.py`) で必要なインテントが有効になっていることを確認してください。特に `intents.voice_states = True` はボイスチャンネル関連の機能に不可欠です。

## セットアップ手順

1.  **リポジトリをクローンします (任意):**
    ```bash
    git clone <リポジトリのURL>
    cd <リポジトリ名>
    ```

2.  **VoiceVoxモデルファイルを配置します:**
    プロジェクトのルートディレクトリに `voicevox_files/models/` ディレクトリを作成し、その中に使用したい話者のVoiceVoxモデルファイル (`.vvm`) を配置します。
    Open JTalk辞書は `Dockerfile` によってビルド時に自動的にダウンロード・展開されますので、手動で配置する必要はありません。

    ```
    your-bot-project/
    ├── voicevox_files/
    │   └── models/            <-- この中に .vvm ファイルを配置
    │       ├── 0.vvm      (例: VOICEVOX_MODEL_ID が "0" の場合)
    │       └── ...
    ├── main.py
    ├── requirements.txt
    ├── Dockerfile
    └── ... (その他のファイル)
    ```
    -   VoiceVoxモデルファイル (`.vvm`) は、[VOICEVOX公式サイトのキャラクターページ](https://voicevox.hiroshiba.jp/)などから入手してください。使用する`voicevox_core`のバージョンと互換性のあるモデルを選択してください。

3.  **Pythonの仮想環境を作成し、アクティベートします (ローカルテスト用、推奨):**
    ```bash
    python -m venv venv
    ```
    Windowsの場合:
    ```bash
    .\\venv\\Scripts\\activate
    ```
    macOS/Linuxの場合:
    ```bash
    source venv/bin/activate
    ```

4.  **必要なライブラリをインストールします (ローカルテスト用):**
    ```bash
    pip install -r requirements.txt
    ```
    ローカル環境でテストする場合、`ffmpeg` が別途必要です。OSに合わせてインストールしてください。
    (例: macOSでは `brew install ffmpeg`, Debian/Ubuntuでは `sudo apt install ffmpeg`)

5.  **設定ファイルを作成します (ローカルテスト用):**
    > [!IMPORTANT]
    > Botを正常に動作させるためには、これらの環境変数を正しく設定することが不可欠です。特にAPIキーやトークンが間違っていると、関連する機能が一切利用できません。

    プロジェクトのルートディレクトリに `.env` という名前のファイルを作成し、以下の内容を記述して、ご自身のAPIキーなどに置き換えてください。
    Koyebにデプロイする際は、これらの値をKoyebの環境変数として設定します。

    ```env
    DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
    VOICEVOX_MODEL_ID="0" # VoiceVoxのモデルID (voicevox_files/models/ 内のファイル名 0.vvm, 1.vvm などと一致させる)
    VOICEVOX_STYLE_ID=8   # VoiceVoxのスタイルID (例: ノーマルスタイル)
    SPOTIPY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID_HERE
    SPOTIPY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET_HERE
    ```

    -   `DISCORD_BOT_TOKEN`: あなたのDiscord Botのトークン。
    -   `GEMINI_API_KEY`: あなたのGemini APIキー。
    -   `VOICEVOX_MODEL_ID`: 使用するVoiceVoxのモデルID。`voicevox_files/models/` ディレクトリに配置したモデルファイル名 (`<ID>.vvm`) の `<ID>` と一致させてください。
    -   `VOICEVOX_STYLE_ID`: 使用するVoiceVoxのスタイルID。モデルに対応するスタイルIDを指定してください。
    -   `SPOTIPY_CLIENT_ID`: あなたのSpotifyアプリケーションのClient ID (Spotify検索機能を使用する場合)。
    -   `SPOTIPY_CLIENT_SECRET`: あなたのSpotifyアプリケーションのClient Secret (Spotify検索機能を使用する場合)。

## Botの実行 (ローカルでのDocker実行例)

1.  **Dockerイメージをビルドします:**
    ```bash
    docker build -t my-discord-bot .
    ```

2.  **Dockerコンテナを実行します (環境変数を渡して):**
    `.env` ファイルを使用する場合:
    ```bash
    docker run --env-file .env my-discord-bot
    ```
    または、個別に環境変数を指定する場合:
    ```bash
    docker run \\
      -e DISCORD_BOT_TOKEN="your_token" \\
      -e GEMINI_API_KEY="your_key" \\
      -e VOICEVOX_MODEL_ID="0" \\
      -e VOICEVOX_STYLE_ID="8" \\
      -e SPOTIPY_CLIENT_ID="your_spotify_client_id" \\
      -e SPOTIPY_CLIENT_SECRET="your_spotify_client_secret" \\
      my-discord-bot
    ```

## Koyebへのデプロイ

1.  このリポジトリをGitHubなどにプッシュします。
2.  Koyebのコントロールパネルで新しいAppを作成し、デプロイ方法として「Git」を選択します。
3.  リポジトリとブランチを指定します。
4.  Koyebは自動的に`Dockerfile`を検出し、ビルドプロセスを開始します。
5.  **環境変数を設定します**: Koyebのサービス設定で、以下の環境変数を設定してください:
    -   `DISCORD_BOT_TOKEN`
    -   `GEMINI_API_KEY`
    -   `VOICEVOX_MODEL_ID` (例: `"0"`)
    -   `VOICEVOX_STYLE_ID` (例: `8`)
    -   `SPOTIPY_CLIENT_ID` (Spotify検索機能を使用する場合)
    -   `SPOTIPY_CLIENT_SECRET` (Spotify検索機能を使用する場合)
6.  デプロイが完了すると、Botが起動します。

## コマンド一覧 (スラッシュコマンド)

-   `/hello`: Botが挨拶を返します。
-   `/join`: Botをあなたのいるボイスチャンネルに参加させます。
-   `/leave`: Botをボイスチャンネルから切断します。
-   `/speak [text_to_speak]`: 指定されたテキストを読み上げます。
    -   `text_to_speak` (必須): 読み上げる内容。
-   `/ask [query]`: Geminiに質問し、テキストと音声で回答を得ます。
    -   `query` (必須): Geminiへの質問内容。
-   `/search_spotify [query]`: Spotifyで曲を検索します。
    -   `query` (必須): 検索する曲名やアーティスト名。

## 注意事項

> [!WARNING]
> APIキーやBotトークンは非常に重要な機密情報です。これらの情報が漏洩すると、悪意のある第三者によって不正利用される可能性があります。
> - `.env` ファイルをGitリポジトリに絶対にコミットしないでください。プロジェクトの `.gitignore` ファイルに `.env` が含まれていることを確認してください。
> - Publicなリポジトリで開発する場合、フォークされた際にも環境変数の内容が公開されないよう注意してください。
> - APIキーの取り扱いには最大限の注意を払い、必要最小限の権限のみを付与するようにしてください。

> [!NOTE]
> Botを初めてサーバーに追加した際や、コマンドの定義を変更 (追加/削除/修正) した直後は、スラッシュコマンドがDiscordクライアントに反映されるまで数分から数十分程度かかることがあります。すぐにコマンドが表示されない場合は、しばらく時間をおいてから再度確認してみてください。

- APIキーは機密情報ですので、取り扱いに注意してください。`.env` ファイルをGitリポジトリにコミットしないように、`.gitignore` ファイルに `.env` を追加することを強く推奨します。
- Botを初めてサーバーに追加した際や、コマンドの定義を変更した直後は、スラッシュコマンドがDiscordに反映されるまで少し時間がかかることがあります。
- Discord Botの権限設定で、(もし `intents.message_content` を有効にしている場合は)「メッセージコンテンツの読み取り」が有効になっていることを確認してください。スラッシュコマンドのみの場合は通常不要です。 