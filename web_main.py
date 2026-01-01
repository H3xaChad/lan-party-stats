"""Web server entry point for LAN Party Stats."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))


def setup_logging():
    """Configure logging for the web server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('web.log')
        ]
    )


def main():
    setup_logging()
    load_dotenv()
    
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "5000"))
    
    print(f"🌐 Starting LAN Party Stats web server on http://{host}:{port}")
    logging.info(f"Starting web server on {host}:{port}")
    
    import uvicorn
    from web.server import app
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
