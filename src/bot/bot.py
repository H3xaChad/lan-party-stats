"""Discord bot main module."""

import discord
from discord.ext import commands
import logging
import signal
import sys
import asyncio
from typing import Optional

from .database import Database
from .tracker import ActivityTracker
from .stats import StatsManager
from .commands import setup as setup_commands

logger = logging.getLogger(__name__)


class LanPartyBot(commands.Bot):
    """The main bot class."""

    def __init__(self, *args, db_path: str = "stats.db", **kwargs):
        super().__init__(*args, **kwargs)
        self.db: Optional[Database] = None
        self.tracker: Optional[ActivityTracker] = None
        self.stats_manager: Optional[StatsManager] = None
        self._shutdown = False
        self._db_path = db_path

    async def setup_hook(self):
        """Initialize database, components, and sync commands."""
        logger.info("Initializing components...")
        try:
            self.db = Database(self._db_path)
            await self.db.connect()
            logger.info("Database connected")
            
            self.tracker = ActivityTracker(self.db)
            self.stats_manager = StatsManager(self.db)
            logger.info("Tracker and stats manager ready")
            
            await setup_commands(self, self.stats_manager)
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            raise

        logger.info("Bot ready")

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        guild_text = f"{len(self.guilds)} guild(s)" if len(self.guilds) != 1 else "1 guild"
        logger.info(f"Connected as {self.user} | {guild_text}")
        if self.tracker:
            await self.tracker.initialize_from_current_state(self)

    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Track user activity changes."""
        if after.bot or not self.tracker:
            return
        try:
            await self.tracker.handle_presence_update(before, after)
        except Exception as e:
            logger.error(f"Presence update error: {e}", exc_info=True)

    async def on_error(self, event: str, *args, **kwargs):
        """Handle errors in events."""
        logger.error(f"Error in {event}:", exc_info=sys.exc_info())

    async def close(self):
        """Cleanly shutdown the bot."""
        if self._shutdown:
            return
        self._shutdown = True
        
        try:
            if self.tracker:
                await self.tracker.cleanup_active_sessions()
            if self.db:
                await self.db.close()
            await super().close()
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
        
        logger.info("Shutdown complete")


def create_bot(db_path: str = "stats.db") -> LanPartyBot:
    """Create and configure the Discord bot instance."""
    intents = discord.Intents.default()
    intents.presences = True
    intents.members = True
    return LanPartyBot(command_prefix="!", intents=intents, db_path=db_path)


async def run_bot(token: str, db_path: str = "stats.db"):
    """Run the bot and handle graceful shutdown."""
    bot = create_bot(db_path)
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    async def runner():
        """Run bot and wait for shutdown signal."""
        try:
            async with bot:
                logger.info("Attempting to connect to Discord...")
                await bot.start(token)
        except discord.errors.LoginFailure as e:
            logger.error(f"Login failed! Invalid token or bot configuration: {e}")
            shutdown_event.set()
            raise
        except discord.errors.PrivilegedIntentsRequired as e:
            logger.error(f"Missing required intents! Enable PRESENCE, MEMBERS, and MESSAGE_CONTENT intents in Developer Portal: {e}")
            shutdown_event.set()
            raise
        except Exception as e:
            logger.error(f"Bot startup failed: {e}", exc_info=True)
            shutdown_event.set()
            raise
    
    try:
        bot_task = asyncio.create_task(runner())
        await shutdown_event.wait()
        
        # Only try to close if bot isn't already closed
        if not bot.is_closed():
            logger.info("Closing bot connection...")
            await bot.close()
        
        try:
            await asyncio.wait_for(bot_task, timeout=2.0)
        except asyncio.TimeoutError:
            logger.warning("Forcing shutdown...")
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
        except Exception:
            pass  # Task already completed with error
                
    except discord.errors.LoginFailure:
        logger.error("Invalid Discord token!")
    except discord.errors.PrivilegedIntentsRequired:
        logger.error("Enable required intents in Discord Developer Portal!")
    except Exception as e:
        logger.error(f"Runtime error: {e}", exc_info=True)
    finally:
        if not bot.is_closed():
            await bot.close()
        await asyncio.sleep(0.1)