"""LAN Party Stats Bot - Main Entry Point."""

import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from bot import run_bot


def setup_logging():
    """Configure logging for the bot."""
    # Custom formatter for clean, readable output
    class CleanFormatter(logging.Formatter):
        """Custom formatter with colors and clean layout."""
        
        COLORS = {
            'DEBUG': '\033[36m',      # Cyan
            'INFO': '\033[32m',       # Green
            'WARNING': '\033[33m',    # Yellow
            'ERROR': '\033[31m',      # Red
            'CRITICAL': '\033[35m',   # Magenta
        }
        RESET = '\033[0m'
        BOLD = '\033[1m'
        
        def format(self, record):
            # Simplify logger names
            logger_name = record.name.replace('bot.', '').replace('discord.', 'discord.')
            if logger_name == 'root':
                logger_name = 'root'
            
            # Color-code level
            level_color = self.COLORS.get(record.levelname, '')
            level = f"{level_color}{record.levelname:<8}{self.RESET}"
            
            # Format message
            timestamp = self.formatTime(record, '%H:%M:%S')
            msg = f"{self.BOLD}{timestamp}{self.RESET} {level} {logger_name:<12} {record.getMessage()}"
            
            if record.exc_info:
                msg += '\n' + self.formatException(record.exc_info)
            
            return msg
    
    # File formatter (no colors)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CleanFormatter())
    
    # File handler without colors
    file_handler = logging.FileHandler('bot.log')
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce discord.py verbosity
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.client').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)


def main():
    setup_logging()
    load_dotenv()
    
    logger = logging.getLogger('main')
    
    token = os.getenv("DISCORD_TOKEN")
    db_path = os.getenv("DATABASE_PATH", "stats.db")
    
    if not token:
        logger.error("DISCORD_TOKEN not set in .env file")
        return 1
    
    logger.info(f"Starting LAN Party Stats Bot (db: {db_path})")
    
    try:
        asyncio.run(run_bot(token, db_path))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    logger.info("Bot shutdown complete - exiting")
    return 0



if __name__ == "__main__":
    exit(main())

