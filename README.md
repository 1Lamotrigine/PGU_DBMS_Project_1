

# Teacher User
Login - teacher@englishquest.dev
Password - Teacher123



---

# English Quest — Геймифицированная платформа для изучения английского языка

Блок 1: Архитектура бэкенда, аутентификация, игровая логика, API контента и клиентский интерфейс.

## Структура репозитория

```
english-quest-project/
├── english-quest-backend/   # Бэкенд на FastAPI + PostgreSQL
├── frontend/                # Клиент на Next.js (App Router)
├── docker-compose.yml       # PostgreSQL 16 в изолированном контейнере
└── README.md

```

## Запуск всего стека в Docker (одна команда)

Собирает и поднимает базу данных, бэкенд и фронтенд одновременно:

```bash
docker compose up --build
```

| Сервис   | Адрес                                      | Описание                         |
|----------|--------------------------------------------|----------------------------------|
| db       | `localhost:5435`                           | PostgreSQL 16                    |
| backend  | http://localhost:8000                      | FastAPI (документация: `/docs`)  |
| frontend | http://localhost:3000                      | Next.js                          |

Таблицы и seed-данные создаются автоматически при старте бэкенда. Остановить стек:

```bash
docker compose down          # сохранить данные БД
docker compose down -v       # удалить данные БД (volume)
```

Дополнительно Adminer (веб-UI для БД) — профиль `tools`:

```bash
docker compose --profile tools up -d
# http://localhost:8080
```

## База данных

Без Docker проект использует **локальный PostgreSQL** (см. `english-quest-backend/.env`, переменная `DATABASE_URL`). Создайте базу данных один раз:

```bash
createdb english_quest     # или: psql -d postgres -c "CREATE DATABASE english_quest;"

```

Таблицы и первоначальные данные (seed) создаются автоматически при старте бэкенда.

### Просмотр БД через веб-интерфейс Adminer

```bash
docker compose --profile tools up -d
# откройте http://localhost:8080

```

Поля для входа: **Движок (System)** = `PostgreSQL`, **Сервер (Server)** = `host.docker.internal`, **Пользователь (Username)** = ваше имя пользователя macOS (например, `niaz`), **Пароль (Password)** = *(оставьте пустым)*, **База данных (Database)** = `english_quest`.

### Альтернатива: запуск PostgreSQL в Docker

Если у вас нет локального PostgreSQL, запустите контейнеризованный вариант и укажите в `DATABASE_URL` значение `postgresql+asyncpg://quest:quest@localhost:5435/english_quest`:

```bash
docker compose --profile docker up -d

```

## Быстрый запуск

```bash
# 1. База данных: локальный Postgres (создайте БД один раз) — см. выше
createdb english_quest

# 2. Бэкенд (http://localhost:8000)
cd english-quest-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # укажите DATABASE_URL для локального Postgres
uvicorn src.server:app --host 0.0.0.0 --port 8000


source .venv/bin/activate && uvicorn src.server:app --host 0.0.0.0 --port 8000

# 3. Фронтенд (http://localhost:3000)
cd ../frontend
npm install
cp .env.local.example .env.local
npm run dev

```

## Прогрессия, XP и Scoreboard

* Внутри уровня миссии открываются **последовательно**: сначала только первая, каждая следующая — после завершения предыдущей.
* Следующий уровень открывается, если набрано **≥ 70 % XP уровня** или пройдены **все 5 миссий** уровня.
* Открытый уровень хранится в `users.unlocked_level_rank` (индекс CEFR) и **не меняет** `cefr_level` — тот по-прежнему задаётся только калибровкой.
* Scoreboard: `GET /api/v1/users/leaderboard?limit=10` — топ студентов по `total_xp` (email не раскрывается). Отображается на `/dashboard` справа для всех авторизованных.

Для баз, созданных до этого изменения, выполните миграцию:

```bash
psql -d english_quest -f english-quest-backend/migrations/001_progression.sql
```

## Тесты и CI
```bash
cd english-quest-backend
pip install -r requirements-dev.txt
pytest -q          # интеграционные API-тесты (изолированная SQLite)
```

```bash
cd frontend
npm ci
npm run lint       # неинтерактивный ESLint
npm run build
```

Пайплайн `.github/workflows/ci.yml` прогоняет compile + pytest (backend) и lint + build (frontend).

## Возможности и функционал

* JWT-аутентификация, хеширование bcrypt (количество раундов = 12)
* Вход и регистрация через **Google** (OAuth 2.0 / Google Identity Services) с проверкой ID-токена на сервере и привязкой к существующему аккаунту по email
* Ролевая модель (RBAC): `student` (ученик) / `teacher` (преподаватель)
* Вступительный тест CEFR с автоматическим зачетом нижестоящих уровней и начислением стартовых очков опыта (XP)
* Уровни → по 5 миссий в каждом → задания/вопросы; свободная навигация с заблокированными (`locked`) уровнями
* Четыре отдельных учебных модуля, открывающихся последовательно: тест (5 вопросов) → произношение → 3D-игра "Словарь" → грамматическая игра
* Игра "Словарь" в стиле Plants vs. Zombies (Three.js): прилетают карточки с картинками — произнесите слово на английском
* Грамматическая игра: по предложению с пропуском одновременно вылетают 4 формы одного слова — нужно нажать правильную (микрофон не нужен)
* Видеоролики с результатами победы/поражения (Буба при успехе, смеющийся кот при неудаче)
* Картинки слов + транскрипция IPA + перевод в модуле произношения
* Расчет XP на стороне сервера: за первое прохождение vs. за повторное
* Панель преподавателя: полный CRUD для миссий, заданий, вопросов и вариантов ответов, а также редактор словаря
* Озвучка слов через браузерный Text-to-Speech (отдельные аудиофайлы не требуются)
* Минималистичный адаптивный UI с поддержкой светлой/темной темы (черная в темной теме, белая в светлой)
* Дружелюбный игровой дизайн: темы daisyUI, анимации Framer Motion, конфетти при успехе, анимированный XP

## Вход через Google

1. В [Google Cloud Console](https://console.cloud.google.com/apis/credentials) создайте **OAuth 2.0 Client ID** типа *Web application*.
2. Добавьте `http://localhost:3000` в **Authorized JavaScript origins** (для продакшена — реальный домен).
3. Пропишите ID в обоих окружениях:
   ```bash
   # english-quest-backend/.env
   GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
   # frontend/.env.local
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
   ```
4. Перезапустите бэкенд и фронтенд. На `/login` и `/register` появится кнопка «Continue with Google».

Секрет клиента не нужен: браузер получает от Google подписанный ID-токен, а бэкенд проверяет его подпись по публичным ключам Google. Если `GOOGLE_CLIENT_ID` не задан, кнопка скрыта, а `POST /api/v1/auth/google` отвечает `503 GOOGLE_NOT_CONFIGURED`.

## Аккаунты для демо

* Преподаватель: `teacher@englishquest.dev` / `Teacher123`
* Ученик: регистрация через пользовательский интерфейс

## Данные и дамп БД

Единственный воспроизводимый путь запуска — `create_all` + `seed` при старте бэкенда (см. «Быстрый запуск»). `english_quest.sql` — необязательный дамп схемы и контента:

* дамп экспортирован PostgreSQL 18.3, а `docker-compose.yml` поднимает PostgreSQL 16; при использовании дампа перегенерируйте его на целевой версии;
* персональные учётные записи и `password_hash` из дампа удалены; тестовый преподаватель создаётся сидом (`SEED_DEMO=true`);
* в продакшене задайте `SEED_DEMO=false`, чтобы не создавать демо-аккаунт и контент.

## Структура backend

Имена модулей используют подчёркивания (`auth_controller.py`, `mission_service.py`, …) — это осознанная адаптация: Python не позволяет импортировать модули с точкой в имени (`auth.controller.py`). Прежние файлы-заглушки с точками удалены.
