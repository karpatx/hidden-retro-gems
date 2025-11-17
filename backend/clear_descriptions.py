"""
Quick script to clear bad/fallback descriptions from cache
Run this to delete generic fallback descriptions so they can be re-fetched
"""
import json
from pathlib import Path

def is_fallback_description(description: str) -> bool:
    """Check if a description is a generic fallback"""
    fallback_phrases = [
        "egy játék a",
        "egyedi játékmenettel",
        "izgalmas kihívásokkal",
        "retro játékok szerelmeseinek",
        "egy érdekes és egyedi játék"
    ]
    desc_lower = description.lower()
    return any(phrase in desc_lower for phrase in fallback_phrases) or len(description) < 100

def main():
    script_dir = Path(__file__).parent
    descriptions_file = script_dir / "game_data" / "descriptions.json"
    
    if descriptions_file.exists():
        # Load existing to show count
        with open(descriptions_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
        
        print(f"Found {len(existing)} descriptions in cache.")
        
        # Create backup
        backup_file = descriptions_file.with_suffix('.json.backup')
        print(f"Creating backup: {backup_file.name}")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        # Filter out fallback descriptions
        good_descriptions = {}
        removed_count = 0
        
        for title, description in existing.items():
            if is_fallback_description(description):
                removed_count += 1
                print(f"  Removing fallback: {title[:50]}...")
            else:
                good_descriptions[title] = description
        
        # Save filtered descriptions
        print(f"\nRemoving {removed_count} fallback descriptions...")
        with open(descriptions_file, "w", encoding="utf-8") as f:
            json.dump(good_descriptions, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Removed {removed_count} fallback descriptions!")
        print(f"✓ Kept {len(good_descriptions)} good descriptions")
        print(f"✓ Backup saved to: {backup_file.name}")
        print("\nNow run: python fetch_all_game_data.py")
    else:
        print("No descriptions.json file found. Nothing to clear.")

if __name__ == "__main__":
    main()

