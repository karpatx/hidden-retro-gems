from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import os
import json
import shutil
from pathlib import Path
from datetime import timedelta
from sqlalchemy.orm import Session
from urllib.parse import unquote
from game_data_service import GameDataService
from database import init_db, get_db, User
from auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user_by_email
)

app = FastAPI(title="Hidden Gem API", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and create admin user if not exists"""
    init_db()
    
    # Create admin user if not exists
    db = next(get_db())
    admin_email = "ikarpati@gmail.com"
    admin_user = get_user_by_email(db, admin_email)
    if not admin_user:
        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash("123456789"),
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user created: {admin_email}")
    db.close()

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

# Auth models
class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    email: str
    is_admin: bool
    is_active: bool

class UserCreate(BaseModel):
    email: EmailStr
    password: str

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

# Authentication endpoints
@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return {
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active
    }

@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_admin=False,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "email": new_user.email,
        "is_admin": new_user.is_admin,
        "is_active": new_user.is_active
    }

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
    
    # Apply image order if available
    order_data = load_image_order()
    game_order = order_data.get(decoded_title, [])
    
    if game_order and "images" in game_info:
        # Sort images according to order
        order_map = {Path(img).name: idx for idx, img in enumerate(game_order)}
        game_info["images"].sort(key=lambda img: (
            order_map.get(Path(img).name, 999),
            img
        ))
    
    # Add tags if available
    tags_data = load_tags()
    if decoded_title in tags_data:
        game_info["tags"] = tags_data[decoded_title]
    
    return game_info

@app.get("/games/{title}/thumbnail")
async def get_game_thumbnail(title: str, console: Optional[str] = None):
    """Get thumbnail image URL for a game (uses first image from ordered list)"""
    from urllib.parse import unquote
    decoded_title = unquote(title).replace('_', ' ')
    
    try:
        # Get game info which includes ordered images
        game_info = game_data_service.get_game_info(decoded_title, console, max_images=5)
        
        images = game_info.get("images", [])
        
        # Apply image order if available
        try:
            order_data = load_image_order()
            game_order = order_data.get(decoded_title, [])
            
            if game_order and images:
                # Sort images according to order
                order_map = {Path(img).name: idx for idx, img in enumerate(game_order)}
                images.sort(key=lambda img: (
                    order_map.get(Path(img).name, 999),
                    img
                ))
        except Exception as e:
            # If order loading fails, just use images as-is
            print(f"Warning: Could not load image order for {decoded_title}: {e}")
        
        # Get first image (cover image)
        # Images from get_game_info are already in URL format like "/static/images/games/..."
        if images and len(images) > 0:
            return {"thumbnail": images[0]}
        
        return {"thumbnail": None}
    except Exception as e:
        print(f"Error getting thumbnail for {decoded_title}: {e}")
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

# Admin endpoints
class DescriptionUpdate(BaseModel):
    description: str

class ImageOrderRequest(BaseModel):
    order: List[str]

class TagsUpdate(BaseModel):
    tags: List[str]

@app.put("/admin/games/{title}/description", tags=["admin"])
async def update_game_description(
    title: str,
    description_data: DescriptionUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update game description (admin only)"""
    print(f"DEBUG: update_game_description called with title={title}, user={current_user.email}")
    try:
        decoded_title = unquote(title)
        
        # Load descriptions
        descriptions_file = Path(__file__).parent / "game_data" / "descriptions.json"
        descriptions = {}
        if descriptions_file.exists():
            try:
                with open(descriptions_file, "r", encoding="utf-8") as f:
                    descriptions = json.load(f)
            except json.JSONDecodeError:
                # If JSON is corrupted, start with empty dict
                descriptions = {}
        
        # Update description
        descriptions[decoded_title] = description_data.description
        
        # Save descriptions
        descriptions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(descriptions_file, "w", encoding="utf-8") as f:
            json.dump(descriptions, f, ensure_ascii=False, indent=2)
        
        # Reload in game_data_service
        game_data_service.descriptions = descriptions
        
        return {"message": "Description updated", "title": decoded_title}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating description: {str(e)}"
        )

@app.delete("/admin/games/{title}/description")
async def delete_game_description(
    title: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete game description (admin only)"""
    decoded_title = unquote(title).replace('_', ' ')
    
    # Load descriptions
    descriptions_file = Path(__file__).parent / "game_data" / "descriptions.json"
    descriptions = {}
    if descriptions_file.exists():
        with open(descriptions_file, "r", encoding="utf-8") as f:
            descriptions = json.load(f)
    
    # Delete description
    if decoded_title in descriptions:
        del descriptions[decoded_title]
        
        # Save descriptions
        with open(descriptions_file, "w", encoding="utf-8") as f:
            json.dump(descriptions, f, ensure_ascii=False, indent=2)
        
        # Reload in game_data_service
        game_data_service.descriptions = descriptions
        
        return {"message": "Description deleted", "title": decoded_title}
    else:
        raise HTTPException(status_code=404, detail="Description not found")

@app.post("/admin/games/{title}/images")
async def upload_game_image(
    title: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload image for a game (admin only)"""
    try:
        decoded_title = unquote(title).replace('_', ' ')
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Get game images directory
        game_dir = game_data_service._get_game_images_dir(decoded_title)
        
        # Sanitize filename to avoid conflicts
        safe_filename = file.filename.replace(' ', '_').replace('/', '_').replace('\\', '_')
        file_path = game_dir / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get relative path for response
        rel_path = file_path.relative_to(static_dir)
        
        return {
            "message": "Image uploaded",
            "title": decoded_title,
            "filename": safe_filename,
            "url": f"/static/{rel_path.as_posix()}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading image: {str(e)}"
        )

@app.put("/admin/games/{title}/images/order")
async def update_image_order(
    title: str,
    order_data: ImageOrderRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Update image order for a game (admin only)"""
    print(f"Received PUT request to /admin/games/{title}/images/order")
    print(f"Order data: {order_data}")
    decoded_title = unquote(title).replace('_', ' ')
    
    try:
        # Load current order
        order = load_image_order()
        
        # Update order for this game
        order[decoded_title] = order_data.order
        save_image_order(order)
        
        print(f"Image order updated for {decoded_title}: {order_data.order}")
        return {"message": "Image order updated", "title": decoded_title, "order": order_data.order}
    except Exception as e:
        print(f"Error updating image order: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating image order: {str(e)}")

@app.delete("/admin/games/{title}/images/{filename}")
async def delete_game_image(
    title: str,
    filename: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete image for a game (admin only)"""
    decoded_title = unquote(title).replace('_', ' ')
    decoded_filename = unquote(filename)
    
    # Get game images directory
    game_dir = game_data_service._get_game_images_dir(decoded_title)
    file_path = game_dir / decoded_filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete file
    file_path.unlink()
    
    return {
        "message": "Image deleted",
        "title": decoded_title,
        "filename": decoded_filename
    }

def get_image_order_file() -> Path:
    """Get path to image order JSON file"""
    return Path(__file__).parent / "game_data" / "image_order.json"

def load_image_order() -> Dict[str, List[str]]:
    """Load image order from JSON file"""
    order_file = get_image_order_file()
    if order_file.exists():
        try:
            with open(order_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_image_order(order: Dict[str, List[str]]):
    """Save image order to JSON file"""
    order_file = get_image_order_file()
    order_file.parent.mkdir(parents=True, exist_ok=True)
    with open(order_file, "w", encoding="utf-8") as f:
        json.dump(order, f, ensure_ascii=False, indent=2)

@app.put("/admin/games/{title}/images/order")
async def update_image_order(
    title: str,
    order_data: ImageOrderRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Update image order for a game (admin only)"""
    print(f"Received PUT request to /admin/games/{title}/images/order")
    print(f"Order data: {order_data}")
    decoded_title = unquote(title).replace('_', ' ')
    
    try:
        # Load current order
        order = load_image_order()
        
        # Update order for this game
        order[decoded_title] = order_data.order
        save_image_order(order)
        
        print(f"Image order updated for {decoded_title}: {order_data.order}")
        return {"message": "Image order updated", "title": decoded_title, "order": order_data.order}
    except Exception as e:
        print(f"Error updating image order: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating image order: {str(e)}")

@app.get("/admin/games/{title}/images")
async def list_game_images(
    title: str,
    current_user: User = Depends(get_current_admin_user)
):
    """List all images for a game (admin only)"""
    decoded_title = unquote(title).replace('_', ' ')
    
    # Get game images directory
    game_dir = game_data_service._get_game_images_dir(decoded_title)
    
    if not game_dir.exists():
        return {"images": []}
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    images = []
    
    for file in game_dir.iterdir():
        if file.suffix.lower() in image_extensions:
            rel_path = file.relative_to(static_dir)
            images.append({
                "filename": file.name,
                "url": f"/static/{rel_path.as_posix()}"
            })
    
    # Load order from JSON
    order_data = load_image_order()
    game_order = order_data.get(decoded_title, [])
    
    # Sort images according to order
    if game_order:
        # Create a mapping of filename to index
        order_map = {filename: idx for idx, filename in enumerate(game_order)}
        # Sort: first by order, then alphabetically for unordered images
        images.sort(key=lambda x: (
            order_map.get(x["filename"], 999),
            x["filename"]
        ))
    else:
        # Default: alphabetical
        images.sort(key=lambda x: x["filename"])
    
    return {"images": images}

# Tags management endpoints
def get_tags_file() -> Path:
    """Get path to tags JSON file"""
    return Path(__file__).parent / "game_data" / "tags.json"

def load_tags() -> Dict[str, List[str]]:
    """Load tags from JSON file"""
    tags_file = get_tags_file()
    if tags_file.exists():
        try:
            with open(tags_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_tags(tags: Dict[str, List[str]]):
    """Save tags to JSON file"""
    tags_file = get_tags_file()
    tags_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tags_file, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)

@app.get("/admin/games/{title}/tags")
async def get_game_tags(
    title: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get tags for a game (admin only)"""
    decoded_title = unquote(title).replace('_', ' ')
    tags_data = load_tags()
    return {"tags": tags_data.get(decoded_title, [])}

@app.put("/admin/games/{title}/tags")
async def update_game_tags(
    title: str,
    tags_data: TagsUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update tags for a game (admin only)"""
    decoded_title = unquote(title).replace('_', ' ')
    
    try:
        tags = load_tags()
        tags[decoded_title] = tags_data.tags
        save_tags(tags)
        return {"message": "Tags updated", "title": decoded_title, "tags": tags_data.tags}
    except Exception as e:
        print(f"Error updating tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating tags: {str(e)}")

@app.delete("/admin/games/{title}/tags")
async def delete_game_tags(
    title: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete tags for a game (admin only)"""
    decoded_title = unquote(title).replace('_', ' ')
    
    try:
        tags = load_tags()
        if decoded_title in tags:
            del tags[decoded_title]
            save_tags(tags)
        return {"message": "Tags deleted", "title": decoded_title}
    except Exception as e:
        print(f"Error deleting tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting tags: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

