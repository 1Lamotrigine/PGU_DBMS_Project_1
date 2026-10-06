

---

# English Quest — Backend (Блок 1)

Бэкенд геймифицированной платформы для изучения английского языка. Построен на **FastAPI**, **SQLAlchemy (async)**, **PostgreSQL** и **JWT**.

Строгая многослойная архитектура: `routes → controllers → services → models`, с валидаторами (Pydantic) и middleware (JWT / RBAC / обработка ошибок).

## Стек технологий

* Python 3.11+ / FastAPI / Uvicorn
* SQLAlchemy 2 (async) + asyncpg
* Pydantic v2 + pydantic-settings
* PyJWT + passlib (bcrypt, количество раундов хеширования = 12)
* PostgreSQL 16 (Docker)

## Структура проекта

```
src/
├── config/         # database.py, settings.py
├── controllers/    # auth, user, mission, game
├── middleware/     # auth (JWT), role (RBAC), обработчики ошибок
├── routes/         # роутеры: auth, user, mission, game
├── services/       # account, calibration, mission, game, user, security
├── validators/     # схемы запросов Pydantic
├── models/         # ORM-модели SQLAlchemy
└── db/seed.py      # первоначальное заполнение БД (seed)

```

> Некоторые модули сохраняют имена файлов с точками из ТЗ (например, `auth.controller.py`) в качестве тонких реэкспортных прослоек (shims); реальная реализация находится в соответствующих модулях вида `*_*.py`.

## Запуск

```bash
# 1. Запуск PostgreSQL (из корневой директории репозитория)
docker compose up -d

# 2. Бэкенд
cd english-quest-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # скорректируйте при необходимости
uvicorn src.server:app --host 0.0.0.0 --port 8000

```

Документация API: http://localhost:8000/docs · Проверка работоспособности (Health): http://localhost:8000/health

Таблицы создаются автоматически, и при старте приложения загружаются начальные данные:

* роли: `student`, `teacher`
* уровни CEFR: `A1`–`C2`
* по 3 калибровочных вопроса на каждый уровень (A1–B2)
* аккаунт преподавателя: `teacher@englishquest.dev` / `Teacher123`
* 5 демо-миссий для уровня A1 (с заданиями, вопросами и вариантами ответов)

## Бизнес-правила

* **Калибровка** (`POST /calibration/submit`): сервер сравнивает ответы, определяет уровень CEFR, автоматически отмечается как пройденные все нижестоящие уровни и начисляется стартовый XP.
* **XP (очки опыта)**: первое успешное прохождение миссии → сумма `xp_reward_first`; повторное прохождение → сумма `xp_reward_repeat`; результат ниже **70%** → XP не начисляется.
* **Свободная навигация**: миссии уровней выше текущего уровня CEFR пользователя отмечаются как `locked` (заблокированы).
* **RBAC (разграничение прав)**: создание, обновление и удаление миссий требуют роли `teacher` (иначе возвращается ошибка 403).

## API

| Метод | Путь | Роль | Назначение |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | — | Регистрация (роль `student`) |
| POST | `/api/v1/auth/login` | — | Вход → получение JWT |
| GET | `/api/v1/auth/me` | auth | Текущий профиль |
| POST | `/api/v1/calibration/submit` | student | Отправка результатов вступительного теста |
| GET | `/api/v1/calibration/questions` | auth | Вопросы вступительного теста |
| GET | `/api/v1/levels` | auth | Уровни + миссии (со статусом `locked`) |
| GET | `/api/v1/missions/{id}` | auth | Детали миссии + вопросы |
| POST | `/api/v1/missions/{id}/submit-tests` | student | Результат тестового блока |
| POST | `/api/v1/missions/{id}/submit-pronunciation` | student | Результат проверки произношения |
| POST | `/api/v1/missions/{id}/submit-game` | student | Результат аркады + XP |
| POST/PUT/DELETE | `/api/v1/missions[/{id}]` | teacher | CRUD-операции над миссиями |
| GET | `/api/v1/users/me/progress` | auth | Прогресс пользователя |
| GET | `/api/v1/students/{id}/progress-preview` | auth | Просмотр прогресса студента |

Ошибки возвращаются в едином формате: `{ "error": { "code", "message", "details" } }` с кодами `400 / 401 / 403 / 404 / 422`.
