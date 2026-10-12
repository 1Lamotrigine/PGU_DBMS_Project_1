"""Integration API tests for the highest-risk flows (audit regressions).

These run against an isolated SQLite database (see conftest.py) and exercise the
real FastAPI app end to end. They are intended to catch the reward-fraud and
access-control regressions described in the project audit.
"""

from sqlalchemy import select

from src.models.models import Question, QuestionOption, Task


async def _register(client, email="student@example.com"):
    r = await client.post(
        "/api/v1/auth/register",
        json={"firstName": "Stu", "lastName": "Dent", "email": email, "password": "Password123"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def _teacher(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@englishquest.dev", "password": "Teacher123"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def _a1_mission_id(client, headers):
    levels = (await client.get("/api/v1/levels", headers=headers)).json()
    a1 = next(l for l in levels if l["code"] == "A1")
    return a1["missions"][0]["id"]


async def _answers_for(session, mission_id, correct: bool):
    questions = (
        await session.execute(
            select(Question)
            .join(Task, Question.task_id == Task.id)
            .where(Task.mission_id == mission_id, Task.task_type == "multiple_choice")
        )
    ).scalars().all()
    answers = []
    for q in questions:
        options = (
            await session.execute(select(QuestionOption).where(QuestionOption.question_id == q.id))
        ).scalars().all()
        pick = next((o for o in options if o.is_correct == correct), options[0])
        answers.append({"question_id": q.id, "option_id": pick.id})
    return answers


async def test_register_hides_password_hash(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"firstName": "A", "lastName": "B", "email": "a@b.com", "password": "Password123"},
    )
    assert r.status_code == 201
    assert "password_hash" not in r.json()["user"]


async def test_password_longer_than_72_bytes_rejected(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"firstName": "A", "lastName": "B", "email": "long@b.com", "password": "A1" + "x" * 80},
    )
    assert r.status_code == 422


async def test_calibration_requires_full_set(client):
    headers = await _register(client)
    questions = (await client.get("/api/v1/calibration/questions", headers=headers)).json()
    assert all("correct_option" not in q for q in questions)
    r = await client.post(
        "/api/v1/calibration/submit",
        headers=headers,
        json={"answers": [{"question_id": questions[0]["id"], "selected_option": "A"}]},
    )
    assert r.status_code == 400


async def test_calibration_does_not_reward_completed_missions(client):
    headers = await _register(client, "cal2@example.com")
    questions = (await client.get("/api/v1/calibration/questions", headers=headers)).json()
    answers = [{"question_id": q["id"], "selected_option": "A"} for q in questions]
    r = await client.post("/api/v1/calibration/submit", headers=headers, json={"answers": answers})
    assert r.status_code == 200
    first_total = r.json()["total_xp"]
    # Calling calibration again must be rejected (already calibrated).
    r2 = await client.post("/api/v1/calibration/submit", headers=headers, json={"answers": answers})
    assert r2.status_code == 400
    me = (await client.get("/api/v1/auth/me", headers=headers)).json()
    assert me["total_xp"] == first_total


async def test_student_mission_detail_hides_correct_answers(client):
    headers = await _register(client, "hide@example.com")
    mid = await _a1_mission_id(client, headers)
    detail = (await client.get(f"/api/v1/missions/{mid}", headers=headers)).json()
    options = [o for t in detail["tasks"] for q in t.get("questions", []) for o in q["options"]]
    assert options and all("is_correct" not in o for o in options)


async def test_teacher_mission_detail_shows_correct_answers(client):
    headers = await _teacher(client)
    mid = await _a1_mission_id(client, headers)
    detail = (await client.get(f"/api/v1/missions/{mid}", headers=headers)).json()
    options = [o for t in detail["tasks"] for q in t.get("questions", []) for o in q["options"]]
    assert any("is_correct" in o for o in options)


async def test_tests_are_server_graded(client, session):
    headers = await _register(client, "tests@example.com")
    mid = await _a1_mission_id(client, headers)
    wrong = await _answers_for(session, mid, correct=False)
    r = await client.post(f"/api/v1/missions/{mid}/submit-tests", headers=headers, json={"answers": wrong})
    assert r.status_code == 200 and r.json()["passed"] is False
    # incomplete set rejected
    r = await client.post(
        f"/api/v1/missions/{mid}/submit-tests", headers=headers, json={"answers": wrong[:1]}
    )
    assert r.status_code == 400
    right = await _answers_for(session, mid, correct=True)
    r = await client.post(f"/api/v1/missions/{mid}/submit-tests", headers=headers, json={"answers": right})
    assert r.status_code == 200 and r.json()["passed"] is True


async def test_game_requires_attempt_and_is_idempotent(client, session):
    headers = await _register(client, "game@example.com")
    mid = await _a1_mission_id(client, headers)
    right = await _answers_for(session, mid, correct=True)
    await client.post(f"/api/v1/missions/{mid}/submit-tests", headers=headers, json={"answers": right})

    # No attempt -> rejected.
    r = await client.post(
        f"/api/v1/missions/{mid}/submit-game", headers=headers, json={"correctAnswers": 10, "totalQuestions": 10}
    )
    assert r.status_code == 400

    start = (await client.post(f"/api/v1/missions/{mid}/start", headers=headers, json={"module": "game"})).json()
    items = start["items"]
    pa = [{"item_id": i["id"], "word": i["word_en"]} for i in items[:10]]
    r = await client.post(
        f"/api/v1/missions/{mid}/submit-pronunciation", headers=headers, json={"answers": pa}
    )
    assert r.status_code == 200 and r.json()["passed"] is True

    g = (await client.post(f"/api/v1/missions/{mid}/start", headers=headers, json={"module": "game"})).json()
    ga = [{"item_id": i["id"], "word": i["word_en"]} for i in g["items"]]
    r = await client.post(
        f"/api/v1/missions/{mid}/submit-game",
        headers=headers,
        json={"attempt_id": g["attempt_id"], "answers": ga},
    )
    assert r.status_code == 200 and r.json()["success"] is True
    total_after_first = r.json()["total_xp"]

    # Replaying the same attempt must not double-award.
    r2 = await client.post(
        f"/api/v1/missions/{mid}/submit-game",
        headers=headers,
        json={"attempt_id": g["attempt_id"], "answers": ga},
    )
    assert r2.status_code == 409
    me = (await client.get("/api/v1/auth/me", headers=headers)).json()
    assert me["total_xp"] == total_after_first


async def test_delete_mission_with_progress_conflicts(client, session):
    headers = await _register(client, "del@example.com")
    mid = await _a1_mission_id(client, headers)
    right = await _answers_for(session, mid, correct=True)
    await client.post(f"/api/v1/missions/{mid}/submit-tests", headers=headers, json={"answers": right})
    th = await _teacher(client)
    r = await client.delete(f"/api/v1/missions/{mid}", headers=th)
    assert r.status_code == 409


async def test_update_validation_rejects_empty_and_null(client):
    th = await _teacher(client)
    mid = await _a1_mission_id(client, th)
    assert (await client.put(f"/api/v1/missions/{mid}", headers=th, json={"title": ""})).status_code == 422
    assert (await client.put(f"/api/v1/missions/{mid}", headers=th, json={"order_index": None})).status_code == 422


async def test_progress_preview_access_control(client):
    headers = await _register(client, "priv@example.com")
    r = await client.get("/api/v1/students/1/progress-preview", headers=headers)
    assert r.status_code in (403, 404)
