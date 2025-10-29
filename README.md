# Discord Bot 908 🤖

A professional Discord bot with music, games, and interactive features. This bot includes a fully functional music system with skip command fixes, interactive games, and comprehensive moderation tools.

## ✨ Features

### 🎵 Music System
- **High-quality audio streaming** using Wavelink and Lavalink
- **Multi-source support**: YouTube, Spotify, SoundCloud, and more
- **Interactive music controls** with buttons and slash commands
- **Queue management** with shuffle, loop, and skip functionality
- **Real-time progress tracking** with auto-updating embeds
- **Volume control** and audio effects

### 🎮 Interactive Games
- **Tic-Tac-Toe**: Play against other users or the bot
- **Blackjack**: Full casino-style blackjack with betting
- **Football Game**: Interactive football simulation

### 🛠️ General Commands
- **Server information** and user profiles
- **Moderation tools** and utilities
- **Custom embed messages**
- **Comprehensive logging system**

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Discord Bot Token
- Lavalink server (for music functionality)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kwgdbeksb/bot908.git
   cd bot908
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   APP_ID=your_application_id
   OWNER_ID=your_discord_user_id
   GUILD_ID=your_test_server_id  # Optional, for development
   SYNC_GLOBAL=false  # Set to true for production
   
   # Lavalink Configuration
   LAVALINK_HOST=localhost
   LAVALINK_PORT=2333
   LAVALINK_PASSWORD=youshallnotpass
   ```

4. **Start Lavalink server**
   - Download Lavalink.jar from the official repository
   - Configure `application.yml` for Lavalink
   - Run: `java -jar Lavalink.jar`

5. **Run the bot**
   ```bash
   python src/bot.py
   ```

## 📋 Commands

### Music Commands
- `/play <query>` - Play a song from various sources
- `/pause` - Pause the current song
- `/resume` - Resume playback
- `/skip` - Skip the current song (fixed implementation)
- `/stop` - Stop music and clear queue
- `/queue` - Show the current queue
- `/volume <0-100>` - Set playback volume
- `/shuffle` - Shuffle the queue
- `/nowplaying` - Show current song info

### Game Commands
- `/tictactoe @user` - Start a tic-tac-toe game
- `/blackjack` - Play blackjack
- `/football` - Start football simulation

### General Commands
- `/ping` - Check bot latency
- `/serverinfo` - Display server information
- `/userinfo @user` - Show user profile

## 🔧 Configuration

The bot uses a flexible configuration system that supports both environment variables and `.env` files. Key configuration options:

- **SYNC_GLOBAL**: Set to `true` for global command sync (production)
- **GUILD_ID**: Specify a guild ID for faster development testing
- **Lavalink settings**: Configure your Lavalink server connection

## 🎯 Recent Fixes

### Skip Command Improvements
- ✅ Fixed validation logic from `not player.playing` to `not player.current`
- ✅ Added comprehensive error handling with try-catch blocks
- ✅ Standardized error messages between slash commands and button interactions
- ✅ Improved user feedback for various skip scenarios

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or need help:
1. Check the logs for error messages
2. Ensure all dependencies are installed
3. Verify your environment configuration
4. Make sure Lavalink is running for music features

## 🔗 Links

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Wavelink Documentation](https://wavelink.dev/)
- [Lavalink](https://github.com/freyacodes/Lavalink)

---

Made with ❤️ for the Discord community