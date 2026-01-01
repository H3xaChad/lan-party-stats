"""Statistics and formatting utilities."""

from typing import List, Dict, Optional

from .database import Database


def seconds_to_readable(seconds: int) -> str:
    """Convert seconds to readable format (12h 34m)."""
    if seconds < 60:
        return f"{seconds}s"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


def seconds_to_hours(seconds: int) -> float:
    """Convert seconds to hours (2 decimals)."""
    return round(seconds / 3600, 2)


class StatsManager:
    """Statistics queries and formatting."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def get_player_stats(self, user_id: int) -> Optional[Dict]:
        """Get comprehensive stats for a player."""
        user = await self.db.get_user(user_id)
        if not user:
            return None
        
        total_seconds = await self.db.get_user_total_playtime(user_id)
        
        async with self.db._connection.cursor() as cursor:
            await cursor.execute("""
                SELECT g.game_name, SUM(gs.duration_seconds) as total_seconds
                FROM game_sessions gs JOIN games g ON gs.game_id = g.game_id
                WHERE gs.user_id = ? AND gs.duration_seconds IS NOT NULL
                GROUP BY g.game_id ORDER BY total_seconds DESC
            """, (user_id,))
            games = await cursor.fetchall()
        
        return {
            'user_id': user[0],
            'username': user[1],
            'display_name': user[2],
            'avatar_url': user[3],
            'total_playtime_seconds': total_seconds,
            'total_playtime_readable': seconds_to_readable(total_seconds),
            'total_playtime_hours': seconds_to_hours(total_seconds),
            'games_played': len(games),
            'games': [{'name': g[0], 'seconds': g[1], 'readable': seconds_to_readable(g[1]), 'hours': seconds_to_hours(g[1])} for g in games]
        }
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get player leaderboard with enhanced stats."""
        players = await self.db.get_player_leaderboard(limit)
        return [{
            'rank': idx,
            'user_id': p[0],
            'username': p[1],
            'display_name': p[2],
            'avatar_url': p[3],
            'total_seconds': p[4],
            'readable': seconds_to_readable(p[4]),
            'hours': seconds_to_hours(p[4]),
            'games_played': p[5],
            'most_played_game': 'Nüxxx' if p[5] == 0 else p[6],
            'most_played_game_seconds': p[7],
            'most_played_game_readable': seconds_to_readable(p[7]),
            'most_played_game_hours': seconds_to_hours(p[7]),
            'spotify_tracks_count': p[8],
            'spotify_total_seconds': p[9],
            'spotify_readable': seconds_to_readable(p[9]),
            'spotify_hours': seconds_to_hours(p[9])
        } for idx, p in enumerate(players, 1)]
    
    async def get_top_games(self, limit: int = 10) -> List[Dict]:
        """Get top games by total playtime."""
        games = await self.db.get_top_games(limit)
        return [{
            'rank': idx,
            'name': g[0],
            'total_seconds': g[1],
            'readable': seconds_to_readable(g[1]),
            'hours': seconds_to_hours(g[1]),
            'unique_players': g[2]
        } for idx, g in enumerate(games, 1)]
    
    async def get_game_details(self, game_name: str) -> Optional[Dict]:
        """Get detailed statistics for a specific game."""
        players = await self.db.get_game_players(game_name)
        if not players:
            return None
        
        total_seconds = sum(p[2] for p in players)
        return {
            'game_name': game_name,
            'total_seconds': total_seconds,
            'readable': seconds_to_readable(total_seconds),
            'hours': seconds_to_hours(total_seconds),
            'unique_players': len(players),
            'players': [{'username': p[0], 'display_name': p[1], 'seconds': p[2], 'readable': seconds_to_readable(p[2]), 'hours': seconds_to_hours(p[2])} for p in players]
        }
    
    async def get_top_spotify_tracks(self, limit: int = 10) -> List[Dict]:
        """Get top Spotify tracks."""
        tracks = await self.db.get_top_spotify_tracks(limit)
        return [{
            'rank': idx,
            'title': t[0],
            'artist': t[1],
            'album': t[2],
            'total_seconds': t[3],
            'readable': seconds_to_readable(t[3]),
            'hours': seconds_to_hours(t[3]),
            'unique_listeners': t[4]
        } for idx, t in enumerate(tracks, 1)]
    
    async def get_user_spotify_stats(self, user_id: int) -> Dict:
        """Get Spotify stats for a user."""
        async with self.db._connection.cursor() as cursor:
            await cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) FROM spotify_sessions WHERE user_id = ? AND duration_seconds IS NOT NULL", (user_id,))
            total_seconds = (await cursor.fetchone())[0]
            
            await cursor.execute("""
                SELECT st.title, st.artist, st.album, SUM(ss.duration_seconds) as total_seconds
                FROM spotify_sessions ss JOIN spotify_tracks st ON ss.track_id = st.track_id
                WHERE ss.user_id = ? AND ss.duration_seconds IS NOT NULL
                GROUP BY ss.track_id ORDER BY total_seconds DESC
            """, (user_id,))
            tracks = await cursor.fetchall()
        
        return {
            'total_seconds': total_seconds,
            'readable': seconds_to_readable(total_seconds),
            'hours': seconds_to_hours(total_seconds),
            'tracks_count': len(tracks),
            'top_tracks': [{'title': t[0], 'artist': t[1], 'album': t[2], 'seconds': t[3], 'readable': seconds_to_readable(t[3]), 'hours': seconds_to_hours(t[3])} for t in tracks]
        }
    
    async def get_overview_stats(self) -> Dict:
        """Get overview statistics for entire server."""
        async with self.db._connection.cursor() as cursor:
            await cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) FROM game_sessions WHERE duration_seconds IS NOT NULL")
            total_game_seconds = (await cursor.fetchone())[0]
            
            await cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) FROM spotify_sessions WHERE duration_seconds IS NOT NULL")
            total_spotify_seconds = (await cursor.fetchone())[0]
            
            await cursor.execute("SELECT COUNT(DISTINCT user_id) FROM game_sessions")
            unique_players = (await cursor.fetchone())[0]
            
            await cursor.execute("SELECT COUNT(*) FROM games")
            unique_games = (await cursor.fetchone())[0]
            
            await cursor.execute("SELECT COUNT(*) FROM spotify_tracks")
            unique_tracks = (await cursor.fetchone())[0]
        
        return {
            'total_game_seconds': total_game_seconds,
            'total_game_readable': seconds_to_readable(total_game_seconds),
            'total_game_hours': seconds_to_hours(total_game_seconds),
            'total_spotify_seconds': total_spotify_seconds,
            'total_spotify_readable': seconds_to_readable(total_spotify_seconds),
            'total_spotify_hours': seconds_to_hours(total_spotify_seconds),
            'unique_players': unique_players,
            'unique_games': unique_games,
            'unique_tracks': unique_tracks
        }
