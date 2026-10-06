# English Quest — Gamified English Learning Platform

Block 1: Backend architecture, authentication, game logic, content API and client interface.

## Repository layout

```
english-quest-project/
├── english-quest-backend/   # FastAPI + PostgreSQL backend
├── frontend/                # Next.js (App Router) client
├── docker-compose.yml       # PostgreSQL 16 in an isolated container
└── README.md
```

## Database

By default the project uses **your local PostgreSQL** (see `english-quest-backend/.env`,
`DATABASE_URL`). Create the database once:

```bash
createdb english_quest     # or: psql -d postgres -c "CREATE DATABASE english_quest;"
```

Tables and seed data are created automatically on backend startup.

### Browse the database with Adminer (web UI)

```bash
docker compose --profile tools up -d
# open http://localhost:8080
```

Login fields: **System** = `PostgreSQL`, **Server** = `host.docker.internal`,
**Username** = your macOS username (e.g. `niaz`), **Password** = *(empty)*,
**Database** = `english_quest`.

### Optional: use a containerized PostgreSQL instead

If you don't have a local Postgres, run the bundled one and point `DATABASE_URL`
to `postgresql+asyncpg://quest:quest@localhost:5435/english_quest`:

```bash
docker compose --profile docker up -d
```

## Quick start

```bash
# 1. Database: local Postgres (create the DB once) — see above
createdb english_quest

# 2. Backend (http://localhost:8000)
cd english-quest-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL to your local Postgres
uvicorn src.server:app --host 0.0.0.0 --port 8000

# 3. Frontend (http://localhost:3000)
cd ../frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Features

- JWT authentication, bcrypt hashing (salt rounds 12)
- RBAC: `student` / `teacher`
- CEFR placement test with auto-completion of lower levels and starting XP
- Levels → 5 missions each → tasks/questions; free navigation with `locked` levels
- Three separate lesson modules that unlock in order: test (5 questions) → pronunciation → 3D dictionary game
- Dictionary game in Plants-vs-Zombies style (Three.js): picture cards fly in — say the English word
- Win/lose result videos (Booba on success, laughing cat on failure)
- Word pictures + IPA transcription + translation in the pronunciation module
- Server-side XP calculation: first pass vs. repeat
- Teacher admin panel: full CRUD for missions, tasks, questions and options, plus a vocabulary editor
- Word pronunciation via browser text-to-speech (no audio files needed)
- Minimal, responsive UI with light/dark theme (black in dark mode, white in light mode)
- Friendly game-like design: daisyUI themes, Framer Motion animations, confetti on success, animated XP

## Demo credentials

- Teacher: `teacher@englishquest.dev` / `Teacher123`
- Student: register through the UI
