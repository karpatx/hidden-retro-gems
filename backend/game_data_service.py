"""
Game data service for fetching game information and images
Uses RAWG API as primary source with caching
"""
import requests
import os
import json
import time
from pathlib import Path
from typing import List, Optional, Dict
from urllib.parse import urlparse
import hashlib


class GameDataService:
    def __init__(
        self, 
        cache_dir: str = "game_data", 
        images_dir: str = "static/images/games",
        api_key: Optional[str] = None
    ):
        # Use absolute paths relative to backend directory
        backend_dir = Path(__file__).parent
        self.cache_dir = backend_dir / cache_dir
        self.images_dir = backend_dir / images_dir
        self.descriptions_file = self.cache_dir / "descriptions.json"
        self.api_key = api_key or os.getenv("RAWG_API_KEY", "")
        
        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Load cached descriptions
        self.descriptions = self._load_descriptions()
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests (5 requests/second max)
        
        # RAWG API base URL
        self.rawg_base_url = "https://api.rawg.io/api/games"
    
    def _load_descriptions(self) -> Dict[str, str]:
        """Load cached descriptions from JSON file"""
        if self.descriptions_file.exists():
            try:
                with open(self.descriptions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_descriptions(self):
        """Save descriptions to JSON file"""
        with open(self.descriptions_file, "w", encoding="utf-8") as f:
            json.dump(self.descriptions, f, ensure_ascii=False, indent=2)
    
    def _rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
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
    
    def _get_existing_images(self, game_title: str) -> List[str]:
        """Get list of existing cached images for a game"""
        game_dir = self._get_game_images_dir(game_title)
        if not game_dir.exists():
            return []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        images = []
        for file in game_dir.iterdir():
            if file.suffix.lower() in image_extensions:
                images.append(str(file))
        
        return sorted(images)
    
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
    
    def _search_game_rawg(self, game_title: str, console: Optional[str] = None) -> Optional[Dict]:
        """Search for a game in RAWG API"""
        if not self.api_key:
            print("Warning: RAWG API key not set. Set RAWG_API_KEY environment variable or pass api_key parameter.")
            return None
        
        try:
            self._rate_limit()
            
            # Build search query
            search_query = game_title
            params = {
                "key": self.api_key,
                "search": search_query,
                "page_size": 5
            }
            
            response = requests.get(
                f"{self.rawg_base_url}",
                params=params,
                timeout=10
            )
            
            if response.status_code == 429:
                print(f"Rate limit exceeded for RAWG API. Waiting...")
                time.sleep(1)
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('results'):
                return None
            
            # Try to find best match
            results = data['results']
            for result in results:
                # Check if title matches (case insensitive)
                if result['name'].lower() == game_title.lower():
                    return result
            
            # If no exact match, return first result
            return results[0]
            
        except Exception as e:
            print(f"Error searching RAWG API for {game_title}: {e}")
            return None
    
    def _get_game_details_rawg(self, game_id: int) -> Optional[Dict]:
        """Get detailed game information from RAWG API"""
        if not self.api_key:
            return None
        
        try:
            self._rate_limit()
            
            params = {"key": self.api_key}
            response = requests.get(
                f"{self.rawg_base_url}/{game_id}",
                params=params,
                timeout=10
            )
            
            if response.status_code == 429:
                print(f"Rate limit exceeded for RAWG API. Waiting...")
                time.sleep(1)
                return None
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error fetching game details from RAWG: {e}")
            return None
    
    def get_game_description(self, game_title: str, console: Optional[str] = None) -> str:
        """Get game description from RAWG API or cache"""
        # Check cache first
        if game_title in self.descriptions:
            return self.descriptions[game_title]
        
        # Try RAWG API
        game_data = self._search_game_rawg(game_title, console)
        if game_data:
            # Get full details
            game_id = game_data.get('id')
            if game_id:
                details = self._get_game_details_rawg(game_id)
                if details:
                    description = details.get('description_raw') or details.get('description', '')
                    if description:
                        # Clean up HTML tags if present
                        import re
                        description = re.sub(r'<[^>]+>', '', description)
                        # Take first 3 sentences
                        sentences = description.split('.')[:3]
                        description = '. '.join(s for s in sentences if s.strip()).strip()
                        if description and not description.endswith('.'):
                            description += '.'
                        
                        self.descriptions[game_title] = description
                        self._save_descriptions()
                        return description
        
        # Fallback description
        description = f"{game_title} egy játék a {console} platformon." if console else f"{game_title} egy játék."
        self.descriptions[game_title] = description
        self._save_descriptions()
        return description
    
    def get_game_images(self, game_title: str, max_images: int = 4) -> List[str]:
        """Get cached images for a game, fetching new ones if needed"""
        # Ensure at least 3-4 images
        if max_images < 3:
            max_images = 3
        
        existing = self._get_existing_images(game_title)
        
        # If we already have enough images, return them
        if len(existing) >= max_images:
            return existing[:max_images]
        
        # Try to fetch from RAWG - try to get more to ensure we reach max_images
        needed = max_images - len(existing)
        # Request more than needed in case some downloads fail
        new_images = self._fetch_images_from_rawg(game_title, max(needed, 4))
        existing.extend(new_images)
        
        # Return up to max_images (but try to get as many as possible)
        return existing[:max_images]
    
    def _fetch_images_from_rawg(self, game_title: str, max_images: int = 4) -> List[str]:
        """Fetch images from RAWG API for a game"""
        game_data = self._search_game_rawg(game_title)
        if not game_data:
            return []
        
        game_id = game_data.get('id')
        if not game_id:
            return []
        
        # Get full game details to access screenshots
        details = self._get_game_details_rawg(game_id)
        if not details:
            return []
        
        game_dir = self._get_game_images_dir(game_title)
        downloaded = []
        
        # Get background image (box art/cover) - this is usually the best quality
        background_image = details.get('background_image')
        if background_image:
            filename = f"background_{hashlib.md5(background_image.encode()).hexdigest()[:8]}.jpg"
            save_path = game_dir / filename
            if not save_path.exists():
                if self._download_image(background_image, save_path):
                    downloaded.append(str(save_path))
            else:
                downloaded.append(str(save_path))
        
        # Get screenshots - try to get more than needed in case some fail
        screenshots = details.get('short_screenshots', [])
        if not screenshots:
            screenshots = details.get('screenshots', [])
        
        # Try to download more screenshots than needed to ensure we get at least max_images
        # Try up to max_images * 2 screenshots to account for failures
        screenshots_to_try = min(len(screenshots), max(max_images * 2, 10))
        
        for screenshot in screenshots[:screenshots_to_try]:
            if len(downloaded) >= max_images:
                break
            
            image_url = screenshot.get('image') if isinstance(screenshot, dict) else screenshot
            if not image_url:
                continue
            
            # Use higher quality image if available
            if isinstance(screenshot, dict):
                # Prefer 'full' quality if available, otherwise 'image'
                image_url = screenshot.get('full') or screenshot.get('image') or image_url
            
            filename = f"screenshot_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg"
            save_path = game_dir / filename
            
            # Skip if we already have this image
            if save_path.exists():
                downloaded.append(str(save_path))
                continue
            
            # Try to download the image
            if self._download_image(image_url, save_path):
                downloaded.append(str(save_path))
        
        # If we still don't have enough, try to get additional images
        # Sometimes there are alternative image sources
        if len(downloaded) < max_images:
            # Try getting platform-specific images or additional screenshots
            additional_images = details.get('background_image_additional', None)
            if additional_images and len(downloaded) < max_images:
                filename = f"background_additional_{hashlib.md5(additional_images.encode()).hexdigest()[:8]}.jpg"
                save_path = game_dir / filename
                if not save_path.exists():
                    if self._download_image(additional_images, save_path):
                        downloaded.append(str(save_path))
                else:
                    downloaded.append(str(save_path))
        
        return downloaded[:max_images]  # Return at most max_images
    
    def get_game_info(self, game_title: str, console: Optional[str] = None, max_images: int = 4) -> Dict:
        """Get complete game information (description + images)"""
        # Ensure at least 3-4 images
        if max_images < 3:
            max_images = 3
        description = self.get_game_description(game_title, console)
        images = self.get_game_images(game_title, max_images)
        
        # Convert absolute paths to relative URLs
        # static_dir is backend/static, images_dir is backend/static/images/games
        # So we need to get relative path from static_dir
        backend_dir = Path(__file__).parent
        static_dir = backend_dir / "static"
        
        image_urls = []
        for img_path in images:
            try:
                img_path_obj = Path(img_path)
                rel_path = img_path_obj.relative_to(static_dir)
                image_urls.append(f"/static/{rel_path.as_posix()}")
            except Exception:
                image_urls.append(img_path)
        
        return {
            "title": game_title,
            "description": description,
            "images": image_urls,
            "image_count": len(image_urls)
        }

