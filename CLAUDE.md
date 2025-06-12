# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Install dependencies (local testing)
pip install -r requirements.txt

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate   # Windows

# Run the bot locally (requires .env file)
python main.py
```

### Docker Development
```bash
# Build Docker image
docker build -t my-discord-bot .

# Run with environment file
docker run --env-file .env my-discord-bot

# Run with individual environment variables
docker run \
  -e DISCORD_BOT_TOKEN="your_token" \
  -e GEMINI_API_KEY="your_key" \
  -e VOICEVOX_MODEL_ID="0" \
  -e VOICEVOX_STYLE_ID="8" \
  -e SPOTIPY_CLIENT_ID="your_spotify_client_id" \
  -e SPOTIPY_CLIENT_SECRET="your_spotify_client_secret" \
  my-discord-bot
```

## Architecture Overview

This is a Japanese Discord bot ("つむぎ") that integrates three main services:
- **Discord.py**: Slash command interface
- **Google Gemini API**: AI-powered chat responses with custom personality
- **VoiceVox**: Japanese text-to-speech synthesis
- **Spotify API**: Music search functionality

### Core Components

**Main Entry Point (`main.py`)**:
- Initializes Discord client with voice state intents
- Sets up command tree and synchronizes slash commands globally
- Coordinates all handlers and cogs

**Handler Architecture (`modules/`)**:
- `VoiceVoxHandler`: Manages Japanese TTS synthesis using voicevox_core
- `GeminiHandler`: Handles AI responses with character personality from config.py
- `BotEventHandler`: Manages Discord events (voice state changes, auto-disconnect)

**Command Structure (`modules/bot_commands.py` + `cogs/`)**:
- Commands organized into Cogs: BasicCommands, VoiceCommands, AICommands
- SpotifyCog in separate file for music search
- All commands registered to command tree, not as traditional discord.py cogs

**Character Configuration (`config.py`)**:
- Defines "つむぎ" character personality for Gemini responses
- Japanese high school girl persona with埼玉県 (Saitama) background
- Specific speaking style: casual but polite, 80-character response limit

### Key Integration Points

**Voice Integration**:
- Bot joins voice channels via `/join` command
- AI responses from `/ask` are automatically spoken if bot is in voice channel
- Responses split into segments for better TTS processing

**Error Handling**:
- VoiceVox initialization checks for model files in `/app/voicevox_files/models/`
- Gemini API fallbacks for blocked content
- Discord permission validation for voice features

**Environment Dependencies**:
- `DISCORD_BOT_TOKEN`: Discord bot authentication
- `GEMINI_API_KEY`: Google AI API access
- `VOICEVOX_MODEL_ID`/`VOICEVOX_STYLE_ID`: Voice model configuration
- `SPOTIPY_CLIENT_ID`/`SPOTIPY_CLIENT_SECRET`: Spotify API access

### VoiceVox Setup Requirements

VoiceVox models (`.vvm` files) must be placed in `voicevox_files/models/` directory. The Docker container automatically downloads Open JTalk dictionary and appropriate ONNX Runtime for the target architecture (x86_64/aarch64).

### Deployment

Designed for Docker-based deployment platforms like Koyeb. The Dockerfile handles:
- Architecture-specific VoiceVox core installation
- ONNX Runtime setup for voice synthesis  
- Open JTalk dictionary download
- ffmpeg installation for Discord voice

## Git Workflow

Follow conventional commits format specified in `.cursor/rules/git.mdc`:
- `feat:` for new features
- `fix:` for bug fixes  
- `docs:` for documentation changes
- Use GitHub CLI for PR creation with proper analysis of all changes