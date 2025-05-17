# Gemini & VoiceVox Discord Bot

このBotは、Discord上でGemini APIを利用して質問応答を行い、`voicevox_core` ライブラリを利用してその応答を音声で読み上げることを目的としたPython製のBotです。
KoyebなどのDockerベースのプラットフォームへのデプロイを想定しています。

## 特徴

-   DiscordのチャットでBotにスラッシュコマンドを使って指示できます。
-   Gemini APIを利用して、質問に対する回答を生成します。
-   Geminiの回答を `voicevox_core` を利用して音声で読み上げます。

## 必要なもの

-   Python 3.8以上 (Dockerfileでは3.10-slimを使用)
-   Discord Botトークン
-   Gemini APIキー
-   `ffmpeg` (音声再生に必要。Dockerfileに含まれます)
-   **VoiceVoxモデルファイル (`.vvm`)** (Open JTalk辞書はDockerfile内で自動ダウンロードされます)

## セットアップ手順

1.  **リポジトリをクローンします（もしGit管理する場合）：**
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

3.  **Pythonの仮想環境を作成し、アクティベートします（ローカルテスト用、推奨）：**
    ```bash
    python -m venv venv
    # Windowsの場合
    # .\venv\Scripts\activate
    # macOS/Linuxの場合
    source venv/bin/activate
    ```

4.  **必要なライブラリをインストールします（ローカルテスト用）：**
    ```bash
    pip install -r requirements.txt
    ```
    ローカル環境でテストする場合、`ffmpeg` が別途必要です。OSに合わせてインストールしてください。
    (例: `brew install ffmpeg` on macOS, `sudo apt install ffmpeg` on Debian/Ubuntu)

5.  **設定ファイルを作成します（ローカルテスト用）：**
    プロジェクトのルートディレクトリに `.env` という名前のファイルを作成し、以下の内容を記述して、ご自身のAPIキーなどに置き換えてください。
    Koyebにデプロイする際は、これらの値をKoyebの環境変数として設定します。

    ```env
    DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
    VOICEVOX_MODEL_ID="0" # VoiceVoxのモデルID (voicevox_files/models/ 内のファイル名 0.vvm, 1.vvm などと一致させる)
    VOICEVOX_STYLE_ID=8   # VoiceVoxのスタイルID (例: ノーマルスタイル)
    ```

    -   `DISCORD_BOT_TOKEN`: あなたのDiscord Botのトークン。
    -   `GEMINI_API_KEY`: あなたのGemini APIキー。
    -   `VOICEVOX_MODEL_ID`: 使用するVoiceVoxのモデルID。`voicevox_files/models/` ディレクトリに配置したモデルファイル名 (`<ID>.vvm`) の `<ID>` と一致させてください。
    -   `VOICEVOX_STYLE_ID`: 使用するVoiceVoxのスタイルID。モデルに対応するスタイルIDを指定してください。

## Botの実行 (ローカルでのDocker実行例)

1.  **Dockerイメージをビルドします:**
    ```bash
    docker build -t my-discord-bot .
    ```

2.  **Dockerコンテナを実行します (環境変数を渡して):**
    ```bash
    docker run --env-file .env my-discord-bot
    ```
    または、個別に環境変数を指定する場合:
    ```bash
    docker run -e DISCORD_BOT_TOKEN="your_token" -e GEMINI_API_KEY="your_key" -e VOICEVOX_MODEL_ID="0" -e VOICEVOX_STYLE_ID="8" my-discord-bot
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
6.  デプロイが完了すると、Botが起動します。

## コマンド一覧 (スラッシュコマンド)

-   `/hello`: Botが挨拶を返します。
-   `/join`: Botをあなたのいるボイスチャンネルに参加させます。
-   `/leave`: Botをボイスチャンネルから切断します。
-   `/speak [text_to_speak]`: 指定されたテキストを読み上げます。
    -   `text_to_speak` (必須): 読み上げる内容。
-   `/ask [query]`: Geminiに質問し、テキストと音声で回答を得ます。
    -   `query` (必須): Geminiへの質問内容。

## 注意事項

-   APIキーは機密情報ですので、取り扱いに注意してください。`.env` ファイルをGitリポジトリにコミットしないように、`.gitignore` ファイルに `.env` を追加することを強く推奨します。
-   Botを初めてサーバーに追加した際や、コマンドの定義を変更した直後は、スラッシュコマンドがDiscordに反映されるまで少し時間がかかることがあります。
-   Discord Botの権限設定で、(もし `intents.message_content` を有効にしている場合は)「メッセージコンテンツの読み取り」が有効になっていることを確認してください。スラッシュコマンドのみの場合は通常不要です。 