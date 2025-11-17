"""
Game data service for fetching game information and images
Uses RAWG API as primary source with caching
Supports TheGamesDB as fallback for retro games
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
    
    def _get_existing_images(self, game_title: str) -> Dict[str, List[str]]:
        """Get list of existing cached images for a game, categorized by type
        
        Returns:
            Dict with 'cover' and 'screenshots' keys containing lists of image paths
        """
        game_dir = self._get_game_images_dir(game_title)
        if not game_dir.exists():
            return {"cover": [], "screenshots": []}
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        cover_images = []
        screenshot_images = []
        
        for file in game_dir.iterdir():
            if file.suffix.lower() not in image_extensions:
                continue
            
            filename = file.name.lower()
            # Prioritize cover/boxart images
            if any(keyword in filename for keyword in ['cover', 'boxart', 'background', 'poster', 'artwork']):
                cover_images.append(str(file))
            else:
                screenshot_images.append(str(file))
        
        # Sort: cover images first, then screenshots
        cover_images = sorted(cover_images)
        screenshot_images = sorted(screenshot_images)
        
        return {
            "cover": cover_images,
            "screenshots": screenshot_images
        }
    
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
        """Get game description from cache only (no runtime fetching)
        
        Returns a 1-2 paragraph description (4-8 sentences) about the game.
        Use fetch_game_description() to download and cache descriptions.
        """
        # Only read from cache - no runtime fetching
        if game_title in self.descriptions:
            cached_desc = self.descriptions[game_title]
            # Check if it's a generic fallback description
            fallback_phrases = [
                "egy játék a",
                "egyedi játékmenettel",
                "izgalmas kihívásokkal",
                "retro játékok szerelmeseinek"
            ]
            is_fallback = any(phrase in cached_desc.lower() for phrase in fallback_phrases)
            
            # Only use cache if it's substantial AND not a fallback
            if len(cached_desc) > 100 and not is_fallback:
                return cached_desc
        
        # Return empty string if not in cache (frontend can handle this)
        return ""
    
    def fetch_game_description(self, game_title: str, console: Optional[str] = None) -> str:
        """Fetch game description from APIs and cache it (for use in scripts, not runtime)
        
        Returns a 1-2 paragraph description (4-8 sentences) about the game.
        """
        # Try RAWG API first (only if API key is available)
        # If no API key, skip directly to TheGamesDB
        if not self.api_key:
            print("RAWG API key not set, using TheGamesDB fallback...")
            rawg_success = False
        else:
            rawg_success = False
            try:
                game_data = self._search_game_rawg(game_title, console)
                if game_data:
                    # Get full details
                    game_id = game_data.get('id')
                    if game_id:
                        details = self._get_game_details_rawg(game_id)
                        if details:
                            description = details.get('description_raw') or details.get('description', '')
                            if description and len(description.strip()) > 50:  # At least some content
                                # Clean up HTML tags if present
                                import re
                                description = re.sub(r'<[^>]+>', '', description)
                                
                                # Remove extra whitespace and newlines
                                description = re.sub(r'\s+', ' ', description).strip()
                                
                                # Split into sentences
                                # Handle common sentence endings
                                sentence_endings = r'[.!?]+'
                                sentences = re.split(sentence_endings, description)
                                sentences = [s.strip() for s in sentences if s.strip()]
                                
                                # Target: 1-2 paragraphs = 4-8 sentences
                                # First paragraph: 3-4 sentences (introduction, gameplay overview)
                                # Second paragraph: 2-4 sentences (story, features, or additional details)
                                target_sentences = min(len(sentences), 8)
                                
                                if target_sentences >= 4:
                                    # Take first 4-8 sentences
                                    selected_sentences = sentences[:target_sentences]
                                    
                                    # Try to create 2 paragraphs if we have enough sentences
                                    if len(selected_sentences) >= 6:
                                        # First paragraph: first 3-4 sentences
                                        first_para = '. '.join(selected_sentences[:4]) + '.'
                                        # Second paragraph: remaining sentences
                                        second_para = '. '.join(selected_sentences[4:]) + '.'
                                        description = f"{first_para}\n\n{second_para}"
                                    else:
                                        # Single paragraph with 4-5 sentences
                                        description = '. '.join(selected_sentences) + '.'
                                else:
                                    # If we have fewer sentences, use what we have
                                    description = '. '.join(sentences) + '.'
                                
                                # Ensure description ends properly
                                if description and not description.endswith('.'):
                                    description += '.'
                                
                                # Only cache if description is substantial
                                if len(description) > 100:
                                    self.descriptions[game_title] = description
                                    self._save_descriptions()
                                    rawg_success = True
                                    return description
            except Exception as e:
                print(f"Error fetching description from RAWG API: {e}")
                rawg_success = False
        
        # Fallback: Try TheGamesDB if RAWG failed, didn't return a good description, or no API key
        if not rawg_success:
            try:
                from thegamesdb_service import TheGamesDBService
                tgdb_service = TheGamesDBService()
                tgdb_description = tgdb_service.get_game_description(game_title, console)
                
                if tgdb_description and len(tgdb_description) > 100:
                    # Cache the description
                    self.descriptions[game_title] = tgdb_description
                    self._save_descriptions()
                    print(f"✓ Got description from TheGamesDB fallback")
                    return tgdb_description
                else:
                    print(f"⚠ TheGamesDB fallback didn't return a good description")
            except Exception as e:
                print(f"Error using TheGamesDB fallback for description: {e}")
        
        # Final fallback: Try to create a better fallback description
        if console:
            description = f"{game_title} egy játék a {console} platformon. Ez a játék egyedi játékmenettel és izgalmas kihívásokkal rendelkezik, amelyek a retro játékok szerelmeseinek szólnak."
        else:
            description = f"{game_title} egy érdekes és egyedi játék, amely érdemes lehet kipróbálni."
        
        self.descriptions[game_title] = description
        self._save_descriptions()
        return description
    
    def get_game_images(self, game_title: str, max_images: int = 5, console: Optional[str] = None, use_fallback: bool = True, force_refresh: bool = False) -> List[str]:
        """Get cached images for a game (no runtime fetching)
        
        Args:
            game_title: Title of the game
            max_images: Maximum number of images to return (default: 5, including 1 cover + 4 screenshots)
            console: Console/platform name (unused in cache-only mode)
            use_fallback: Unused in cache-only mode
            force_refresh: Unused in cache-only mode
        
        Returns:
            List of image paths: [cover_image, screenshot1, screenshot2, ...]
        Use fetch_game_images() to download and cache images.
        """
        # Default: 1 cover + 4 screenshots = 5 images total
        if max_images < 5:
            max_images = 5
        
        # Get existing cached images only - no fetching
        existing = self._get_existing_images(game_title)
        existing_cover = existing.get("cover", [])
        existing_screenshots = existing.get("screenshots", [])
        
        # Return what we have in cache
        result = existing_cover[:1] + existing_screenshots[:max_images - 1]
        return result[:max_images]
    
    def fetch_game_images(self, game_title: str, max_images: int = 5, console: Optional[str] = None, use_fallback: bool = True, force_refresh: bool = False) -> List[str]:
        """Fetch images for a game from APIs and cache them (for use in scripts, not runtime)
        
        Args:
            game_title: Title of the game
            max_images: Maximum number of images to return (default: 5, including 1 cover + 4 screenshots)
            console: Console/platform name (for fallback API)
            use_fallback: Whether to use TheGamesDB as fallback if RAWG fails
            force_refresh: If True, force download even if images exist (default: False)
        
        Returns:
            List of image paths: [cover_image, screenshot1, screenshot2, ...]
        """
        # Default: 1 cover + 4 screenshots = 5 images total
        if max_images < 5:
            max_images = 5
        
        # Get existing cached images
        existing = self._get_existing_images(game_title)
        existing_cover = existing.get("cover", [])
        existing_screenshots = existing.get("screenshots", [])
        
        # Check if we have enough images (1 cover + at least 4 screenshots)
        has_cover = len(existing_cover) > 0
        has_enough_screenshots = len(existing_screenshots) >= (max_images - 1)
        
        # If we have enough cached images and not forcing refresh, return them
        if not force_refresh and has_cover and has_enough_screenshots:
            # Return: 1 cover + (max_images - 1) screenshots
            result = existing_cover[:1] + existing_screenshots[:max_images - 1]
            return result[:max_images]
        
        # We need to fetch images
        print(f"Fetching images for {game_title} (cover: {not has_cover}, screenshots: {len(existing_screenshots)}/{max_images - 1})")
        
        # Try RAWG API first (only if API key is available)
        # If no API key, skip directly to TheGamesDB
        if not self.api_key:
            print("RAWG API key not set, using TheGamesDB fallback for images...")
            rawg_success = False
            fetched_images = []
        else:
            rawg_success = False
            fetched_images = []
            try:
                fetched_images = self._fetch_images_from_rawg(game_title, max_images, console)
                # Consider RAWG successful if we got at least some images
                if len(fetched_images) > 0:
                    rawg_success = True
            except Exception as e:
                print(f"Error fetching images from RAWG API: {e}")
                rawg_success = False
        
        # Categorize fetched images
        fetched_cover = []
        fetched_screenshots = []
        
        for img_path in fetched_images:
            filename = Path(img_path).name.lower()
            if any(keyword in filename for keyword in ['cover', 'boxart', 'background', 'poster', 'artwork']):
                fetched_cover.append(img_path)
            else:
                fetched_screenshots.append(img_path)
        
        # Combine existing and fetched images
        all_cover = existing_cover + fetched_cover
        all_screenshots = existing_screenshots + fetched_screenshots
        
        # Remove duplicates while preserving order
        seen = set()
        unique_cover = []
        for img in all_cover:
            if img not in seen:
                seen.add(img)
                unique_cover.append(img)
        
        unique_screenshots = []
        for img in all_screenshots:
            if img not in seen:
                seen.add(img)
                unique_screenshots.append(img)
        
        # Only try TheGamesDB if RAWG failed or didn't provide enough images
        if not rawg_success or (len(unique_cover) == 0 or len(unique_screenshots) < max_images - 1):
            if use_fallback:
                try:
                    from thegamesdb_service import TheGamesDBService
                    tgdb_service = TheGamesDBService()
                    tgdb_images = tgdb_service.get_game_images(
                        game_title, 
                        console, 
                        max(max_images - len(unique_screenshots), 1)
                    )
                    
                    if tgdb_images:
                        print(f"✓ Got {len(tgdb_images)} images from TheGamesDB fallback")
                    
                    # Categorize TheGamesDB images
                    for img_path in tgdb_images:
                        filename = Path(img_path).name.lower()
                        if img_path not in seen:
                            seen.add(img_path)
                            if any(keyword in filename for keyword in ['cover', 'boxart', 'background']):
                                if len(unique_cover) == 0:
                                    unique_cover.append(img_path)
                            else:
                                unique_screenshots.append(img_path)
                except Exception as e:
                    print(f"Error using TheGamesDB fallback: {e}")
        
        # Build result: 1 cover (if available) + screenshots
        result = []
        if unique_cover:
            result.append(unique_cover[0])
        result.extend(unique_screenshots[:max_images - len(result)])
        
        return result[:max_images]
    
    def _fetch_images_from_rawg(self, game_title: str, max_images: int = 5, console: Optional[str] = None) -> List[str]:
        """Fetch images from RAWG API for a game
        
        Args:
            game_title: Title of the game
            max_images: Maximum number of images to fetch
            console: Console/platform name for better matching
        
        Returns:
            List of downloaded image paths (cover first, then screenshots)
        """
        game_data = self._search_game_rawg(game_title, console)
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
        downloaded_cover = []
        downloaded_screenshots = []
        
        # Priority 1: Get background image (box art/cover) - this is usually the best quality
        background_image = details.get('background_image')
        if background_image:
            filename = f"cover_background_{hashlib.md5(background_image.encode()).hexdigest()[:8]}.jpg"
            save_path = game_dir / filename
            if not save_path.exists():
                if self._download_image(background_image, save_path):
                    downloaded_cover.append(str(save_path))
            else:
                downloaded_cover.append(str(save_path))
        
        # Priority 2: Get additional cover images
        additional_images = details.get('background_image_additional', None)
        if additional_images and len(downloaded_cover) == 0:
            filename = f"cover_additional_{hashlib.md5(additional_images.encode()).hexdigest()[:8]}.jpg"
            save_path = game_dir / filename
            if not save_path.exists():
                if self._download_image(additional_images, save_path):
                    downloaded_cover.append(str(save_path))
            else:
                downloaded_cover.append(str(save_path))
        
        # Priority 3: Get screenshots - try to get more than needed in case some fail
        screenshots = details.get('short_screenshots', [])
        if not screenshots:
            screenshots = details.get('screenshots', [])
        
        # Try to download more screenshots than needed to ensure we get at least max_images - 1
        # (we want 1 cover + (max_images - 1) screenshots)
        screenshots_needed = max_images - 1
        screenshots_to_try = min(len(screenshots), max(screenshots_needed * 2, 10))
        
        for screenshot in screenshots[:screenshots_to_try]:
            if len(downloaded_screenshots) >= screenshots_needed:
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
                downloaded_screenshots.append(str(save_path))
                continue
            
            # Try to download the image
            if self._download_image(image_url, save_path):
                downloaded_screenshots.append(str(save_path))
        
        # Combine: cover first, then screenshots
        result = downloaded_cover[:1] + downloaded_screenshots[:max_images - len(downloaded_cover)]
        return result[:max_images]
    
    def get_game_info(self, game_title: str, console: Optional[str] = None, max_images: int = 5) -> Dict:
        """Get complete game information from cache only (description + images)
        
        Args:
            game_title: Title of the game
            console: Console/platform name
            max_images: Maximum number of images (default: 5 = 1 cover + 4 screenshots)
        
        Returns:
            Dict with title, description, images, and image_count
        Use fetch_game_info() to download and cache game data.
        """
        # Default: 1 cover + 4 screenshots = 5 images total
        if max_images < 5:
            max_images = 5
        description = self.get_game_description(game_title, console)
        images = self.get_game_images(game_title, max_images, console=console, force_refresh=False)
        
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

