

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

## База данных

По умолчанию проект использует **локальный PostgreSQL** (см. `english-quest-backend/.env`, переменная `DATABASE_URL`). Создайте базу данных один раз:

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

# 3. Фронтенд (http://localhost:3000)
cd ../frontend
npm install
cp .env.local.example .env.local
npm run dev

```

## Возможности и функционал

* JWT-аутентификация, хеширование bcrypt (количество раундов = 12)
* Ролевая модель (RBAC): `student` (ученик) / `teacher` (преподаватель)
* Вступительный тест CEFR с автоматическим зачетом нижестоящих уровней и начислением стартовых очков опыта (XP)
* Уровни → по 5 миссий в каждом → задания/вопросы; свободная навигация с заблокированными (`locked`) уровнями
* Три отдельных учебных модуля, открывающихся последовательно: тест (5 вопросов) → произношение → 3D-игра "Словарь"
* Игра "Словарь" в стиле Plants vs. Zombies (Three.js): прилетают карточки с картинками — произнесите слово на английском
* Видеоролики с результатами победы/поражения (Буба при успехе, смеющийся кот при неудаче)
* Картинки слов + транскрипция IPA + перевод в модуле произношения
* Расчет XP на стороне сервера: за первое прохождение vs. за повторное
* Панель преподавателя: полный CRUD для миссий, заданий, вопросов и вариантов ответов, а также редактор словаря
* Озвучка слов через браузерный Text-to-Speech (отдельные аудиофайлы не требуются)
* Минималистичный адаптивный UI с поддержкой светлой/темной темы (черная в темной теме, белая в светлой)
* Дружелюбный игровой дизайн: темы daisyUI, анимации Framer Motion, конфетти при успехе, анимированный XP

## Аккаунты для демо

* Преподаватель: `teacher@englishquest.dev` / `Teacher123`
* Ученик: регистрация через пользовательский интерфейс
