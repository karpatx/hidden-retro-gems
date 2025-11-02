# RAWG API Beállítás

A rendszer most a RAWG Video Games Database API-t használja a játék adatok és képek beszerzésére. Ez megbízhatóbb és jobb minőségű adatokat nyújt, mint a Wikipedia.

## API Kulcs Beszerzése

1. Menj a [RAWG.io](https://rawg.io/) weboldalra
2. Regisztrálj egy ingyenes fiókot
3. Menj az [API dokumentáció oldalra](https://rawg.io/apidocs)
4. Generálj egy API kulcsot

## API Kulcs Beállítása

### Windows (PowerShell)
```powershell
$env:RAWG_API_KEY="your_api_key_here"
```

### Windows (Command Prompt)
```cmd
set RAWG_API_KEY=your_api_key_here
```

### Linux/Mac
```bash
export RAWG_API_KEY="your_api_key_here"
```

### Permanens beállítás Windows-on

1. Nyisd meg a "Környezeti változók" beállítást
2. Adj hozzá egy új felhasználói változót:
   - Név: `RAWG_API_KEY`
   - Érték: `your_api_key_here`

### Permanens beállítás Linux/Mac-on

Add hozzá a `.bashrc` vagy `.zshrc` fájlhoz:
```bash
export RAWG_API_KEY="your_api_key_here"
```

## Alternatív: API Kulcs Fájlban

Ha nem szeretnéd környezeti változóként beállítani, módosíthatod a `backend/main.py` fájlt:

```python
rawg_api_key = "your_api_key_here"  # Közvetlenül itt
```

**FIGYELEM:** Ne commitold az API kulcsot a Git repository-ba! Add hozzá a `.gitignore`-hoz.

## API Korlátok

- **Ingyenes tier:** 500 kérés/nap
- **Rate limit:** ~5 kérés/másodperc (a rendszer automatikusan kezeli)
- További információ: [RAWG API dokumentáció](https://rawg.io/apidocs)

## Használat

Miután beállítottad az API kulcsot, a rendszer automatikusan használni fogja a RAWG API-t:

1. **Játék leírások:** Automatikusan letöltődnek a RAWG API-ból
2. **Játék képek:** Box art és screenshot képek letöltődnek
3. **Cache:** Minden adat cache-elődik, így nem kell minden alkalommal API hívást tenni

## Hibaelhárítás

**"Rate limit exceeded" hiba:**
- A rendszer automatikusan várakozik és újra próbálkozik
- Ha túl gyakran előfordul, növeld a `min_request_interval` értékét a `game_data_service.py`-ben

**API kulcs hiánya:**
- Ellenőrizd, hogy beállítottad-e a `RAWG_API_KEY` környezeti változót
- Újraindítsd a backend szervert a változások életbe lépéséhez

**Képek nem töltődnek le:**
- Ellenőrizd az internetkapcsolatot
- Nézd meg a backend console üzeneteit hibákért
- Bizonyos játékokhoz lehet, hogy nincs elérhető kép a RAWG adatbázisában

