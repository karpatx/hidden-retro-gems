# Kép Cache Rendszer

Ez a dokumentum leírja, hogyan működik a játék képek cache-elése és automatikus letöltése.

## Áttekintés

A rendszer **intelligens cache-elést** használ:
- ✅ **Először ellenőrzi a cache-t** - nem tölt le feleslegesen
- ✅ **Csak akkor tölt le**, ha nincs elég kép
- ✅ **Automatikusan kategorizálja** a képeket (borítókép vs screenshot)
- ✅ **Prioritizálja a borítóképet** - mindig legyen legalább 1 borítókép
- ✅ **Fallback támogatás** - ha RAWG nem ad elég képet, próbálja a TheGamesDB-t

## Kép Struktúra

Minden játékhoz **5 kép** tartozik (alapértelmezett):
- **1 borítókép** (cover/boxart) - első kép
- **4 screenshot** - a játékból készült képek

### Kép Elnevezés

A képek fájlneve alapján kategorizálódnak:

**Borítókép fájlnevek:**
- `cover_*.jpg`
- `boxart_*.jpg`
- `background_*.jpg`
- `poster_*.jpg`
- `artwork_*.jpg`

**Screenshot fájlnevek:**
- `screenshot_*.jpg`
- Minden más kép

## Cache Működés

### 1. Kép Lekérés (`get_game_images`)

```python
images = game_data_service.get_game_images(
    game_title="Super Mario Bros",
    max_images=5,  # 1 cover + 4 screenshots
    console="NES",
    force_refresh=False  # Ne töltse le újra, ha már van cache
)
```

**Működés:**
1. Ellenőrzi a cache-t (`_get_existing_images`)
2. Ha van **1 borítókép** és **4 screenshot** → visszaadja őket
3. Ha nincs elég kép → letölti a hiányzókat
4. Visszaadja: `[cover_image, screenshot1, screenshot2, screenshot3, screenshot4]`

### 2. Cache Ellenőrzés

A rendszer automatikusan ellenőrzi:
- Van-e borítókép?
- Van-e elég screenshot (legalább 4)?
- Ha mindkettő megvan → **nem tölt le újra**

### 3. Automatikus Letöltés

Ha nincs elég kép, a rendszer:
1. **RAWG API**-t próbálja először
2. Ha nincs elég kép → **TheGamesDB fallback** (ha engedélyezve)
3. Kategorizálja a letöltött képeket
4. Eltárolja a cache-ben

## API Végpontok

### Játék Részletek (5 kép)

```http
GET /games/{title}/details?console=NES&max_images=5
```

**Válasz:**
```json
{
  "title": "Super Mario Bros",
  "description": "...",
  "images": [
    "/static/images/games/Super_Mario_Bros/cover_background_abc123.jpg",
    "/static/images/games/Super_Mario_Bros/screenshot_def456.jpg",
    "/static/images/games/Super_Mario_Bros/screenshot_ghi789.jpg",
    "/static/images/games/Super_Mario_Bros/screenshot_jkl012.jpg",
    "/static/images/games/Super_Mario_Bros/screenshot_mno345.jpg"
  ],
  "image_count": 5
}
```

### Thumbnail (első kép = borítókép)

```http
GET /games/{title}/thumbnail?console=NES
```

**Válasz:**
```json
{
  "thumbnail": "/static/images/games/Super_Mario_Bros/cover_background_abc123.jpg"
}
```

## Fájlstruktúra

```
backend/
└── static/
    └── images/
        └── games/
            ├── Super_Mario_Bros/
            │   ├── cover_background_abc123.jpg  ← Borítókép
            │   ├── screenshot_def456.jpg        ← Screenshot 1
            │   ├── screenshot_ghi789.jpg        ← Screenshot 2
            │   ├── screenshot_jkl012.jpg        ← Screenshot 3
            │   └── screenshot_mno345.jpg        ← Screenshot 4
            └── Another_Game/
                └── ...
```

## Használat

### Alapértelmezett (5 kép, cache használata)

```python
# Automatikusan ellenőrzi a cache-t
# Csak akkor tölt le, ha nincs elég kép
images = game_data_service.get_game_images("Super Mario Bros", console="NES")
```

### Kényszerített Frissítés

```python
# Mindig letölti újra (pl. ha rossz képek lettek)
images = game_data_service.get_game_images(
    "Super Mario Bros",
    console="NES",
    force_refresh=True
)
```

### Egyedi Képszám

```python
# 1 borítókép + 6 screenshot = 7 kép összesen
images = game_data_service.get_game_images(
    "Super Mario Bros",
    max_images=7,
    console="NES"
)
```

## Előnyök

✅ **Gyors** - Ha van cache, azonnal visszaadja  
✅ **Hatékony** - Nem tölt le feleslegesen  
✅ **Megbízható** - Fallback API-k támogatása  
✅ **Strukturált** - Borítókép + screenshots kategorizálás  
✅ **Rugalmas** - Konfigurálható képszám  

## Megjegyzések

- A cache **perzisztens** - a képek fájlrendszerben tárolódnak
- A képek **nem törlődnek** automatikusan
- Ha törölni szeretnél képeket, manuálisan töröld a mappákat
- A rendszer **automatikusan kezeli** a duplikációkat

