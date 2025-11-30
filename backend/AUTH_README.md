# Autentikációs rendszer dokumentáció

## Áttekintés

A backend mostantól felhasználókezelést és autentikációt tartalmaz JWT token alapú rendszerrel.

## Adatbázis

- **Típus:** SQLite
- **Fájl:** `backend/database.db`
- **Concurrent access:** WAL (Write-Ahead Logging) módban működik, így több futó példány is tudja használni egyszerre
- **Modell:** SQLAlchemy ORM

## Felhasználó modell

- `id`: Egyedi azonosító
- `email`: Email cím (egyedi, indexelt)
- `hashed_password`: Bcrypt-tel hashelt jelszó
- `is_admin`: Admin jogosultság (boolean)
- `is_active`: Aktív felhasználó (boolean)
- `created_at`: Létrehozás dátuma
- `updated_at`: Frissítés dátuma

## Admin felhasználó

Az admin felhasználó automatikusan létrejön az első indításkor:
- **Email:** ikarpati@gmail.com
- **Jelszó:** 123456789
- **Jogosultság:** Admin

## API Endpointok

### POST `/auth/login`
Bejelentkezés

**Request body (form-data):**
```
username: ikarpati@gmail.com
password: 123456789
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### GET `/auth/me`
Jelenlegi felhasználó információi (autentikáció szükséges)

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "email": "ikarpati@gmail.com",
  "is_admin": true,
  "is_active": true
}
```

### POST `/auth/register`
Új felhasználó regisztrálása

**Request body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "email": "user@example.com",
  "is_admin": false,
  "is_active": true
}
```

## Token használat

A token 30 napig érvényes. A védett endpointokhoz a következő header-t kell küldeni:

```
Authorization: Bearer <access_token>
```

## Függőségek

- `sqlalchemy>=2.0.0` - ORM
- `passlib[bcrypt]>=1.7.4` - Jelszó hashelés
- `python-jose[cryptography]>=3.3.0` - JWT tokenek

## Telepítés

A függőségek automatikusan települnek:
```bash
cd backend
uv sync
```

## Adatbázis inicializálás

Az adatbázis automatikusan inicializálódik az első indításkor. Ha manuálisan szeretnéd inicializálni:

```python
from database import init_db
init_db()
```

## Biztonsági megjegyzések

⚠️ **Fontos:** A production környezetben:
1. Változtasd meg a `SECRET_KEY`-t az `auth.py` fájlban (vagy használj environment változót)
2. Használj erős jelszavakat
3. Fontold meg a HTTPS használatát
4. Állíts be megfelelő CORS beállításokat

