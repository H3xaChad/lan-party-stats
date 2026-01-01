# LAN Party Stats Bot

Discord bot that tracks game playtime and Spotify listening statistics.

## Quick Start

```bash
make install    # Install dependencies and create .env
# Edit .env and add your DISCORD_TOKEN
make run        # Start the bot
```

## Discord Bot Setup

1. Create bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Copy bot token to `.env`
3. Enable **Privileged Gateway Intents**:
   - PRESENCE INTENT (required)
   - SERVER MEMBERS INTENT (required)
4. Invite bot with `bot` and `applications.commands` scopes

## Commands

- `/stats [user]` - Gaming statistics
- `/leaderboard` - Top players
- `/topgames` - Most played games
- `/game <name>` - Game details
- `/spotify [user]` - Spotify stats
- `/topsongs` - Top tracks
- `/overview` - Server overview

## Database

SQLite with session-based tracking:
- `users` - User information
- `games` - Game catalog
- `spotify_tracks` - Track catalog
- `game_sessions` - Gaming sessions with timestamps
- `spotify_sessions` - Listening sessions with timestamps

Optimized with indexes for fast queries. View with: `sqlite3 stats.db`

## Configuration

`.env` file:
```env
DISCORD_TOKEN=your_token_here
DATABASE_PATH=stats.db
```

## Troubleshooting

- **Bot doesn't track activities**: Enable PRESENCE INTENT in Discord Portal
- **Commands not showing**: Wait 1-2 minutes for Discord to sync
- **Database errors**: Check write permissions and disk space
