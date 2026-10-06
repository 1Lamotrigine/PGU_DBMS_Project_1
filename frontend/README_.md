# English Quest — Frontend

Next.js (App Router) + TypeScript + Tailwind client for the English Quest platform.

## Pages

| Route | Description |
|---|---|
| `/` | Public landing |
| `/login`, `/register` | Authentication |
| `/calibration` | Placement test |
| `/dashboard` | Profile, XP, levels & missions |
| `/missions/[id]` | Mission overview (three modules) |
| `/test/[id]` | Test module — 5 multiple-choice questions |
| `/pronounce/[id]` | Pronunciation module (picture + word + transcription + translation) |
| `/game/[id]` | Dictionary game — picture cards fly in, say the English word |
| `/admin/missions` | Teacher admin panel (role `teacher` only) |

Route protection is enforced by `src/middleware.ts` (JWT presence + `teacher` role for `/admin`).
The API client (`src/services/api.ts`) automatically attaches `Authorization: Bearer <token>`.

## Design & theming

The interface has a friendly, game-like look built on **daisyUI** (Tailwind plugin) with two custom
themes:

- `eqlight` — white background
- `eqdark` — pure black background

A blue-cyan primary and a violet secondary drive gradients (XP bars, badges, avatars). The theme
toggle is in the header and the choice is persisted in `localStorage` (`eq_theme`), defaulting to the
OS preference. daisyUI sets `data-theme` on `<html>`.

**Motion & delight:** `framer-motion` for entrance/transition animations, `canvas-confetti` for
celebrations on passing a test, pronunciation, game or calibration, `react-countup` for animated XP
numbers, and `lucide-react` icons.

## Lesson structure

Each mission is a three-part lesson, with a **separate page per module** (70% pass threshold).
Modules unlock **in order — each one unlocks the next**:

1. **Test** (`/test/[id]`) — 5 meaningful multiple-choice questions. Unlocked first.
2. **Pronunciation** (`/pronounce/[id]`) — say each English word out loud. Unlocks after passing the test.
3. **Dictionary game** (`/game/[id]`) — a **Plants-vs-Zombies–style** voice game rendered with
   **Three.js** (flat 2D scene). **Picture cards** fly right → left toward your base; the
   **microphone stays on for the whole game**, so you simply **say the English word** for each
   picture to make it vanish. A word reaching the left edge costs **1 of 5 lives** (health bar).
   Clear 12 pictures to pass (70% threshold).

Each module ends on a **result screen**: success plays `win.mp4` (Booba), failure plays `lose.mp4`
(the laughing cat) — both with their own audio. Media lives in `frontend/public/media/`.

Word pictures live in `frontend/public/images/` (SVG icons); the pronunciation module shows the
picture, the English word, its IPA transcription and the Russian translation.

The `/missions/[id]` page shows the three modules with their state: a lock, the module number, or a
checkmark once passed. Each module screen ends with a button that goes straight to the **next module**
(Test → Pronunciation → Dictionary game). The backend enforces the order — pronunciation is rejected
before the test, and the game is rejected before pronunciation.

Both spoken parts use the **Web Speech API** (`SpeechRecognition`) — no backend or API key.
Where it is unavailable (e.g. Firefox), a text input fallback is always offered, and scoring
still happens on the backend.

## XP rules

- First successful pass of a level (mission) → `xp_reward_first`.
- Repeat pass → `xp_reward_repeat`.
- Below 70% → no XP.
- After calibration, all lower levels/missions are auto-completed and their `xp_reward_first`
  is added to the starting XP.


## Run

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev                        # http://localhost:3000
```

Make sure the backend is running (see `english-quest-backend/README.md`).

## Demo credentials

- Student: register via `/register`
- Teacher: `teacher@englishquest.dev` / `Teacher123`
