"""
Script to fetch and cache game descriptions AND images for all games
This should be run once to populate descriptions.json and download images
"""
import json
import os
from pathlib import Path
from game_data_service import GameDataService

def load_games_from_tsv(games_file: Path):
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
                        "title": title.strip(),
                        "manufacturer": manufacturers[i] if i < len(manufacturers) else "Unknown",
                        "console": consoles[i] if i < len(consoles) else "Unknown"
                    })
    
    return games

def main():
    """Fetch descriptions and images for all games"""
    # Get paths
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    games_file = workspace_root / "games.tsv"
    
    # Initialize service
    rawg_api_key = os.getenv("RAWG_API_KEY", "")
    if not rawg_api_key:
        print("Warning: RAWG_API_KEY not set. Set it as environment variable.")
        print("Continuing anyway, will use TheGamesDB fallback...")
    
    service = GameDataService(api_key=rawg_api_key)
    
    # Load games
    games = load_games_from_tsv(games_file)
    print(f"Loaded {len(games)} games from games.tsv")
    
    # Load existing descriptions
    existing_descriptions = service.descriptions
    print(f"Found {len(existing_descriptions)} existing descriptions")
    
    # Filter games that need data
    games_to_fetch = []
    for game in games:
        title = game["title"]
        needs_description = title not in existing_descriptions or len(existing_descriptions.get(title, "")) < 100
        
        # Check if images exist
        existing_images = service._get_existing_images(title)
        has_cover = len(existing_images.get("cover", [])) > 0
        has_enough_screenshots = len(existing_images.get("screenshots", [])) >= 4
        needs_images = not (has_cover and has_enough_screenshots)
        
        if needs_description or needs_images:
            games_to_fetch.append(game)
    
    print(f"\nNeed to fetch data for {len(games_to_fetch)} games")
    print("This may take a while due to API rate limiting...")
    print("Fetching both descriptions and images...")
    
    # Fetch data
    fetched_desc = 0
    fetched_images = 0
    skipped = 0
    
    for i, game in enumerate(games_to_fetch, 1):
        title = game["title"]
        console = game["console"]
        
        print(f"\n[{i}/{len(games_to_fetch)}] Processing: {title} ({console})")
        
        # Check what we need
        needs_description = title not in existing_descriptions or len(existing_descriptions.get(title, "")) < 100
        existing_images = service._get_existing_images(title)
        has_cover = len(existing_images.get("cover", [])) > 0
        has_enough_screenshots = len(existing_images.get("screenshots", [])) >= 4
        needs_images = not (has_cover and has_enough_screenshots)
        
        # Fetch description if needed
        if needs_description:
            try:
                description = service.fetch_game_description(title, console)
                if len(description) > 100:
                    fetched_desc += 1
                    print(f"  ✓ Got description ({len(description)} chars)")
                else:
                    print(f"  ⚠ Short description")
            except Exception as e:
                print(f"  ✗ Error fetching description: {e}")
        else:
            print(f"  ⊘ Description already cached")
        
        # Fetch images if needed
        if needs_images:
            try:
                images = service.fetch_game_images(title, max_images=5, console=console, force_refresh=False)
                if len(images) > 0:
                    fetched_images += 1
                    print(f"  ✓ Got {len(images)} images")
                else:
                    print(f"  ⚠ No images fetched")
            except Exception as e:
                print(f"  ✗ Error fetching images: {e}")
        else:
            print(f"  ⊘ Images already cached")
        
        # Save periodically (every 10 games)
        if i % 10 == 0:
            service._save_descriptions()
            print(f"\n  Saved progress... ({fetched_desc} descriptions, {fetched_images} image sets)")
    
    # Final save
    service._save_descriptions()
    
    print(f"\n\nDone!")
    print(f"Fetched: {fetched_desc} descriptions")
    print(f"Fetched: {fetched_images} image sets")
    print(f"Total descriptions: {len(service.descriptions)}")

if __name__ == "__main__":
    main()

