"""Database module for LAN Party Stats Bot."""

import aiosqlite
from typing import Optional, List, Tuple


class Database:
    """SQLite database manager with async support."""
    
    def __init__(self, db_path: str = "stats.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Connect to database and initialize schema."""
        self._connection = await aiosqlite.connect(self.db_path)
        await self._initialize_schema()
    
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
    
    async def _initialize_schema(self):
        """Create tables and indexes."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    avatar_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_name TEXT UNIQUE NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS spotify_tracks (
                    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(title, artist)
                )
            """)
            
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (game_id) REFERENCES games(game_id)
                )
            """)
            
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS spotify_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (track_id) REFERENCES spotify_tracks(track_id)
                )
            """)
            
            # Indexes for performance
            for idx_query in [
                "CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_game_sessions_game ON game_sessions(game_id)",
                "CREATE INDEX IF NOT EXISTS idx_game_sessions_time ON game_sessions(start_time, end_time)",
                "CREATE INDEX IF NOT EXISTS idx_spotify_sessions_user ON spotify_sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_spotify_sessions_track ON spotify_sessions(track_id)",
                "CREATE INDEX IF NOT EXISTS idx_spotify_sessions_time ON spotify_sessions(start_time, end_time)",
            ]:
                await cursor.execute(idx_query)
            
            await self._connection.commit()
    
    async def upsert_user(self, user_id: int, username: str, display_name: str = None, avatar_url: str = None):
        """Insert or update user."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO users (user_id, username, display_name, avatar_url, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    display_name = excluded.display_name,
                    avatar_url = excluded.avatar_url,
                    last_updated = CURRENT_TIMESTAMP
            """, (user_id, username, display_name, avatar_url))
            await self._connection.commit()
    
    async def get_user(self, user_id: int) -> Optional[Tuple]:
        """Get user information."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("SELECT user_id, username, display_name, avatar_url, last_updated FROM users WHERE user_id = ?", (user_id,))
            return await cursor.fetchone()
    
    async def get_or_create_game(self, game_name: str) -> int:
        """Get or create game, return game_id."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("INSERT OR IGNORE INTO games (game_name) VALUES (?)", (game_name,))
            await cursor.execute("SELECT game_id FROM games WHERE game_name = ?", (game_name,))
            result = await cursor.fetchone()
            await self._connection.commit()
            return result[0]
    
    async def get_or_create_track(self, title: str, artist: str, album: str = None) -> int:
        """Get or create Spotify track, return track_id."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("INSERT OR IGNORE INTO spotify_tracks (title, artist, album) VALUES (?, ?, ?)", (title, artist, album))
            await cursor.execute("SELECT track_id FROM spotify_tracks WHERE title = ? AND artist = ?", (title, artist))
            result = await cursor.fetchone()
            await self._connection.commit()
            return result[0]
    
    async def start_game_session(self, user_id: int, game_name: str) -> int:
        """Start new game session."""
        game_id = await self.get_or_create_game(game_name)
        async with self._connection.cursor() as cursor:
            await cursor.execute("INSERT INTO game_sessions (user_id, game_id, start_time) VALUES (?, ?, CURRENT_TIMESTAMP)", (user_id, game_id))
            await self._connection.commit()
            return cursor.lastrowid
    
    async def end_game_session(self, session_id: int):
        """End game session and calculate duration."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE game_sessions
                SET end_time = CURRENT_TIMESTAMP,
                    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
                WHERE session_id = ?
            """, (session_id,))
            await self._connection.commit()
    
    async def get_active_game_session(self, user_id: int) -> Optional[Tuple]:
        """Get active game session for user."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                SELECT gs.session_id, g.game_name, gs.start_time
                FROM game_sessions gs
                JOIN games g ON gs.game_id = g.game_id
                WHERE gs.user_id = ? AND gs.end_time IS NULL
                ORDER BY gs.start_time DESC LIMIT 1
            """, (user_id,))
            return await cursor.fetchone()
    
    async def start_spotify_session(self, user_id: int, title: str, artist: str, album: str = None) -> int:
        """Start new Spotify session."""
        track_id = await self.get_or_create_track(title, artist, album)
        async with self._connection.cursor() as cursor:
            await cursor.execute("INSERT INTO spotify_sessions (user_id, track_id, start_time) VALUES (?, ?, CURRENT_TIMESTAMP)", (user_id, track_id))
            await self._connection.commit()
            return cursor.lastrowid
    
    async def end_spotify_session(self, session_id: int):
        """End Spotify session and calculate duration."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE spotify_sessions
                SET end_time = CURRENT_TIMESTAMP,
                    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
                WHERE session_id = ?
            """, (session_id,))
            await self._connection.commit()
    
    async def get_active_spotify_session(self, user_id: int) -> Optional[Tuple]:
        """Get active Spotify session for user."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                SELECT ss.session_id, st.title, st.artist, st.album, ss.start_time
                FROM spotify_sessions ss
                JOIN spotify_tracks st ON ss.track_id = st.track_id
                WHERE ss.user_id = ? AND ss.end_time IS NULL
                ORDER BY ss.start_time DESC LIMIT 1
            """, (user_id,))
            return await cursor.fetchone()
    
    async def get_user_total_playtime(self, user_id: int) -> int:
        """Get total playtime in seconds for user."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) FROM game_sessions WHERE user_id = ? AND duration_seconds IS NOT NULL", (user_id,))
            return (await cursor.fetchone())[0]
    
    async def get_user_game_playtime(self, user_id: int, game_name: str) -> int:
        """Get playtime in seconds for specific user and game."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                SELECT COALESCE(SUM(gs.duration_seconds), 0)
                FROM game_sessions gs JOIN games g ON gs.game_id = g.game_id
                WHERE gs.user_id = ? AND g.game_name = ? AND gs.duration_seconds IS NOT NULL
            """, (user_id, game_name))
            return (await cursor.fetchone())[0]
    
    async def get_top_games(self, limit: int = 10) -> List[Tuple]:
        """Get top games by total playtime."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                SELECT g.game_name, SUM(gs.duration_seconds) as total_seconds, COUNT(DISTINCT gs.user_id) as unique_players
                FROM game_sessions gs JOIN games g ON gs.game_id = g.game_id
                WHERE gs.duration_seconds IS NOT NULL
                GROUP BY g.game_id ORDER BY total_seconds DESC LIMIT ?
            """, (limit,))
            return await cursor.fetchall()
    
    async def get_player_leaderboard(self, limit: int = 10) -> List[Tuple]:
        """Get player leaderboard by total playtime with enhanced stats."""
        async with self._connection.cursor() as cursor:
            # Simplified query using CTEs for better readability and performance
            await cursor.execute("""
                WITH game_stats AS (
                    SELECT 
                        user_id,
                        SUM(duration_seconds) as total_seconds,
                        COUNT(DISTINCT game_id) as games_played
                    FROM game_sessions
                    WHERE duration_seconds IS NOT NULL
                    GROUP BY user_id
                ),
                top_game AS (
                    SELECT 
                        gs.user_id,
                        g.game_name,
                        SUM(gs.duration_seconds) as game_seconds,
                        ROW_NUMBER() OVER (PARTITION BY gs.user_id ORDER BY SUM(gs.duration_seconds) DESC) as rn
                    FROM game_sessions gs
                    JOIN games g ON gs.game_id = g.game_id
                    WHERE gs.duration_seconds IS NOT NULL
                    GROUP BY gs.user_id, g.game_id
                ),
                spotify_stats AS (
                    SELECT 
                        user_id,
                        COUNT(DISTINCT track_id) as tracks_count,
                        SUM(duration_seconds) as total_seconds
                    FROM spotify_sessions
                    WHERE duration_seconds IS NOT NULL
                    GROUP BY user_id
                )
                SELECT 
                    u.user_id,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(g.total_seconds, 0) as total_game_seconds,
                    COALESCE(g.games_played, 0) as games_played,
                    COALESCE(t.game_name, 'N/A') as most_played_game,
                    COALESCE(t.game_seconds, 0) as most_played_game_seconds,
                    COALESCE(s.tracks_count, 0) as spotify_tracks_count,
                    COALESCE(s.total_seconds, 0) as spotify_total_seconds
                FROM users u
                LEFT JOIN game_stats g ON g.user_id = u.user_id
                LEFT JOIN top_game t ON t.user_id = u.user_id AND t.rn = 1
                LEFT JOIN spotify_stats s ON s.user_id = u.user_id
                ORDER BY COALESCE(g.total_seconds, 0) DESC
                LIMIT ?
            """, (limit,))
            return await cursor.fetchall()
    
    async def get_top_spotify_tracks(self, limit: int = 10) -> List[Tuple]:
        """Get top Spotify tracks by listening time."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                SELECT st.title, st.artist, st.album, SUM(ss.duration_seconds) as total_seconds, COUNT(DISTINCT ss.user_id) as unique_listeners
                FROM spotify_sessions ss JOIN spotify_tracks st ON ss.track_id = st.track_id
                WHERE ss.duration_seconds IS NOT NULL
                GROUP BY ss.track_id ORDER BY total_seconds DESC LIMIT ?
            """, (limit,))
            return await cursor.fetchall()
    
    async def get_game_players(self, game_name: str) -> List[Tuple]:
        """Get all players and playtime for specific game."""
        async with self._connection.cursor() as cursor:
            await cursor.execute("""
                SELECT u.username, u.display_name, SUM(gs.duration_seconds) as total_seconds
                FROM game_sessions gs
                JOIN users u ON gs.user_id = u.user_id
                JOIN games g ON gs.game_id = g.game_id
                WHERE g.game_name = ? AND gs.duration_seconds IS NOT NULL
                GROUP BY gs.user_id ORDER BY total_seconds DESC
            """, (game_name,))
            return await cursor.fetchall()
