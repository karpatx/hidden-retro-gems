# Játék Adatok Kezelése

Ez a dokumentum leírja, hogyan működik a játék adatok (leírások és képek) kezelése és hogyan lehet kézi erővel módosítani őket.

## Fájlstruktúra

A rendszer a következő struktúrában tárolja az adatokat:

```
backend/
├── game_data/
│   └── descriptions.json          # Játék leírások (könnyen szerkeszthető JSON)
├── static/
│   └── images/
│       └── games/
│           ├── Game_Title_1/      # Minden játék saját mappája
│           │   ├── image1.jpg
│           │   ├── image2.png
│           │   └── ...
│           └── Game_Title_2/
│               └── ...
```

## Játék Leírások Szerkesztése

A leírások a `backend/game_data/descriptions.json` fájlban találhatók. Ez egy egyszerű JSON fájl, amelyet bármilyen szövegszerkesztővel megnyithatsz:

```json
{
  "Game Title 1": "Ez a játék leírása...",
  "Game Title 2": "Egy másik játék leírása...",
  ...
}
```

### Leírás hozzáadása/módosítása

1. Nyisd meg a `backend/game_data/descriptions.json` fájlt
2. Adj hozzá egy új kulcsot a játék pontos nevével (ahogy szerepel a `games.txt`-ben)
3. Add meg a leírást értékként
4. Mentsd el a fájlt

**Példa:**
```json
{
  "The Messenger": "The Messenger egy platform játék, amely egyedi mechanikákkal rendelkezik...",
  "999": "Nine Hours, Nine Persons, Nine Doors egy vizuális regény..."
}
```

**Fontos:** A játék nevének pontosan egyeznie kell a `games.txt` fájlban szereplő névvel (kis- és nagybetű érzékeny).

## Képek Kezelése

A képek a `backend/static/images/games/[Játék_Név]/` mappákban találhatók.

### Kép hozzáadása

1. Keressd meg a játék mappáját (pl. `backend/static/images/games/The_Messenger/`)
2. Ha nem létezik, hozd létre a mappát a játék nevével (szóközöket aláhúzásjelre cserélve)
3. Másold be a képeket (jpg, jpeg, png, gif, webp formátumok támogatottak)
4. A rendszer automatikusan használja ezeket a képeket

### Kép cseréje/törlése

1. Nyisd meg a megfelelő játék mappát
2. Töröld vagy cseréld le a képeket
3. Az új képek azonnal elérhetők lesznek

### Kép formátum és elnevezés

- **Támogatott formátumok:** .jpg, .jpeg, .png, .gif, .webp
- **Elnevezés:** A fájlnevek tetszőlegesek lehetnek, a rendszer az összes képet betölti
- **Maximum:** A rendszer maximum 4 képet jelenít meg játékonként (a főképet + 3 galériát)
  - A főkép az első kép lesz (abc sorrendben)
  - A többi kép a galériában jelenik meg

## Automatikus Letöltés

Ha egy játékhoz nincs még leírás vagy kép, a rendszer automatikusan megpróbálja lekérni őket a RAWG API-ból:

1. **Leírás:** A RAWG API-ból letölti a játék leírását (első 3 mondat)
2. **Képek:** Box art és screenshot képeket letölt a RAWG API-ból

**Megjegyzés:** Az automatikus letöltéshez be kell állítani a RAWG API kulcsot. További információ: `RAWG_API_SETUP.md`

### Automatikus letöltés kikapcsolása

Az automatikus letöltés akkor történik meg, amikor:
- Egy játékhoz még nincs leírás a `descriptions.json`-ben
- Egy játék mappájában kevesebb mint 3-4 kép van

Ha manuálisan hozzáadsz leírást vagy képeket, azok elsőbbséget élveznek.

## Tippek

1. **Javasolt:** Mentsd el a `descriptions.json`-t és a `static/images/games/` mappát verziókezelésbe (Git), hogy mások is használhassák
2. **Backup:** Készíts rendszeres mentést az adatokról
3. **Minőség:** Ha lehetséges, használj nagy felbontású, jó minőségű képeket
4. **Leírások:** A leírások lehetnek rövidek vagy hosszabbak, de érdemes releváns információkat tartalmazniuk

## Hibaelhárítás

**Probléma:** A képek nem jelennek meg
- Ellenőrizd, hogy a kép fájl elérési útja helyes-e
- Nézd meg, hogy a fájl kiterjesztése támogatott-e
- Ellenőrizd a backend console üzeneteit hibákért

**Probléma:** A leírás nem frissül
- Ellenőrizd, hogy a játék neve pontosan egyezik a `games.txt`-ben szereplő névvel
- Ellenőrizd, hogy a JSON szintaxis helyes-e (használj JSON validator-t)

**Probléma:** Az automatikus letöltés nem működik
- Ellenőrizd, hogy beállítottad-e a `RAWG_API_KEY` környezeti változót
- Nézd meg a `RAWG_API_SETUP.md` fájlt a részletes beállítási útmutatóért
- Ellenőrizd az internetkapcsolatot
- Nézd meg a backend console üzeneteit
- A RAWG API ingyenes tier-je napi 500 kérésre korlátozott

