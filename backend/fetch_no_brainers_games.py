"""
Script to fetch game data (descriptions and images) for popular games from games.tsv
that match keywords from no_brainers.tsv

This script:
1. Loads games from games.tsv
2. Loads keywords from no_brainers.tsv
3. Identifies games that match the keywords
4. Fetches descriptions, cover images, and gameplay screenshots for these games
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


def load_no_brainers_keywords(no_brainers_file: Path):
    """Load keywords from no_brainers.tsv file"""
    keywords = []
    if not no_brainers_file.exists():
        return keywords
    
    with open(no_brainers_file, "r", encoding="utf-8") as f:
        keywords = [line.strip().lower() for line in f.readlines() if line.strip()]
    
    return keywords


def is_no_brainer_game(title: str, keywords: list) -> bool:
    """Check if a game matches any no_brainers keywords"""
    if not keywords:
        return False
    
    title_lower = title.lower().strip()
    title_normalized = "".join(c if c.isalnum() or c.isspace() else " " for c in title_lower)
    
    for keyword in keywords:
        keyword_normalized = "".join(c if c.isalnum() or c.isspace() else " " for c in keyword.lower().strip())
        
        # Check if keyword is contained in title (normalized)
        if keyword_normalized in title_normalized:
            return True
        
        # Check individual words from keyword
        keyword_words = keyword_normalized.split()
        title_words = title_normalized.split()
        
        # Check if all keyword words appear in title (for multi-word keywords like "donkey kong")
        if len(keyword_words) > 1:
            if all(kw in title_words for kw in keyword_words if len(kw) > 2):
                return True
        elif len(keyword_words) == 1 and keyword_words[0] in title_words:
            # Single word match (like "mario", "zelda")
            return True
    
    return False


def main():
    """Main function to fetch data for no_brainer games"""
    # Get paths
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    games_file = workspace_root / "games.tsv"
    no_brainers_file = workspace_root / "no_brainers.tsv"
    
    # Initialize service
    rawg_api_key = os.getenv("RAWG_API_KEY", "")
    if not rawg_api_key:
        print("Warning: RAWG_API_KEY not set. Set it as environment variable.")
        print("Will use TheGamesDB fallback, but results may be limited...")
    
    service = GameDataService(api_key=rawg_api_key)
    
    # Load games and keywords
    print("Loading games from games.tsv...")
    all_games = load_games_from_tsv(games_file)
    print(f"Loaded {len(all_games)} games from games.tsv")
    
    print("\nLoading keywords from no_brainers.tsv...")
    keywords = load_no_brainers_keywords(no_brainers_file)
    print(f"Loaded {len(keywords)} keywords from no_brainers.tsv")
    
    # Find matching games
    print("\nIdentifying no_brainer games...")
    no_brainer_games = []
    for game in all_games:
        if is_no_brainer_game(game["title"], keywords):
            no_brainer_games.append(game)
    
    print(f"Found {len(no_brainer_games)} no_brainer games")
    
    if len(no_brainer_games) == 0:
        print("No matching games found. Exiting.")
        return
    
    # Group by platform for better reporting
    games_by_platform = {}
    for game in no_brainer_games:
        platform = game["console"]
        if platform not in games_by_platform:
            games_by_platform[platform] = []
        games_by_platform[platform].append(game)
    
    print("\nGames by platform:")
    for platform, games in sorted(games_by_platform.items()):
        print(f"  {platform}: {len(games)} games")
    
    # Load existing descriptions and images
    existing_descriptions = service.descriptions
    print(f"\nFound {len(existing_descriptions)} existing descriptions in cache")
    
    # Filter games that need data
    games_to_fetch = []
    for game in no_brainer_games:
        title = game["title"]
        
        # Check if description is needed
        needs_description = title not in existing_descriptions or len(existing_descriptions.get(title, "")) < 100
        
        # Check if images are needed
        existing_images = service._get_existing_images(title)
        has_cover = len(existing_images.get("cover", [])) > 0
        has_enough_screenshots = len(existing_images.get("screenshots", [])) >= 4
        needs_images = not (has_cover and has_enough_screenshots)
        
        if needs_description or needs_images:
            games_to_fetch.append(game)
    
    total_games = len(no_brainer_games)
    needs_fetch = len(games_to_fetch)
    already_complete = total_games - needs_fetch
    
    print(f"\nStatus:")
    print(f"  Total no_brainer games: {total_games}")
    print(f"  Already have complete data: {already_complete}")
    print(f"  Need to fetch data: {needs_fetch}")
    
    if needs_fetch == 0:
        print("\nAll games already have complete data!")
        return
    
    print(f"\nFetching data for {needs_fetch} games...")
    print("This may take a while due to API rate limiting...")
    print("Fetching descriptions, cover images, and 4-5 gameplay screenshots for each game...\n")
    
    # Fetch data
    fetched_desc = 0
    fetched_images = 0
    skipped_desc = 0
    skipped_images = 0
    
    for i, game in enumerate(games_to_fetch, 1):
        title = game["title"]
        console = game["console"]
        manufacturer = game["manufacturer"]
        
        print(f"\n[{i}/{needs_fetch}] Processing: {title} ({console})")
        
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
                    skipped_desc += 1
                    print(f"  ⚠ Short description ({len(description)} chars)")
            except Exception as e:
                skipped_desc += 1
                print(f"  ✗ Error fetching description: {e}")
        else:
            print(f"  ⊘ Description already cached")
        
        # Fetch images if needed (1 cover + 4-5 screenshots = 5-6 total)
        if needs_images:
            try:
                # Request 6 images total to ensure we get 1 cover + at least 4-5 screenshots
                images = service.fetch_game_images(title, max_images=6, console=console, force_refresh=False)
                if len(images) > 0:
                    fetched_images += 1
                    print(f"  ✓ Got {len(images)} images")
                    
                    # Check what we got
                    game_images = service._get_existing_images(title)
                    cover_count = len(game_images.get("cover", []))
                    screenshot_count = len(game_images.get("screenshots", []))
                    print(f"     - Cover images: {cover_count}")
                    print(f"     - Screenshots: {screenshot_count}")
                else:
                    skipped_images += 1
                    print(f"  ⚠ No images fetched")
            except Exception as e:
                skipped_images += 1
                print(f"  ✗ Error fetching images: {e}")
        else:
            print(f"  ⊘ Images already cached")
        
        # Save periodically (every 10 games)
        if i % 10 == 0:
            service._save_descriptions()
            print(f"\n  Saved progress... ({fetched_desc} descriptions, {fetched_images} image sets)")
    
    # Final save
    service._save_descriptions()
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"Total no_brainer games processed: {total_games}")
    print(f"Descriptions: {fetched_desc} fetched, {skipped_desc} skipped/failed")
    print(f"Images: {fetched_images} fetched, {skipped_images} skipped/failed")
    print(f"Total descriptions in cache: {len(service.descriptions)}")
    
    # Final summary by platform
    print("\nFinal summary by platform:")
    for platform, games in sorted(games_by_platform.items()):
        complete_count = 0
        for game in games:
            title = game["title"]
            existing_images = service._get_existing_images(title)
            has_cover = len(existing_images.get("cover", [])) > 0
            has_enough_screenshots = len(existing_images.get("screenshots", [])) >= 4
            has_description = title in service.descriptions and len(service.descriptions.get(title, "")) > 100
            if has_cover and has_enough_screenshots and has_description:
                complete_count += 1
        
        print(f"  {platform}: {complete_count}/{len(games)} games have complete data")


if __name__ == "__main__":
    main()

