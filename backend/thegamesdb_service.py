"""
TheGamesDB API service for fetching retro game images and descriptions
Alternative to RAWG API, specialized for retro games
"""
import requests
import os
import re
from pathlib import Path
from typing import List, Optional, Dict
import hashlib


class TheGamesDBService:
    def __init__(self, api_key: Optional[str] = None, images_dir: str = "static/images/games"):
        """
        Initialize TheGamesDB service
        
        Args:
            api_key: TheGamesDB API key (get from https://forums.thegamesdb.net/)
            images_dir: Directory to save images
        """
        backend_dir = Path(__file__).parent
        self.images_dir = backend_dir / images_dir
        self.api_key = api_key or os.getenv("THEGAMESDB_API_KEY", "")
        self.base_url = "https://api.thegamesdb.net/v1"
        
        # Create images directory
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_game_name(self, game_title: str) -> str:
        """Create a safe filename from game title"""
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in game_title)
        return safe_name.strip().replace(' ', '_')
    
    def _get_game_images_dir(self, game_title: str) -> Path:
        """Get the directory for a specific game's images"""
        safe_name = self._sanitize_game_name(game_title)
        game_dir = self.images_dir / safe_name
        game_dir.mkdir(parents=True, exist_ok=True)
        return game_dir
    
    def _download_image(self, url: str, save_path: Path) -> bool:
        """Download an image from URL"""
        try:
            headers = {
                'User-Agent': 'HiddenGem/1.0 (https://github.com/yourusername/hidden-gem)'
            }
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            return False
    
    def _map_platform_name(self, console: str) -> Optional[str]:
        """Map internal console names to TheGamesDB platform IDs"""
        platform_mapping = {
            "NES": "7",
            "SNES": "6",
            "N64": "4",
            "Gamecube": "21",
            "Wii": "36",
            "Wii U": "41",
            "Switch": "130",
            "Gameboy": "33",
            "GBA": "24",
            "DS": "20",
            "3DS": "37",
            "PS1": "7",
            "PS2": "8",
            "PS3": "9",
            "PSP": "13",
            "PS Vita": "46",
            "XBOX": "11",
            "XBOX360": "12",
            "Megadrive": "18",
            "Dreamcast": "23",
            "Sega Master System": "64",
        }
        return platform_mapping.get(console)
    
    def search_game(self, game_title: str, console: Optional[str] = None) -> Optional[Dict]:
        """Search for a game in TheGamesDB"""
        try:
            url = f"{self.base_url}/Games/ByGameName"
            params = {
                "name": game_title
            }
            
            # Add API key if available (some endpoints may work without it)
            if self.api_key:
                params["apikey"] = self.api_key
            
            if console:
                platform_id = self._map_platform_name(console)
                if platform_id:
                    params["platform"] = platform_id
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200 and data.get("data", {}).get("games"):
                games = data["data"]["games"]
                # Return first match
                return games[0] if games else None
            
            return None
        except Exception as e:
            print(f"Error searching TheGamesDB for {game_title}: {e}")
            return None
    
    def get_game_images(self, game_title: str, console: Optional[str] = None, max_images: int = 4) -> List[str]:
        """Get images for a game from TheGamesDB"""
        game_data = self.search_game(game_title, console)
        if not game_data:
            return []
        
        game_id = game_data.get("id")
        if not game_id:
            return []
        
        # Get game images
        try:
            url = f"{self.base_url}/Games/Images"
            params = {
                "games_id": game_id
            }
            
            # Add API key if available
            if self.api_key:
                params["apikey"] = self.api_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 200:
                return []
            
            images_data = data.get("data", {}).get("images", {})
            if not images_data:
                return []
            
            game_dir = self._get_game_images_dir(game_title)
            downloaded = []
            
            # Get box art (front cover)
            boxart = images_data.get("boxart", {})
            if boxart:
                # Get front box art
                front_boxart = boxart.get("front", {})
                if front_boxart:
                    image_url = front_boxart.get("original", {}).get("url", "")
                    if image_url:
                        # TheGamesDB returns relative URLs, need to prepend base URL
                        if not image_url.startswith("http"):
                            image_url = f"https://cdn.thegamesdb.net/images/original/{image_url}"
                        
                        filename = f"boxart_front_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg"
                        save_path = game_dir / filename
                        if not save_path.exists():
                            if self._download_image(image_url, save_path):
                                downloaded.append(str(save_path))
                        else:
                            downloaded.append(str(save_path))
            
            # Get screenshots
            screenshots = images_data.get("screenshots", {})
            if screenshots:
                screenshot_list = screenshots.get("screenshot", [])
                if not isinstance(screenshot_list, list):
                    screenshot_list = [screenshot_list]
                
                for screenshot in screenshot_list[:max_images]:
                    if len(downloaded) >= max_images:
                        break
                    
                    image_url = screenshot.get("original", {}).get("url", "")
                    if image_url:
                        if not image_url.startswith("http"):
                            image_url = f"https://cdn.thegamesdb.net/images/original/{image_url}"
                        
                        filename = f"screenshot_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg"
                        save_path = game_dir / filename
                        if not save_path.exists():
                            if self._download_image(image_url, save_path):
                                downloaded.append(str(save_path))
                        else:
                            downloaded.append(str(save_path))
            
            return downloaded[:max_images]
            
        except Exception as e:
            print(f"Error fetching images from TheGamesDB: {e}")
            return []


    def get_game_description(self, game_title: str, console: Optional[str] = None) -> Optional[str]:
        """Get game description from TheGamesDB
        
        Args:
            game_title: Title of the game
            console: Console/platform name
        
        Returns:
            Game description (1-2 paragraphs) or None if not found
        """
        game_data = self.search_game(game_title, console)
        if not game_data:
            return None
        
        game_id = game_data.get("id")
        if not game_id:
            return None
        
        # Get game details including overview/description
        try:
            url = f"{self.base_url}/Games/ByGameID"
            params = {
                "id": game_id,
                "fields": "overview"
            }
            
            # Add API key if available
            if self.api_key:
                params["apikey"] = self.api_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 200:
                return None
            
            games_data = data.get("data", {}).get("games", [])
            if not games_data:
                return None
            
            game_info = games_data[0]
            overview = game_info.get("overview", "")
            
            if not overview:
                return None
            
            # Clean up the description
            # Remove HTML tags
            overview = re.sub(r'<[^>]+>', '', overview)
            # Remove extra whitespace
            overview = re.sub(r'\s+', ' ', overview).strip()
            
            # Format as 1-2 paragraphs (4-8 sentences)
            sentence_endings = r'[.!?]+'
            sentences = re.split(sentence_endings, overview)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) >= 4:
                target_sentences = min(len(sentences), 8)
                selected_sentences = sentences[:target_sentences]
                
                # Try to create 2 paragraphs if we have enough sentences
                if len(selected_sentences) >= 6:
                    first_para = '. '.join(selected_sentences[:4]) + '.'
                    second_para = '. '.join(selected_sentences[4:]) + '.'
                    return f"{first_para}\n\n{second_para}"
                else:
                    return '. '.join(selected_sentences) + '.'
            else:
                return '. '.join(sentences) + '.'
                
        except Exception as e:
            print(f"Error fetching description from TheGamesDB: {e}")
            return None

# Example usage
if __name__ == "__main__":
    service = TheGamesDBService()
    images = service.get_game_images("Super Mario Bros", "NES")
    print(f"Downloaded {len(images)} images")
    
    description = service.get_game_description("Super Mario Bros", "NES")
    if description:
        print(f"\nDescription:\n{description}")

