"""
Script to reset and re-fetch all game descriptions
This will delete existing descriptions and fetch new ones from APIs
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
    """Reset and re-fetch all descriptions"""
    # Get paths
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    games_file = workspace_root / "games.tsv"
    descriptions_file = script_dir / "game_data" / "descriptions.json"
    
    print("=" * 60)
    print("RESET AND RE-FETCH GAME DESCRIPTIONS")
    print("=" * 60)
    
    # Ask for confirmation
    if descriptions_file.exists():
        with open(descriptions_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"\nFound {len(existing)} existing descriptions in cache.")
        response = input("\nDo you want to DELETE all existing descriptions and re-fetch? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
        
        # Backup existing descriptions (just in case)
        backup_file = descriptions_file.with_suffix('.json.backup')
        print(f"\nCreating backup: {backup_file}")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    # Initialize service with empty descriptions
    rawg_api_key = os.getenv("RAWG_API_KEY", "")
    if not rawg_api_key:
        print("\nWarning: RAWG_API_KEY not set. Set it as environment variable.")
        print("Will try to use TheGamesDB fallback...")
    
    # Create new service instance
    service = GameDataService(api_key=rawg_api_key)
    
    # Clear all descriptions
    print("\nClearing all cached descriptions...")
    service.descriptions = {}
    service._save_descriptions()
    print("✓ Cache cleared")
    
    # Load games
    games = load_games_from_tsv(games_file)
    print(f"\nLoaded {len(games)} games from games.tsv")
    
    # Fetch descriptions
    print("\nStarting to fetch descriptions...")
    print("This will use RAWG API first, then TheGamesDB as fallback.")
    print("This may take a while due to API rate limiting...\n")
    
    fetched = 0
    skipped = 0
    failed = 0
    
    for i, game in enumerate(games, 1):
        title = game["title"]
        console = game["console"]
        
        print(f"[{i}/{len(games)}] {title} ({console})")
        
        try:
            # Force fetch (bypass cache since we cleared it)
            description = service.get_game_description(title, console)
            
            if len(description) > 100:
                fetched += 1
                print(f"  ✓ Got description ({len(description)} chars)")
            else:
                skipped += 1
                print(f"  ⚠ Short description ({len(description)} chars)")
        except Exception as e:
            failed += 1
            print(f"  ✗ Error: {e}")
        
        # Save periodically (every 10 games)
        if i % 10 == 0:
            service._save_descriptions()
            print(f"\n  → Saved progress... ({fetched} fetched, {skipped} short, {failed} failed)\n")
    
    # Final save
    service._save_descriptions()
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"Total games: {len(games)}")
    print(f"✓ Fetched (good): {fetched}")
    print(f"⚠ Short descriptions: {skipped}")
    print(f"✗ Failed: {failed}")
    print(f"\nTotal descriptions saved: {len(service.descriptions)}")
    
    if backup_file.exists():
        print(f"\nBackup saved to: {backup_file}")

if __name__ == "__main__":
    main()

