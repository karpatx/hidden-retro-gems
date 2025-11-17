# Alternatív API-k Retro Játékokhoz

A RAWG API mellett több alternatív forrás is létezik retro játékok képeinek és adatainak lekéréséhez.

## 1. TheGamesDB API ⭐ (Ajánlott)

**Előnyök:**
- Ingyenes és nyílt forráskódú
- Retro játékokra specializálódott
- Közösség által fenntartott adatbázis
- Képek (box art, screenshots, fanart)
- Nincs API kulcs szükséglet

**API Endpoint:**
```
https://api.thegamesdb.net/v1/Games/ByGameName
```

**Dokumentáció:**
- Web: https://thegamesdb.net/
- API Docs: https://forums.thegamesdb.net/viewforum.php?f=10

**Példa használat:**
```python
import requests

def search_thegamesdb(game_title, platform=None):
    url = "https://api.thegamesdb.net/v1/Games/ByGameName"
    params = {
        "apikey": "YOUR_API_KEY",  # Regisztráció szükséges
        "name": game_title
    }
    if platform:
        params["platform"] = platform
    
    response = requests.get(url, params=params)
    return response.json()
```

## 2. IGDB API (Internet Game Database)

**Előnyök:**
- Twitch által támogatott
- Nagyon átfogó adatbázis
- Modern és retro játékok egyaránt
- Ingyenes tier elérhető

**Előnyök:**
- Twitch Developer Account szükséges
- OAuth2 autentikáció
- Rate limiting

**API Endpoint:**
```
https://api.igdb.com/v4/games
```

**Dokumentáció:**
- Web: https://www.igdb.com/
- API Docs: https://api-docs.igdb.com/

**Példa használat:**
```python
import requests

def search_igdb(game_title, client_id, access_token):
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    data = f'search "{game_title}"; fields name,cover.url,screenshots.url; limit 10;'
    
    response = requests.post(url, headers=headers, data=data)
    return response.json()
```

## 3. MobyGames

**Előnyök:**
- Nagyon átfogó retro játék adatbázis
- Sok képernyőkép és borítókép
- Részletes játék információk

**Hátrányok:**
- Nincs hivatalos API
- Web scraping szükséges
- Rate limiting és ToS figyelembe vétele szükséges

**Web:**
- https://www.mobygames.com/

## 4. Giant Bomb API

**Előnyök:**
- Ingyenes API kulcs
- Jó dokumentáció
- Képek és videók

**Hátrányok:**
- Kevesebb retro játék
- Rate limiting (200 kérés/nap ingyenes tier)

**API Endpoint:**
```
https://www.giantbomb.com/api/games/
```

**Dokumentáció:**
- Web: https://www.giantbomb.com/
- API Docs: https://www.giantbomb.com/api/documentation

**Példa használat:**
```python
import requests

def search_giantbomb(game_title, api_key):
    url = "https://www.giantbomb.com/api/search/"
    params = {
        "api_key": api_key,
        "format": "json",
        "query": game_title,
        "resources": "game",
        "limit": 10
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

## Összehasonlítás

| API | Ingyenes | Retro Fókusz | Képek | API Kulcs | Nehézség |
|-----|----------|--------------|-------|-----------|----------|
| **TheGamesDB** | ✅ | ⭐⭐⭐⭐⭐ | ✅ | Regisztráció | Könnyű |
| **IGDB** | ✅ (Tier) | ⭐⭐⭐ | ✅ | Twitch Account | Közepes |
| **MobyGames** | ✅ | ⭐⭐⭐⭐⭐ | ✅ | Nincs API | Nehéz |
| **Giant Bomb** | ✅ | ⭐⭐ | ✅ | Ingyenes | Könnyű |
| **RAWG** | ✅ (Tier) | ⭐⭐⭐ | ✅ | Ingyenes | Könnyű |

## Leírások (Descriptions)

### TheGamesDB - Leírások

A TheGamesDB API támogatja a játék leírások lekérését is:

```python
from thegamesdb_service import TheGamesDBService

service = TheGamesDBService()
description = service.get_game_description("Super Mario Bros", "NES")
```

**Előnyök:**
- Retro játékokra specializálódott leírások
- Közösség által írt, részletes információ
- Ingyenes API

**API Endpoint:**
```
GET /Games/ByGameID?id={game_id}&fields=overview
```

### Integráció

A `game_data_service.py` automatikusan használja a TheGamesDB-t fallback-ként:
1. Először próbálja a **RAWG API**-t
2. Ha nincs elég információ → **TheGamesDB fallback**
3. Ha az sem ad eredményt → alapértelmezett leírás

## Ajánlás

**Retro játékokhoz:** **TheGamesDB** a legjobb választás, mert:
- Ingyenes
- Retro játékokra specializálódott
- Könnyű integrálni
- Közösség által fenntartott
- **Leírásokat is tartalmaz**

**Átfogó megoldáshoz:** **IGDB** vagy **RAWG** kombinációja a legjobb.

