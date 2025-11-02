# Hidden Gem - Játékgyűjtemény Weboldal

Egy modern weboldal, amely segít felfedezni a kevésbé ismert, de remek játékokat különböző konzolokon és platformokon.

## Technológiai stack

### Backend
- **Python FastAPI** - REST API
- **UV** - Python package manager
- **Uvicorn** - ASGI szerver

### Frontend
- **React** - UI keretrendszer
- **TypeScript** - Type safety
- **Mantine** - UI komponenskönyvtár
- **Vite** - Build eszköz
- **React Router** - Routing

## Telepítés és futtatás

### Backend

1. Telepítsd a UV-t, ha még nincs meg:
```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Navigálj a backend könyvtárba és telepítsd a függőségeket:
```bash
cd backend
uv sync

# Vagy ha problémáid vannak:
Remove-Item uv.lock -ErrorAction SilentlyContinue
uv sync
```

3. Indítsd el a FastAPI szervert:
```bash
# Opció 1: Közvetlenül Python-nal
uv run python main.py

# Opció 2: Uvicorn-nel direktben
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opció 3: Windows batch fájl
start.bat

# Opció 4: Linux/Mac shell script
./start.sh
```

A backend elérhető lesz a `http://localhost:8000` címen.

### Frontend

1. Navigálj a frontend könyvtárba:
```bash
cd frontend
```

2. Telepítsd a függőségeket:
```bash
npm install
```

3. Indítsd el a fejlesztői szervert:
```bash
npm run dev
```

A frontend elérhető lesz a `http://localhost:3000` címen.

## Funkciók

### Játékok
- 🔍 Keresés játékcím alapján
- 📊 Szűrés gyártó és konzol szerint
- 📋 Táblázatos megjelenítés
- 📱 Reszponzív dizájn

### Gyártók
- 🎴 Kártyás megjelenítés
- 📈 Játékszámok és platform stats
- 🔗 Részletes gyártó oldal
- 🎨 Színes tematikus kártyák

### Játék részletek
- 🖼️ Többkép megjelenítés
- 📝 Automatikus leírás generálás
- 🏷️ Műfaj címkék
- 🔍 Navigációs breadcrumb

### Általános
- 🎨 Modern, letisztult UI
- 📱 Reszponzív dizájn
- ⚡ Gyors API válaszidők

## API Endpoints

### Főoldal
- `GET /` - Főoldal információ

### Játékok
- `GET /games` - Összes játék lekérése (2232 db)
- `GET /games/search?q={query}` - Játékkeresés
- `GET /games/by-manufacturer/{manufacturer}` - Játékok gyártó szerint
- `GET /games/by-console/{console}` - Játékok konzol szerint
- `GET /games/consoles` - Konzolok listája

### Gyártók
- `GET /manufacturers` - Összes gyártó platformokkal és játékszámokkal
- `GET /manufacturer/{name}` - Egy gyártó részletes adatai (pl: Nintendo, Sony, Sega)
- `GET /manufacturer/{name}/{platform}` - Konkrét gyártó platformján lévő játékok ABC sorrendben

## Fejlesztés

### Backend teszt
```bash
cd backend
uv run python -m pytest
```

### Frontend build
```bash
cd frontend
npm run build
```

## Licenc

MIT

