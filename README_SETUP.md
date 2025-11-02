# Gyors telepítési útmutató

## Backend telepítés és futtatás

### 1. UV telepítés (ha még nincs)

**Windows (PowerShell - Adminisztrátorként):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Backend indítás

```bash
cd backend
uv sync
uv run python main.py
```

A backend elérhető lesz: http://localhost:8000
- API: http://localhost:8000/docs (Swagger dokumentáció)
- Health check: http://localhost:8000/

## Frontend telepítés és futtatás

```bash
cd frontend
npm install
npm run dev
```

A frontend elérhető lesz: http://localhost:3000

## Tesztelés

### Backend teszt:
```bash
# Új terminálban
curl http://localhost:8000/

# Játékok listázása
curl http://localhost:8000/games | ConvertFrom-Json | Select-Object -First 1
```

### Frontend teszt:
Nyisd meg a böngészőt: http://localhost:3000

## Projekt struktúra

```
hidden-gem/
├── backend/
│   ├── main.py           # FastAPI alkalmazás
│   └── pyproject.toml    # UV dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx       # Fő komponens
│   │   ├── main.tsx      # Entry point
│   │   └── components/   # React komponensek
│   ├── package.json      # NPM dependencies
│   └── vite.config.ts    # Vite config
├── games.txt             # Játék adatbázis
└── README.md             # Dokumentáció
```

## API Endpoints

- `GET /` - Főoldal
- `GET /games` - Összes játék (2232 db)
- `GET /games/platforms` - Platformok listája
- `GET /games/consoles` - Konzolok listája
- `GET /games/search?q=mario` - Keresés
- `GET /games/by-platform/{platform}` - Platform szerint
- `GET /games/by-console/{console}` - Konzol szerint

## Teljesített funkciók

✅ FastAPI backend UV-vel
✅ React frontend Mantine UI-val
✅ Tab-delimited games.txt parser
✅ 2232 játék feldolgozása
✅ Keresés és szűrés
✅ Reszponzív dizájn
✅ Platform/konzol alapú szűrés

