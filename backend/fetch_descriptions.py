"""
Script to fetch and cache game descriptions for all games
This can be run once to populate descriptions.json with detailed descriptions
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
    """Fetch descriptions for all games"""
    # Get paths
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    games_file = workspace_root / "games.tsv"
    
    # Initialize service
    rawg_api_key = os.getenv("RAWG_API_KEY", "")
    if not rawg_api_key:
        print("Warning: RAWG_API_KEY not set. Set it as environment variable.")
        print("Continuing anyway, but descriptions may be limited...")
    
    service = GameDataService(api_key=rawg_api_key)
    
    # Load games
    games = load_games_from_tsv(games_file)
    print(f"Loaded {len(games)} games from games.tsv")
    
    # Load existing descriptions
    existing_descriptions = service.descriptions
    print(f"Found {len(existing_descriptions)} existing descriptions")
    
    # Filter games that need descriptions
    games_to_fetch = []
    for game in games:
        title = game["title"]
        if title not in existing_descriptions or len(existing_descriptions.get(title, "")) < 100:
            games_to_fetch.append(game)
    
    print(f"\nNeed to fetch descriptions for {len(games_to_fetch)} games")
    print("This may take a while due to API rate limiting...")
    
    # Fetch descriptions
    fetched = 0
    skipped = 0
    
    for i, game in enumerate(games_to_fetch, 1):
        title = game["title"]
        console = game["console"]
        
        print(f"\n[{i}/{len(games_to_fetch)}] Fetching description for: {title} ({console})")
        
        try:
            description = service.fetch_game_description(title, console)
            
            if len(description) > 100:
                fetched += 1
                print(f"  ✓ Got description ({len(description)} chars)")
            else:
                skipped += 1
                print(f"  ⚠ Short description, may need manual editing")
        except Exception as e:
            skipped += 1
            print(f"  ✗ Error: {e}")
        
        # Save periodically (every 10 games)
        if i % 10 == 0:
            service._save_descriptions()
            print(f"\n  Saved progress... ({fetched} fetched, {skipped} skipped)")
    
    # Final save
    service._save_descriptions()
    
    print(f"\n\nDone!")
    print(f"Fetched: {fetched} descriptions")
    print(f"Skipped/Failed: {skipped} descriptions")
    print(f"Total descriptions: {len(service.descriptions)}")

if __name__ == "__main__":
    main()

