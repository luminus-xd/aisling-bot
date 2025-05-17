FROM python:3.10-bookworm

# システムのタイムゾーンを設定 (任意)
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Rustのインストールとビルドに必要なツールのインストール
# (curl, build-essential, libssl-dev, pkg-config はRustのビルドや一部Pythonパッケージのビルドに役立つ)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    tar \
    curl \
    build-essential \
    libssl-dev \
    pkg-config \
    unzip \
    # Rustのインストール
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    # PATHにCargo（Rustのパッケージマネージャ）を追加
    # && . "$HOME/.cargo/env" # この行はRUN命令内でのみ有効。永続化はENVで行う
    # 後続のpip installでRustコンパイラが使えるようにする
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 環境変数にCargoのパスを通す (RUN命令を跨いで永続化するため)
# Dockerのデフォルトユーザーはrootなので、$HOMEは/rootになることが多い
ENV PATH="/root/.cargo/bin:${PATH}"

# 作業ディレクトリの設定
WORKDIR /app

# VoiceVoxモデルファイルのコピー
# voicevox_files/models ディレクトリがプロジェクトルートにあることを前提とします
COPY voicevox_files/models/ /app/voicevox_files/models/

# wheelsディレクトリは使用せず、必要時にダウンロードする方式に変更

# Open JTalk辞書のダウンロードと展開
ENV OPENJTALK_DIC_VERSION=1.11
ENV OPENJTALK_DIC_FILENAME=open_jtalk_dic_utf_8-${OPENJTALK_DIC_VERSION}.tar.gz
ENV OPENJTALK_DIC_DOWNLOAD_URL=http://downloads.sourceforge.net/open-jtalk/${OPENJTALK_DIC_FILENAME}

RUN mkdir -p /app/voicevox_files/open_jtalk_dic \
    && cd /tmp \
    && wget -q ${OPENJTALK_DIC_DOWNLOAD_URL} \
    && tar xzf ${OPENJTALK_DIC_FILENAME} -C /app/voicevox_files/open_jtalk_dic --strip-components=1 \
    && rm ${OPENJTALK_DIC_FILENAME}

# VoiceVox Core wheelファイルの変数定義
ENV VOICEVOX_CORE_VERSION=0.16.0
ENV VOICEVOX_CORE_WHEEL=voicevox_core-${VOICEVOX_CORE_VERSION}-cp310-abi3-manylinux_2_34_x86_64.whl
ENV VOICEVOX_CORE_URL=https://github.com/VOICEVOX/voicevox_core/releases/download/${VOICEVOX_CORE_VERSION}/${VOICEVOX_CORE_WHEEL}

# requirements.txt をコピーして依存関係をインストール
COPY requirements.txt .

# アーキテクチャ検出と適切なwheelファイルのインストール
RUN ARCH=$(uname -m) \
    && echo "検出されたアーキテクチャ: ${ARCH}" \
    # VOICEVOX_CORE_WHEEL と VOICEVOX_ONNXRUNTIME_TGZ の設定
    && ONNXRUNTIME_VERSION="1.17.3" \
    && if [ "${ARCH}" = "x86_64" ]; then \
    VOICEVOX_CORE_WHEEL="voicevox_core-${VOICEVOX_CORE_VERSION}-cp310-abi3-manylinux_2_34_x86_64.whl"; \
    VOICEVOX_ONNXRUNTIME_TGZ="voicevox_onnxruntime-linux-x64-${ONNXRUNTIME_VERSION}.tgz"; \
    VOICEVOX_ONNXRUNTIME_EXTRACTED_DIR_NAME="voicevox_onnxruntime-linux-x64-${ONNXRUNTIME_VERSION}"; \
    elif [ "${ARCH}" = "aarch64" ]; then \
    VOICEVOX_CORE_WHEEL="voicevox_core-${VOICEVOX_CORE_VERSION}-cp310-abi3-manylinux_2_34_aarch64.whl"; \
    VOICEVOX_ONNXRUNTIME_TGZ="voicevox_onnxruntime-linux-arm64-${ONNXRUNTIME_VERSION}.tgz"; \
    VOICEVOX_ONNXRUNTIME_EXTRACTED_DIR_NAME="voicevox_onnxruntime-linux-arm64-${ONNXRUNTIME_VERSION}"; \
    else \
    echo "サポートされていないアーキテクチャ: ${ARCH}"; \
    exit 1; \
    fi \
    && VOICEVOX_CORE_URL="https://github.com/VOICEVOX/voicevox_core/releases/download/${VOICEVOX_CORE_VERSION}/${VOICEVOX_CORE_WHEEL}" \
    && VOICEVOX_ONNXRUNTIME_URL="https://github.com/VOICEVOX/onnxruntime-builder/releases/download/voicevox_onnxruntime-${ONNXRUNTIME_VERSION}/${VOICEVOX_ONNXRUNTIME_TGZ}" \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    # VOICEVOX提供のONNXRuntimeをインストール
    && cd /tmp \
    && wget -q "${VOICEVOX_ONNXRUNTIME_URL}" \
    && tar xzf "${VOICEVOX_ONNXRUNTIME_TGZ}" \
    && SO_FILE="libvoicevox_onnxruntime.so.${ONNXRUNTIME_VERSION}" \
    # VOICEVOX_ONNXRUNTIME_EXTRACTED_DIR_NAME は使用せず、カレントディレクトリ以下を検索
    && EXTRACTED_SO_PATH=$(find . -name "${SO_FILE}" -type f -print -quit) \
    && if [ -z "${EXTRACTED_SO_PATH}" ]; then echo "Error: ${SO_FILE} not found after extraction in /tmp. Files: $(ls -R)"; exit 1; fi \
    && cp "${EXTRACTED_SO_PATH}" "/usr/local/lib/" \
    && ln -sf "/usr/local/lib/${SO_FILE}" "/usr/local/lib/libvoicevox_onnxruntime.so" \
    && ldconfig \
    && rm "${VOICEVOX_ONNXRUNTIME_TGZ}" \
    # find で見つかったパスのディレクトリ部分を削除 (例: ./onnxruntime-linux-x64-1.17.3/lib/libonnxruntime.so.1.17.3 -> ./onnxruntime-linux-x64-1.17.3 を削除) \
    && rm -rf "$(dirname "$(dirname "${EXTRACTED_SO_PATH}")")" \
    && cd /app \
    && wget -q ${VOICEVOX_CORE_URL} \
    && pip install ${VOICEVOX_CORE_WHEEL} \
    && rm ${VOICEVOX_CORE_WHEEL} \
    && if [ ! -f "/usr/local/lib/python3.10/site-packages/voicevox_core/_rust.abi3.so" ]; then \
    echo "ERROR: _rust.abi3.so NOT FOUND after install!"; \
    exit 1; \
    fi

# アプリケーションコードをコピー
COPY . .

# ポートの公開 (Botの種類によっては不要)
# EXPOSE 8080 

# Botの起動コマンド
CMD ["python", "main.py"] 