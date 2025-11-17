from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
from pathlib import Path
from game_data_service import GameDataService

app = FastAPI(title="Hidden Gem API", version="1.0.0")

# Initialize game data service (RAWG API)
# Get API key from environment variable or set it here
rawg_api_key = os.getenv("RAWG_API_KEY", "")
game_data_service = GameDataService(api_key=rawg_api_key)

# Load trivial games data
trivial_games_file = Path(__file__).parent / "game_data" / "trivial_games.json"
trivial_games: Dict[str, Dict[str, List[str]]] = {}
if trivial_games_file.exists():
    with open(trivial_games_file, "r", encoding="utf-8") as f:
        trivial_games = json.load(f)

def is_trivial_game(title: str, manufacturer: str, console: str) -> bool:
    """Check if a game is trivial (mainstream/popular) for its platform"""
    if manufacturer not in trivial_games:
        return False
    
    platform_games = trivial_games[manufacturer].get(console, [])
    if not platform_games:
        return False
    
    title_lower = title.lower().strip()
    title_normalized = "".join(c if c.isalnum() or c.isspace() else " " for c in title_lower)
    title_words = set(word for word in title_normalized.split() if len(word) > 2)
    
    for trivial_title in platform_games:
        trivial_lower = trivial_title.lower().strip()
        trivial_normalized = "".join(c if c.isalnum() or c.isspace() else " " for c in trivial_lower)
        trivial_words = set(word for word in trivial_normalized.split() if len(word) > 2)
        
        # Check exact match (normalized)
        if title_normalized == trivial_normalized:
            return True
        
        # Check if title contains trivial title or vice versa
        if trivial_normalized in title_normalized or title_normalized in trivial_normalized:
            return True
        
        # Check for significant word overlap (at least 2 words match)
        common_words = title_words.intersection(trivial_words)
        if len(common_words) >= 2:
            return True
        
        # Check if key words match (for series like "Mario", "Kirby", "Metroid")
        if len(trivial_words) == 1 and list(trivial_words)[0] in title_words:
            return True
    
    return False

def get_game_type(title: str, manufacturer: str, console: str) -> str:
    """Get game type: 'trivial' or 'hidden_gem'"""
    return "trivial" if is_trivial_game(title, manufacturer, console) else "hidden_gem"

# Mount static files for images
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Game(BaseModel):
    title: str
    manufacturer: str
    console: str
    type: str = "hidden_gem"  # "trivial" or "hidden_gem"

class GamesResponse(BaseModel):
    games: List[Game]
    total: int

class Manufacturer(BaseModel):
    name: str
    platforms: List[str]
    total_games: int

class ManufacturersResponse(BaseModel):
    manufacturers: List[Manufacturer]
    total: int

# Load games from CSV
def load_games():
    games = []
    games_file = os.path.join(os.path.dirname(__file__), "..", "games.txt")
    
    if not os.path.exists(games_file):
        return games
    
    with open(games_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) < 3:
            return games
        
        # First line: manufacturers
        manufacturers = lines[0].strip().split("\t")
        # Second line: consoles
        consoles = lines[1].strip().split("\t")
        
        # Remaining lines: games
        for line in lines[2:]:
            titles = line.strip().split("\t")
            for i, title in enumerate(titles):
                if title and i < len(consoles):
                    manufacturer = manufacturers[i] if i < len(manufacturers) else "Unknown"
                    console = consoles[i] if i < len(consoles) else "Unknown"
                    game_type = get_game_type(title, manufacturer, console)
                    games.append({
                        "title": title,
                        "manufacturer": manufacturer,
                        "console": console,
                        "type": game_type
                    })
    
    return games

@app.get("/")
async def root():
    return {"message": "Hidden Gem API", "version": "1.0.0"}

@app.get("/games", response_model=GamesResponse)
async def get_games():
    """Get all games"""
    games = load_games()
    return {"games": games, "total": len(games)}

@app.get("/games/search")
async def search_games(q: str = ""):
    """Search games by title"""
    games = load_games()
    if q:
        games = [g for g in games if q.lower() in g["title"].lower()]
    return {"games": games, "total": len(games)}

@app.get("/games/consoles")
async def get_consoles():
    """Get all unique consoles"""
    games = load_games()
    consoles = set(g["console"] for g in games)
    return {"consoles": sorted(list(consoles))}

@app.get("/games/by-console/{console}")
async def get_games_by_console(console: str):
    """Get games by console"""
    games = load_games()
    filtered = [g for g in games if console.lower() == g["console"].lower()]
    return {"games": filtered, "total": len(filtered)}

@app.get("/manufacturers", response_model=ManufacturersResponse)
async def get_manufacturers():
    """Get all manufacturers with their platforms and game counts"""
    games = load_games()
    
    # Group by manufacturer
    manufacturer_data = {}
    for game in games:
        mfr = game["manufacturer"]
        console = game["console"]
        
        if mfr not in manufacturer_data:
            manufacturer_data[mfr] = {
                "platforms": set(),
                "total_games": 0
            }
        
        manufacturer_data[mfr]["platforms"].add(console)
        manufacturer_data[mfr]["total_games"] += 1
    
    # Convert to list
    manufacturers = []
    for name, data in manufacturer_data.items():
        manufacturers.append({
            "name": name,
            "platforms": sorted(list(data["platforms"])),
            "total_games": data["total_games"]
        })
    
    # Sort by total games descending
    manufacturers.sort(key=lambda x: x["total_games"], reverse=True)
    
    return {"manufacturers": manufacturers, "total": len(manufacturers)}

@app.get("/manufacturer/{name}")
async def get_manufacturer_detail(name: str):
    """Get details for a specific manufacturer"""
    games = load_games()
    
    # Filter games for this manufacturer
    manufacturer_games = [g for g in games if g["manufacturer"].lower() == name.lower()]
    
    if not manufacturer_games:
        raise HTTPException(status_code=404, detail=f"Manufacturer '{name}' not found")
    
    # Get unique platforms for this manufacturer
    platforms = sorted(set(g["console"] for g in manufacturer_games))
    
    return {
        "name": manufacturer_games[0]["manufacturer"],
        "platforms": platforms,
        "total_games": len(manufacturer_games),
        "games": manufacturer_games
    }

@app.get("/games/by-manufacturer/{manufacturer}")
async def get_games_by_manufacturer(manufacturer: str):
    """Get games by manufacturer"""
    games = load_games()
    filtered = [g for g in games if manufacturer.lower() == g["manufacturer"].lower()]
    return {"games": filtered, "total": len(filtered)}

@app.get("/manufacturer/{name}/{platform}")
async def get_manufacturer_platform_games(name: str, platform: str):
    """Get games for a specific manufacturer and platform"""
    games = load_games()
    
    # Filter games for this manufacturer and platform
    filtered = [
        g for g in games 
        if g["manufacturer"].lower() == name.lower() 
        and g["console"].lower() == platform.lower()
    ]
    
    if not filtered:
        raise HTTPException(
            status_code=404, 
            detail=f"No games found for manufacturer '{name}' on platform '{platform}'"
        )
    
    # Sort alphabetically by title
    filtered.sort(key=lambda x: x["title"].lower())
    
    return {
        "manufacturer": name,
        "platform": platform,
        "games": filtered,
        "total": len(filtered)
    }

@app.get("/games/{title}/details")
async def get_game_details(title: str, console: Optional[str] = None, max_images: int = 5):
    """Get game details including description and images from RAWG API
    
    Args:
        title: Game title
        console: Console/platform name (optional, helps with matching)
        max_images: Maximum number of images (default: 5 = 1 cover + 4 screenshots)
    """
    from urllib.parse import unquote
    decoded_title = unquote(title).replace('_', ' ')
    
    # Ensure minimum 5 images (1 cover + 4 screenshots)
    if max_images < 5:
        max_images = 5
    
    # Get game info from game data service (uses cache, only downloads if needed)
    game_info = game_data_service.get_game_info(decoded_title, console, max_images)
    
    return game_info

@app.get("/games/{title}/thumbnail")
async def get_game_thumbnail(title: str, console: Optional[str] = None):
    """Get thumbnail image URL for a game"""
    from urllib.parse import unquote
    decoded_title = unquote(title).replace('_', ' ')
    
    # Get first image for thumbnail
    images = game_data_service.get_game_images(decoded_title, max_images=1, console=console)
    
    if images and len(images) > 0:
        # Convert to URL
        img_path = Path(images[0])
        try:
            # Get relative path from static directory
            rel_path = img_path.relative_to(static_dir)
            return {"thumbnail": f"/static/{rel_path.as_posix()}"}
        except Exception:
            return {"thumbnail": None}
    
    return {"thumbnail": None}

def get_system_image_filename(console_name: str) -> Optional[str]:
    """Convert console name to system image filename"""
    # Mapping from games.txt console names to system image filenames
    console_mapping = {
        "N64": "system_Nintendo64.jpg",
        "Gamecube": "system_GameCube.jpg",
        "Windows": "system_Windows.jpg",
        "PS3": "system_PS3.jpg",
        "Gameboy": "system_GameBoyGB.jpg",
        "GBA": "system_GBA.jpg",
        "NES": "system_NES.jpg",
        "SNES": "system_SNES.jpg",
        "Switch": "system_NintendoSwitch.jpg",  # May not exist
        "Wii": "system_NintendoWii.jpg",
        "DS": "system_NintendoDS.jpg",
        "3DS": "system_Nintendo3DS.jpg",
        "Wii U": "system_WiiU.jpg",
        "PSP": "system_PSP.jpg",
        "PS Vita": "system_PSVita.jpg",  # May not exist
        "ZX Spectrum": "system_ZXSpectrum.jpg",  # May not exist
        "Amiga": "system_Commodore-Amiga.jpg",
        "Megadrive": "system_SegaGenesis.jpg",
        "PS2": "system_PS2.jpg",
        "TurboGrafx-16/PC Engine": "system_NECTurboGrafx-16.jpg",
        "Neo-Geo": "system_NeoGeo.jpg",
        "Sega Master System": "system_SegaMasterSystem.jpg",
        "Dreamcast": "system_SegaDreamcast.jpg",
        "PS1": "system_PlayStationPS.jpg",
        "XBOX": "system_XBOX.jpg",
        "XBOX360": "system_Xbox360.jpg",
        "Pico-8": "system_Pico8.jpg",  # May not exist
    }
    
    # Try direct mapping first
    if console_name in console_mapping:
        return console_mapping[console_name]
    
    # Try case-insensitive matching
    console_lower = console_name.lower()
    for key, value in console_mapping.items():
        if key.lower() == console_lower:
            return value
    
    # Try to construct filename from console name
    # Replace spaces and special chars with nothing, add system_ prefix
    safe_name = console_name.replace(" ", "").replace("/", "").replace("-", "")
    return f"system_{safe_name}.jpg"

@app.get("/systems/{console}/image")
async def get_system_image(console: str):
    """Get system image URL for a console/platform"""
    from urllib.parse import unquote
    decoded_console = unquote(console).replace('_', ' ')
    
    filename = get_system_image_filename(decoded_console)
    if not filename:
        return {"image": None}
    
    systems_dir = static_dir / "images" / "systems"
    image_path = systems_dir / filename
    
    if image_path.exists():
        rel_path = image_path.relative_to(static_dir)
        return {"image": f"/static/{rel_path.as_posix()}"}
    
    return {"image": None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

