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


async def test_failed_calibration_leaves_no_partial_state(client):
    """A rejected calibration must not change the user or create progress rows."""
    headers = await _register(client, "rollback@example.com")
    me_before = (await client.get("/api/v1/auth/me", headers=headers)).json()
    questions = (await client.get("/api/v1/calibration/questions", headers=headers)).json()
    # Incomplete submission -> 400, must not calibrate the user.
    r = await client.post(
        "/api/v1/calibration/submit",
        headers=headers,
        json={"answers": [{"question_id": questions[0]["id"], "selected_option": "A"}]},
    )
    assert r.status_code == 400
    me_after = (await client.get("/api/v1/auth/me", headers=headers)).json()
    assert me_after["is_calibrated"] is False
    assert me_after["cefr_level"] == me_before["cefr_level"]
    assert me_after["total_xp"] == me_before["total_xp"]


async def _levels(client, headers):
    return (await client.get("/api/v1/levels", headers=headers)).json()


async def _play_mission(client, session, headers, mission_id):
    """Run test -> pronunciation -> game for a mission, returning the game result."""
    right = await _answers_for(session, mission_id, correct=True)
    r = await client.post(f"/api/v1/missions/{mission_id}/submit-tests", headers=headers, json={"answers": right})
    assert r.status_code == 200 and r.json()["passed"] is True, r.text

    start = (await client.post(f"/api/v1/missions/{mission_id}/start", headers=headers, json={"module": "game"})).json()
    pa = [{"item_id": i["id"], "word": i["word_en"]} for i in start["items"]]
    r = await client.post(f"/api/v1/missions/{mission_id}/submit-pronunciation", headers=headers, json={"answers": pa})
    assert r.status_code == 200 and r.json()["passed"] is True, r.text

    g = (await client.post(f"/api/v1/missions/{mission_id}/start", headers=headers, json={"module": "game"})).json()
    ga = [{"item_id": i["id"], "word": i["word_en"]} for i in g["items"]]
    return (
        await client.post(
            f"/api/v1/missions/{mission_id}/submit-game",
            headers=headers,
            json={"attempt_id": g["attempt_id"], "answers": ga},
        )
    ).json()


async def test_missions_unlock_sequentially(client):
    """Only the first mission of a level is open until the previous one is done."""
    headers = await _register(client, "chain@example.com")
    levels = await _levels(client, headers)
    a1 = next(l for l in levels if l["code"] == "A1")
    missions = sorted(a1["missions"], key=lambda m: m["order_index"])
    assert missions[0]["locked"] is False
    assert missions[1]["locked"] is True
    assert missions[2]["locked"] is True

    # Direct access to a locked mission is rejected server-side.
    r = await client.get(f"/api/v1/missions/{missions[1]['id']}", headers=headers)
    assert r.status_code == 403


async def test_level_unlocks_after_xp_threshold(client, session):
    """Completing enough A1 missions (>=70% XP) unlocks A2."""
    headers = await _register(client, "unlock@example.com")
    levels = await _levels(client, headers)
    a1 = next(l for l in levels if l["code"] == "A1")
    missions = sorted(a1["missions"], key=lambda m: m["order_index"])

    # Play the missions in order; A1 has 5 missions and the threshold is 70% of
    # the level's maximum XP, so 4 of 5 first-time completions (80%) suffice.
    for mission in missions[:4]:
        await _play_mission(client, session, headers, mission["id"])

    me = (await client.get("/api/v1/auth/me", headers=headers)).json()
    assert me["unlocked_level_rank"] >= 1  # A2 unlocked

    levels_after = await _levels(client, headers)
    a2 = next(l for l in levels_after if l["code"] == "A2")
    assert a2["locked"] is False
    # The demo seed has no A2 missions yet; the level itself must be unlocked.
    assert a2["missions"] == [] or a2["missions"][0]["locked"] is False


async def test_level_unlocks_after_all_missions(client, session):
    """Completing all 5 A1 missions also unlocks A2."""
    headers = await _register(client, "allfive@example.com")
    levels = await _levels(client, headers)
    a1 = next(l for l in levels if l["code"] == "A1")
    for mission in sorted(a1["missions"], key=lambda m: m["order_index"]):
        await _play_mission(client, session, headers, mission["id"])
    me = (await client.get("/api/v1/auth/me", headers=headers)).json()
    assert me["unlocked_level_rank"] >= 1


async def test_leaderboard_ranks_by_xp_and_hides_email(client, session):
    low = await _register(client, "low@example.com")
    high = await _register(client, "high@example.com")
    # Give the second user some XP.
    levels = await _levels(client, high)
    a1 = next(l for l in levels if l["code"] == "A1")
    missions = sorted(a1["missions"], key=lambda m: m["order_index"])
    await _play_mission(client, session, high, missions[0]["id"])

    board = (await client.get("/api/v1/users/leaderboard?limit=10", headers=low)).json()
    assert len(board) >= 1
    assert board[0]["rank"] == 1
    assert board[0]["total_xp"] > 0
    assert "email" not in board[0]
    xps = [entry["total_xp"] for entry in board]
    assert xps == sorted(xps, reverse=True)