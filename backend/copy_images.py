"""
Script to copy images from roms_crawler/images to the backend static directories
"""
import json
import shutil
from pathlib import Path
import re
from typing import Dict, List, Optional

def sanitize_filename(name: str) -> str:
    """Create a safe filename from game title"""
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in name)
    return safe_name.strip().replace(' ', '_')

def normalize_title(title: str) -> str:
    """Normalize game title for matching"""
    # Remove special characters, convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def load_games_from_tsv(games_file: Path) -> List[Dict]:
    """Load games from games.tsv file"""
    games = []
    if not games_file.exists():
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
                    games.append({
                        "title": title,
                        "manufacturer": manufacturers[i] if i < len(manufacturers) else "Unknown",
                        "console": consoles[i] if i < len(consoles) else "Unknown"
                    })
    
    return games

def find_matching_game(game_title: str, console: str, games_list: List[Dict]) -> Optional[Dict]:
    """Find matching game in games.tsv by title and console"""
    normalized_title = normalize_title(game_title)
    
    for game in games_list:
        normalized_game_title = normalize_title(game["title"])
        normalized_game_console = normalize_title(game["console"])
        normalized_console = normalize_title(console)
        
        # Try exact match first
        if normalized_title == normalized_game_title and normalized_console == normalized_game_console:
            return game
        
        # Try partial match (title contains or is contained)
        if (normalized_title in normalized_game_title or normalized_game_title in normalized_title) and \
           (normalized_console in normalized_game_console or normalized_game_console in normalized_console):
            return game
    
    return None

def copy_system_images(roms_data_file: Path, source_images_dir: Path, target_systems_dir: Path):
    """Copy system images from roms_crawler/images to backend/static/images/systems/"""
    print("Copying system images...")
    
    # Create target directory
    target_systems_dir.mkdir(parents=True, exist_ok=True)
    
    # Load roms_data.json
    with open(roms_data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    systems_copied = 0
    systems_skipped = 0
    
    for system in data.get("systems", []):
        image_path = system.get("image_path")
        if not image_path:
            continue
        
        # Convert Windows path separators
        image_path = image_path.replace("\\", "/")
        image_filename = Path(image_path).name
        
        source_path = source_images_dir / image_filename
        target_path = target_systems_dir / image_filename
        
        if source_path.exists():
            if not target_path.exists():
                shutil.copy2(source_path, target_path)
                print(f"  Copied: {image_filename}")
                systems_copied += 1
            else:
                print(f"  Skipped (exists): {image_filename}")
                systems_skipped += 1
        else:
            print(f"  Not found: {image_filename}")
    
    print(f"\nSystem images: {systems_copied} copied, {systems_skipped} already existed")
    return systems_copied

def copy_game_images(roms_data_file: Path, source_images_dir: Path, target_games_dir: Path, games_file: Path):
    """Copy game images from roms_crawler/images to backend/static/images/games/"""
    print("\nCopying game images...")
    
    # Load games from games.tsv
    games_list = load_games_from_tsv(games_file)
    print(f"Loaded {len(games_list)} games from games.tsv")
    
    # Create a mapping of normalized titles to game objects
    games_map: Dict[str, Dict] = {}
    for game in games_list:
        normalized = normalize_title(game["title"])
        if normalized not in games_map:
            games_map[normalized] = []
        games_map[normalized].append(game)
    
    # Load roms_data.json
    with open(roms_data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    games_copied = 0
    games_skipped = 0
    games_not_found = 0
    
    for system in data.get("systems", []):
        system_name = system.get("name", "")
        
        for game in system.get("games", []):
            game_title = game.get("title", "")
            image_path = game.get("image_path", "")
            
            if not image_path or not game_title:
                continue
            
            # Convert Windows path separators
            image_path = image_path.replace("\\", "/")
            image_filename = Path(image_path).name
            
            source_path = source_images_dir / image_filename
            
            if not source_path.exists():
                continue
            
            # Try to find matching game in games.tsv
            matching_game = find_matching_game(game_title, system_name, games_list)
            
            if matching_game:
                # Use the game title from games.tsv for directory name
                game_dir_name = sanitize_filename(matching_game["title"])
                game_dir = target_games_dir / game_dir_name
                game_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = game_dir / image_filename
                
                if not target_path.exists():
                    shutil.copy2(source_path, target_path)
                    games_copied += 1
                    if games_copied % 50 == 0:
                        print(f"  Copied {games_copied} images...")
                else:
                    games_skipped += 1
            else:
                games_not_found += 1
                if games_not_found <= 10:  # Print first 10 not found
                    print(f"  Game not found in games.tsv: {game_title} ({system_name})")
    
    print(f"\nGame images: {games_copied} copied, {games_skipped} already existed, {games_not_found} not found in games.tsv")
    return games_copied

def main():
    # Get paths relative to this script
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    roms_crawler_dir = workspace_root.parent / "roms_crawler"
    
    roms_data_file = roms_crawler_dir / "roms_data.json"
    source_images_dir = roms_crawler_dir / "images"
    games_file = workspace_root / "games.tsv"
    
    target_systems_dir = script_dir / "static" / "images" / "systems"
    target_games_dir = script_dir / "static" / "images" / "games"
    
    # Check if source files exist
    if not roms_data_file.exists():
        print(f"Error: {roms_data_file} not found")
        return
    
    if not source_images_dir.exists():
        print(f"Error: {source_images_dir} not found")
        return
    
    print(f"Source images: {source_images_dir}")
    print(f"Target systems: {target_systems_dir}")
    print(f"Target games: {target_games_dir}")
    print()
    
    # Copy system images
    copy_system_images(roms_data_file, source_images_dir, target_systems_dir)
    
    # Copy game images
    copy_game_images(roms_data_file, source_images_dir, target_games_dir, games_file)
    
    print("\nDone!")

if __name__ == "__main__":
    main()

