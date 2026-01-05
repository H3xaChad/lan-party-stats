"""Activity tracker for games and Spotify."""

import discord
from typing import Dict, Optional, Tuple
import logging

from .database import Database

logger = logging.getLogger(__name__)


class ActivityTracker:
    """Tracks user activities across Discord."""
    
    def __init__(self, db: Database):
        self.db = db
        self.active_sessions: Dict[int, Dict[str, int]] = {}
    
    async def handle_presence_update(self, before: discord.Member, after: discord.Member):
        """Handle Discord presence updates."""
        user_id = after.id
        avatar_url = after.display_avatar.url if after.display_avatar else None
        
        await self.db.upsert_user(user_id, after.name, after.display_name, avatar_url)
        
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = {'game': None, 'spotify': None}
        
        await self._handle_game_activity(before, after, user_id)
        await self._handle_spotify_activity(before, after, user_id)
    
    async def _handle_game_activity(self, before: discord.Member, after: discord.Member, user_id: int):
        """Handle game playing activity."""
        before_game = self._get_playing_activity(before)
        after_game = self._get_playing_activity(after)
        
        if before_game == after_game:
            return
        
        if before_game and before_game != after_game:
            await self._end_game_session(user_id, after.name, before_game)
        
        if after_game and after_game != before_game:
            await self._start_game_session(user_id, after.name, after_game)
    
    async def _handle_spotify_activity(self, before: discord.Member, after: discord.Member, user_id: int):
        """Handle Spotify listening activity."""
        before_spotify = self._get_spotify_activity(before)
        after_spotify = self._get_spotify_activity(after)
        
        if before_spotify == after_spotify:
            return
        
        if before_spotify and before_spotify != after_spotify:
            await self._end_spotify_session(user_id, after.name, before_spotify)
        
        if after_spotify and after_spotify != before_spotify:
            await self._start_spotify_session(user_id, after.name, after_spotify)
    
    def _get_playing_activity(self, member: discord.Member) -> Optional[str]:
        """Extract game name from activities."""
        if not member or not member.activities:
            return None
        
        for activity in member.activities:
            if activity.type == discord.ActivityType.playing:
                return activity.name
        
        return None
    
    def _get_spotify_activity(self, member: discord.Member) -> Optional[Tuple[str, str, str]]:
        """Extract Spotify info (title, artist, album)."""
        if not member or not member.activities:
            return None
        
        for activity in member.activities:
            if isinstance(activity, discord.Spotify):
                return (activity.title, activity.artist, activity.album or "Unknown Album")
        
        return None
    
    async def _start_game_session(self, user_id: int, username: str, game_name: str):
        """Start game session."""
        try:
            session_id = await self.db.start_game_session(user_id, game_name)
            self.active_sessions[user_id]['game'] = session_id
            logger.info(f"{username}: started {game_name}")
        except Exception as e:
            logger.error(f"Error starting game session: {e}")
    
    async def _end_game_session(self, user_id: int, username: str, game_name: str):
        """End game session."""
        session_id = self.active_sessions[user_id].get('game')
        if session_id:
            try:
                await self.db.end_game_session(session_id)
                self.active_sessions[user_id]['game'] = None
                logger.info(f"{username}: stopped {game_name}")
            except Exception as e:
                logger.error(f"Error ending game session: {e}")
    
    async def _start_spotify_session(self, user_id: int, username: str, track_info: Tuple[str, str, str]):
        """Start Spotify session."""
        try:
            title, artist, album = track_info
            session_id = await self.db.start_spotify_session(user_id, title, artist, album)
            self.active_sessions[user_id]['spotify'] = session_id
            logger.info(f"{username}: {title} - {artist}")
        except Exception as e:
            logger.error(f"Error starting Spotify session: {e}")
    
    async def _end_spotify_session(self, user_id: int, username: str, track_info: Tuple[str, str, str]):
        """End Spotify session."""
        session_id = self.active_sessions[user_id].get('spotify')
        if session_id:
            try:
                await self.db.end_spotify_session(session_id)
                self.active_sessions[user_id]['spotify'] = None
            except Exception as e:
                logger.error(f"Error ending Spotify session: {e}")
    
    async def cleanup_active_sessions(self):
        """Clean up active sessions on shutdown."""
        session_count = sum(1 for s in self.active_sessions.values() if s.get('game') or s.get('spotify'))
        if session_count > 0:
            logger.info(f"Saving {session_count} active session(s)...")
        
        for user_id, sessions in self.active_sessions.items():
            if sessions.get('game'):
                try:
                    await self.db.end_game_session(sessions['game'])
                except Exception as e:
                    logger.error(f"Error saving game session: {e}")
            
            if sessions.get('spotify'):
                try:
                    await self.db.end_spotify_session(sessions['spotify'])
                except Exception as e:
                    logger.error(f"Error saving Spotify session: {e}")
        
        self.active_sessions.clear()
    
    async def initialize_from_current_state(self, bot, guild_id: Optional[int] = None):
        """Initialize tracker from current Discord state and recover from crashes.
        
        This method recovers ALL orphaned sessions regardless of age by:
        1. Getting all orphaned sessions from the database
        2. Checking which users are currently active
        3. Recovering sessions for currently active users
        4. Properly closing sessions for inactive users with accurate duration
        """
        logger.info("Checking for orphaned sessions from previous run...")
        
        # Get ALL orphaned sessions (no time limit)
        orphaned_games, orphaned_spotify = await self.db.get_all_orphaned_sessions()
        
        if not orphaned_games and not orphaned_spotify:
            logger.info("No orphaned sessions found")
        else:
            logger.warning(
                f"Found {len(orphaned_games)} orphaned game sessions and "
                f"{len(orphaned_spotify)} orphaned Spotify sessions from previous run"
            )
        
        recovered_sessions = {'games': 0, 'spotify': 0}
        closed_sessions = {'games': 0, 'spotify': 0}
        
        logger.info("Scanning current Discord activity...")
        
        active_games = 0
        active_spotify = 0
        
        # Build lookup maps for ALL orphaned sessions
        user_game_sessions = {(user_id, game_id): (session_id, user_id, game_id) for session_id, user_id, game_id in orphaned_games}
        user_spotify_sessions = {(user_id, track_id): (session_id, user_id, track_id) for session_id, user_id, track_id in orphaned_spotify}
        
        # Filter guilds by guild_id if specified
        guilds = [g for g in bot.guilds if guild_id is None or g.id == guild_id]
        
        for guild in guilds:
            for member in guild.members:
                if member.bot:
                    continue
                
                user_id = member.id
                avatar_url = member.display_avatar.url if member.display_avatar else None
                await self.db.upsert_user(user_id, member.name, member.display_name, avatar_url)
                
                if user_id not in self.active_sessions:
                    self.active_sessions[user_id] = {'game': None, 'spotify': None}
                
                # Handle game activity - try to recover or start new
                game_name = self._get_playing_activity(member)
                if game_name:
                    game_id = await self.db.get_or_create_game(game_name)
                    session_key = (user_id, game_id)
                    
                    # Check if we can recover an orphaned session
                    if session_key in user_game_sessions:
                        session_id, _, _ = user_game_sessions[session_key]
                        self.active_sessions[user_id]['game'] = session_id
                        logger.info(f"Recovered game session for {member.name}: {game_name}")
                        recovered_sessions['games'] += 1
                        del user_game_sessions[session_key]  # Mark as recovered
                    else:
                        # Start new session (no matching orphaned session)
                        await self._start_game_session(user_id, member.name, game_name)
                    active_games += 1
                
                # Handle Spotify activity - try to recover or start new
                spotify_info = self._get_spotify_activity(member)
                if spotify_info:
                    title, artist, album = spotify_info
                    track_id = await self.db.get_or_create_track(title, artist, album)
                    session_key = (user_id, track_id)
                    
                    # Check if we can recover an orphaned session
                    if session_key in user_spotify_sessions:
                        session_id, _, _ = user_spotify_sessions[session_key]
                        self.active_sessions[user_id]['spotify'] = session_id
                        logger.info(f"Recovered Spotify session for {member.name}: {title}")
                        recovered_sessions['spotify'] += 1
                        del user_spotify_sessions[session_key]  # Mark as recovered
                    else:
                        # Start new session (no matching orphaned session)
                        await self._start_spotify_session(user_id, member.name, spotify_info)
                    active_spotify += 1
        
        # Close remaining orphaned sessions that weren't recovered
        # These are sessions where the user is no longer doing that activity
        for session_id, user_id, game_id in user_game_sessions.values():
            await self.db.end_game_session(session_id)
            closed_sessions['games'] += 1
        
        for session_id, user_id, track_id in user_spotify_sessions.values():
            await self.db.end_spotify_session(session_id)
            closed_sessions['spotify'] += 1
        
        # Log summary
        if recovered_sessions['games'] > 0 or recovered_sessions['spotify'] > 0:
            logger.info(
                f"Recovered {recovered_sessions['games']} game and "
                f"{recovered_sessions['spotify']} Spotify sessions from restart"
            )
        
        if closed_sessions['games'] > 0 or closed_sessions['spotify'] > 0:
            logger.info(
                f"Properly closed {closed_sessions['games']} game and "
                f"{closed_sessions['spotify']} Spotify sessions (users no longer active)"
            )
        
        logger.info(f"Tracking {len(self.active_sessions)} users ({active_games} gaming, {active_spotify} listening)")
