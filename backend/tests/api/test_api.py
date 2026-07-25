from fastapi.testclient import TestClient
from httpx import Response

_STANDARD_SCALE = [
    {"letter": "A", "min_percent": "90"},
    {"letter": "B", "min_percent": "80"},
    {"letter": "C", "min_percent": "70"},
    {"letter": "D", "min_percent": "60"},
    {"letter": "F", "min_percent": "0"},
]


def _class(client: TestClient, name: str = "Room 5") -> str:
    r = client.post("/classes", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _grade_level(client: TestClient, class_id: str, name: str, position: int = 0) -> str:
    r = client.post(f"/classes/{class_id}/grade-levels", json={"name": name, "position": position})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _scale(client: TestClient, class_id: str) -> None:
    r = client.put(f"/classes/{class_id}/grading-scale", json={"bands": _STANDARD_SCALE})
    assert r.status_code == 200, r.text


def _subject(client: TestClient, class_id: str, name: str = "Math") -> str:
    r = client.post(f"/classes/{class_id}/subjects", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _category(client: TestClient, subject_id: str, name: str, weight: str) -> str:
    r = client.post(f"/subjects/{subject_id}/categories", json={"name": name, "weight": weight})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _assignment(
    client: TestClient,
    subject_id: str,
    category_id: str,
    name: str,
    max_points: str,
    audience: list[str],
) -> str:
    r = client.post(
        f"/subjects/{subject_id}/assignments",
        json={
            "name": name,
            "category_id": category_id,
            "max_points": max_points,
            "audience_grade_level_ids": audience,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _student(client: TestClient, class_id: str, grade_level_id: str, name: str) -> str:
    r = client.post(
        f"/classes/{class_id}/students", json={"name": name, "grade_level_id": grade_level_id}
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _score(client: TestClient, student_id: str, assignment_id: str, points: str) -> Response:
    return client.put(
        f"/students/{student_id}/assignments/{assignment_id}/score",
        json={"points_earned": points},
    )


def _mixed_audience_setup(client: TestClient) -> dict[str, str]:
    """Combined 1st/2nd class, Math with HW 30% / Tests 70%; HW2 targets 2nd only."""
    class_id = _class(client, "Combined 1/2")
    first = _grade_level(client, class_id, "1st", 1)
    second = _grade_level(client, class_id, "2nd", 2)
    _scale(client, class_id)
    subject = _subject(client, class_id, "Math")
    homework = _category(client, subject, "Homework", "30")
    tests = _category(client, subject, "Tests", "70")
    hw1 = _assignment(client, subject, homework, "HW1", "10", [])
    hw2 = _assignment(client, subject, homework, "HW2", "10", [second])
    test1 = _assignment(client, subject, tests, "Test1", "100", [])
    alice = _student(client, class_id, first, "Alice")  # 1st grade
    bob = _student(client, class_id, second, "Bob")  # 2nd grade
    return {
        "class_id": class_id,
        "first": first,
        "second": second,
        "subject": subject,
        "homework": homework,
        "tests": tests,
        "hw1": hw1,
        "hw2": hw2,
        "test1": test1,
        "alice": alice,
        "bob": bob,
    }


def test_class_crud(client: TestClient) -> None:
    class_id = _class(client, "Room 5")
    assert client.get(f"/classes/{class_id}").json()["name"] == "Room 5"
    assert client.patch(f"/classes/{class_id}", json={"name": "Room 6"}).json()["name"] == "Room 6"
    assert any(c["id"] == class_id for c in client.get("/classes").json())
    assert client.delete(f"/classes/{class_id}").status_code == 204
    assert client.get(f"/classes/{class_id}").status_code == 404


def test_duplicate_grade_level_conflicts(client: TestClient) -> None:
    class_id = _class(client)
    _grade_level(client, class_id, "1st")
    dup = client.post(f"/classes/{class_id}/grade-levels", json={"name": "1st", "position": 2})
    assert dup.status_code == 409


def test_student_grade_level_must_belong_to_class(client: TestClient) -> None:
    other = _class(client, "Other")
    foreign_gl = _grade_level(client, other, "1st")
    class_id = _class(client, "Mine")
    r = client.post(
        f"/classes/{class_id}/students", json={"name": "X", "grade_level_id": foreign_gl}
    )
    assert r.status_code == 422


def test_assignment_audience_must_belong_to_class(client: TestClient) -> None:
    other = _class(client, "Other")
    foreign_gl = _grade_level(client, other, "1st")
    class_id = _class(client, "Mine")
    subject = _subject(client, class_id)
    category = _category(client, subject, "HW", "100")
    r = client.post(
        f"/subjects/{subject}/assignments",
        json={
            "name": "X",
            "category_id": category,
            "max_points": "10",
            "audience_grade_level_ids": [foreign_gl],
        },
    )
    assert r.status_code == 422


def test_scoring_outside_audience_is_rejected(client: TestClient) -> None:
    s = _mixed_audience_setup(client)
    # Alice is 1st grade; HW2 targets 2nd grade only.
    r = _score(client, s["alice"], s["hw2"], "5")
    assert r.status_code == 422


def test_grade_is_numeric_and_respects_audience(client: TestClient) -> None:
    s = _mixed_audience_setup(client)
    assert _score(client, s["alice"], s["hw1"], "8").status_code == 200
    assert _score(client, s["alice"], s["test1"], "90").status_code == 200

    alice_grade = client.get(f"/students/{s['alice']}/subjects/{s['subject']}/grade").json()
    assert alice_grade["is_incomplete"] is False
    assert alice_grade["percent"] == "87.00"  # 80*0.3 + 90*0.7, HW2 out of audience
    assert alice_grade["letter"] == "B"

    _score(client, s["bob"], s["hw1"], "8")
    _score(client, s["bob"], s["hw2"], "10")
    _score(client, s["bob"], s["test1"], "90")
    bob_grade = client.get(f"/students/{s['bob']}/subjects/{s['subject']}/grade").json()
    assert bob_grade["percent"] == "90.00"  # HW2 applies for a 2nd grader
    assert bob_grade["letter"] == "A"


def test_grade_incomplete_when_category_empty(client: TestClient) -> None:
    s = _mixed_audience_setup(client)
    _score(client, s["alice"], s["hw1"], "8")  # Tests left blank
    grade = client.get(f"/students/{s['alice']}/subjects/{s['subject']}/grade").json()
    assert grade["is_incomplete"] is True
    assert grade["percent"] is None and grade["letter"] is None
    assert "empty_category" in {r["code"] for r in grade["incomplete_reasons"]}


def test_grade_incomplete_when_weights_not_100(client: TestClient) -> None:
    class_id = _class(client)
    grade_level = _grade_level(client, class_id, "1st")
    _scale(client, class_id)
    subject = _subject(client, class_id)
    c1 = _category(client, subject, "A", "30")
    c2 = _category(client, subject, "B", "30")  # totals 60%, not 100%
    a1 = _assignment(client, subject, c1, "A1", "10", [])
    a2 = _assignment(client, subject, c2, "B1", "10", [])
    student = _student(client, class_id, grade_level, "Z")
    _score(client, student, a1, "10")
    _score(client, student, a2, "10")

    grade = client.get(f"/students/{student}/subjects/{subject}/grade").json()
    assert grade["is_incomplete"] is True
    assert "weights_not_100" in {r["code"] for r in grade["incomplete_reasons"]}


def test_roster_grades(client: TestClient) -> None:
    s = _mixed_audience_setup(client)
    _score(client, s["alice"], s["hw1"], "8")
    _score(client, s["alice"], s["test1"], "90")
    _score(client, s["bob"], s["hw1"], "8")
    _score(client, s["bob"], s["hw2"], "10")
    _score(client, s["bob"], s["test1"], "90")

    r = client.get(f"/classes/{s['class_id']}/subjects/{s['subject']}/grades")
    assert r.status_code == 200
    body = r.json()
    assert body["subject_id"] == s["subject"]
    by_student = {g["student_id"]: g for g in body["grades"]}
    assert by_student[s["alice"]]["letter"] == "B"
    assert by_student[s["bob"]]["letter"] == "A"
