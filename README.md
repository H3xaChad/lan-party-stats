# LAN Party Stats

Discord bot that tracks gaming and Spotify activity with a web dashboard.

## Setup

1. **Create Discord Bot** at [Discord Developer Portal](https://discord.com/developers/applications)
   - Enable **Privileged Gateway Intents**: `PRESENCE` and `SERVER MEMBERS`
   - Copy bot token

2. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your `DISCORD_TOKEN` and `DISCORD_GUILD_ID`
   
   _Note: without guild id data will be gathered from ALL servers the bot is on!_

3. **Invite Bot** to your server with permissions: `bot` + `applications.commands`

## Running

### Native (uv)

Install dependencies:
```bash
uv sync --extra web
```

Start Discord bot:
```bash
uv run python main.py
```

Start web dashboard:
```bash
uv run python web_main.py
```

### Docker

Build containers:
```bash
docker compose build
```

Start services:
```bash
docker compose up -d
```

View logs:
```bash
docker compose logs -f
```

Stop services:
```bash
docker compose down
```

Clean up (remove volumes and images):
```bash
docker compose down -v --rmi local
```

## Configuration

Required in `.env`:
- `DISCORD_TOKEN` - Bot token from Discord Developer Portal
- `DISCORD_GUILD_ID` - Server ID to monitor (right-click server → Copy ID)

Optional:
- `DATABASE_PATH` - Database file location (default: `stats.db`)
- `WEB_PORT` - Web dashboard port (default: `5000`)

## Commands

- `/stats [user]` - View gaming stats
- `/leaderboard` - Top players
- `/game <name>` - Game details
- `/spotify [user]` - Spotify listening stats
- `/overview` - Server overview

## License

MIT
