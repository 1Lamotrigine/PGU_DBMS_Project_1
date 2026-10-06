# English Quest — Backend (Block 1)

Gamified English learning platform backend built with **FastAPI**, **SQLAlchemy (async)**, **PostgreSQL** and **JWT**.

Strict layered architecture: `routes → controllers → services → models`, with validators (Pydantic) and middleware (JWT / RBAC / errors).

## Tech stack

- Python 3.11+ / FastAPI / Uvicorn
- SQLAlchemy 2 (async) + asyncpg
- Pydantic v2 + pydantic-settings
- PyJWT + passlib (bcrypt, salt rounds = 12)
- PostgreSQL 16 (Docker)

## Structure

```
src/
├── config/        # database.py, settings.py
├── controllers/   # auth, user, mission, game
├── middleware/    # auth (JWT), role (RBAC), error handlers
├── routes/        # auth, user, mission, game routers
├── services/      # account, calibration, mission, game, user, security
├── validators/    # Pydantic request schemas
├── models/        # SQLAlchemy ORM
└── db/seed.py     # startup seed data
```

> Some modules keep the dotted filenames from the ТЗ (e.g. `auth.controller.py`) as thin
> re-export shims; the real implementation lives in the matching `*_*.py` module.

## Run

```bash
# 1. Start PostgreSQL (from the repository root)
docker compose up -d

# 2. Backend
cd english-quest-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # adjust if needed
uvicorn src.server:app --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs · Health: http://localhost:8000/health

Tables are created automatically and seed data is inserted on startup:

- roles `student`, `teacher`
- CEFR levels `A1`–`C2`
- 3 calibration questions per level (A1–B2)
- teacher account `teacher@englishquest.dev` / `Teacher123`
- 5 demo missions for level A1 (with tasks, questions, options)

## Business rules

- **Calibration** (`POST /calibration/submit`): server compares answers, derives CEFR level,
  auto-completes all lower levels and awards starting XP.
- **XP**: first successful pass of a mission → sum of `xp_reward_first`; repeat → sum of
  `xp_reward_repeat`; below **70%** → no XP.
- **Free navigation**: missions of levels above the user's CEFR are marked `locked`.
- **RBAC**: mission create/update/delete require the `teacher` role (otherwise 403).

## API

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Register (role `student`) |
| POST | `/api/v1/auth/login` | — | Login → JWT |
| GET | `/api/v1/auth/me` | auth | Current profile |
| POST | `/api/v1/calibration/submit` | student | Submit placement test |
| GET | `/api/v1/calibration/questions` | auth | Placement questions |
| GET | `/api/v1/levels` | auth | Levels + missions (`locked`) |
| GET | `/api/v1/missions/{id}` | auth | Mission detail + questions |
| POST | `/api/v1/missions/{id}/submit-tests` | student | Test block result |
| POST | `/api/v1/missions/{id}/submit-pronunciation` | student | Pronunciation result |
| POST | `/api/v1/missions/{id}/submit-game` | student | Arcade result + XP |
| POST/PUT/DELETE | `/api/v1/missions[/{id}]` | teacher | Mission CRUD |
| GET | `/api/v1/users/me/progress` | auth | User progress |
| GET | `/api/v1/students/{id}/progress-preview` | auth | Student preview |

Errors use a unified shape: `{ "error": { "code", "message", "details" } }`
with codes `400 / 401 / 403 / 404 / 422`.
