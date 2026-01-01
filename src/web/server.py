"""FastAPI web server for LAN Party Stats."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from bot.database import Database
from bot.stats import StatsManager

logger = logging.getLogger(__name__)

# Database and stats manager
db: Database = None
stats: StatsManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup and shutdown)."""
    # Startup
    global db, stats
    logger.info("Starting web server...")
    db = Database()
    await db.connect()
    stats = StatsManager(db)
    logger.info("Web server initialized")
    
    yield
    
    # Shutdown
    if db:
        await db.close()
    logger.info("Web server shutdown")


app = FastAPI(title="LAN Party Stats", lifespan=lifespan)

# Setup static files and templates
static_dir = Path(__file__).parent.parent.parent / "static"
templates_dir = Path(__file__).parent.parent.parent / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page."""
    overview = await stats.get_overview_stats()
    top_games = await stats.get_top_games(5)
    top_tracks = await stats.get_top_spotify_tracks(5)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "overview": overview,
        "top_games": top_games,
        "top_tracks": top_tracks,
        "page": "home"
    })


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request):
    """Player leaderboard page."""
    leaders = await stats.get_leaderboard(25)
    
    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "leaders": leaders,
        "page": "leaderboard"
    })


@app.get("/games", response_class=HTMLResponse)
async def games(request: Request):
    """Top games page."""
    try:
        top_games = await stats.get_top_games(25)
        
        return templates.TemplateResponse("games.html", {
            "request": request,
            "games": top_games,
            "page": "games"
        })
    except Exception as e:
        logger.error(f"Error loading games: {e}")
        return templates.TemplateResponse("404.html", {
            "request": request,
            "message": "Error loading games"
        }, status_code=500)


@app.get("/spotify", response_class=HTMLResponse)
async def spotify(request: Request):
    """Top Spotify tracks page."""
    top_tracks = await stats.get_top_spotify_tracks(25)
    
    return templates.TemplateResponse("spotify.html", {
        "request": request,
        "tracks": top_tracks,
        "page": "spotify"
    })


@app.get("/player/{user_id}", response_class=HTMLResponse)
async def player_stats(request: Request, user_id: int):
    """Individual player statistics page."""
    player = await stats.get_player_stats(user_id)
    spotify = await stats.get_user_spotify_stats(user_id)
    
    if not player:
        return templates.TemplateResponse("404.html", {
            "request": request,
            "message": f"Player not found"
        }, status_code=404)
    
    return templates.TemplateResponse("player.html", {
        "request": request,
        "player": player,
        "spotify": spotify,
        "page": "player"
    })


# HTMX partial endpoints for live updates
@app.get("/htmx/overview-stats")
async def htmx_overview_stats(request: Request):
    """HTMX endpoint for overview stats."""
    overview = await stats.get_overview_stats()
    return templates.TemplateResponse("partials/overview_stats.html", {
        "request": request,
        "overview": overview
    })


@app.get("/htmx/leaderboard")
async def htmx_leaderboard(request: Request, limit: int = 10):
    """HTMX endpoint for leaderboard."""
    leaders = await stats.get_leaderboard(limit)
    return templates.TemplateResponse("partials/leaderboard_table.html", {
        "request": request,
        "leaders": leaders
    })
