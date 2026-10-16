import json

import pytest

from backend_tests.support.api_support import (
    error_response_failures,
    make_shift_response,
)


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok", "database": "ok"}


def test_send_shift_notification(client, vk_mock, shift_data, db):

    payload = {
        "shift_id": shift_data["shift_id"],
        "message": "Открыта смена. Нужен пекарь.",
        "user_ids": [shift_data["vk_id"]],
        "open_positions": [
            {"position": shift_data["position_name"], "count": shift_data["employee_count"]}
        ],
    }

    response = client.post("/api/send-shift-notification", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "results": [{"user_id": shift_data["vk_id"], "status": "sent", "error": ""}]
    }
    assert type(response.json()["results"][0]["user_id"]) is int

    vk_mock.assert_called_once()
    method, params = vk_mock.call_args.args
    assert method == "messages.send"
    assert params["user_id"] == shift_data["vk_id"]
    assert params["message"] == payload["message"]
    keyboard = json.loads(params["keyboard"])
    assert keyboard["inline"] is True
    assert len(keyboard["buttons"]) == 1
    assert len(keyboard["buttons"][0]) == 1
    action = keyboard["buttons"][0][0]["action"]
    assert action["type"] == "callback"
    assert json.loads(action["payload"]) == {
        "type": "shift_response",
        "shift_id": shift_data["shift_id"],
        "position": shift_data["position_name"],
    }

    with db.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, message_text, send_status, error_text "
            "FROM sent_notifications WHERE shift_id=%s",
            (shift_data["shift_id"],),
        )
        assert cursor.fetchall() == [(shift_data["vk_id"], payload["message"], "sent", "")]

        cursor.execute(
            "SELECT employee_count FROM shift_open_positions WHERE id=%s",
            (shift_data["open_position_id"],),
        )
        assert cursor.fetchone() == (shift_data["employee_count"],)
        cursor.execute(
            "SELECT count(*) FROM shift_assignments WHERE shift_id=%s", (shift_data["shift_id"],)
        )
        assert cursor.fetchone()[0] == 0
        cursor.execute(
            "SELECT count(*) FROM shift_responses WHERE shift_id=%s", (shift_data["shift_id"],)
        )
        assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize(
    "invalid_case, expected_status",
    [("missing-shift", 404), ("negative-user", 422), ("empty-positions", 422)],
    ids=["missing-shift", "negative-user", "empty-positions"],
)
def test_invalid_notification_is_rejected(
    client, vk_mock, shift_data, db, invalid_case, expected_status
):
    payload = {
        "shift_id": shift_data["shift_id"],
        "message": "QA: invalid notification must not be sent",
        "user_ids": [shift_data["vk_id"]],
        "open_positions": [{"position": shift_data["position_name"], "count": 2}],
    }
    if invalid_case == "missing-shift":
        with db:
            with db.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM shift_open_positions WHERE shift_id=%s", (payload["shift_id"],)
                )
                cursor.execute("DELETE FROM shifts WHERE id=%s", (payload["shift_id"],))
                cursor.execute("SELECT count(*) FROM shifts WHERE id=%s", (payload["shift_id"],))
                assert cursor.fetchone()[0] == 0
    elif invalid_case == "negative-user":
        payload["user_ids"] = [-1]
    else:
        payload["open_positions"] = []

    response = client.post("/api/send-shift-notification", json=payload)

    with db.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, send_status FROM sent_notifications WHERE shift_id=%s",
            (payload["shift_id"],),
        )
        notifications = cursor.fetchall()

    failures = error_response_failures(
        response,
        expected_status,
        field=("user_ids" if invalid_case == "negative-user" else "open_positions")
        if expected_status == 422
        else None,
    )
    if vk_mock.call_count:
        failures.append(f"Expected no VK calls, got {vk_mock.call_count}")
    if notifications:
        failures.append(f"Expected no notification rows, got {notifications!r}")
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize(
    "invalid_case, expected_status",
    [("missing-shift", 404), ("negative-user", 422)],
    ids=["missing-shift", "negative-user"],
)
def test_invalid_shift_response_is_rejected(
    client, vk_mock, shift_data, db, invalid_case, expected_status
):
    event = make_shift_response(shift_data)
    if invalid_case == "missing-shift":
        with db:
            with db.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM shift_open_positions WHERE shift_id=%s", (shift_data["shift_id"],)
                )
                cursor.execute("DELETE FROM shifts WHERE id=%s", (shift_data["shift_id"],))
                cursor.execute("SELECT count(*) FROM shifts WHERE id=%s", (shift_data["shift_id"],))
                assert cursor.fetchone()[0] == 0
    else:
        event["object"]["user_id"] = -1

    response = client.post("/vk/callback", json=event)

    with db.cursor() as cursor:
        cursor.execute(
            "SELECT vk_id, response_status FROM shift_responses WHERE shift_id=%s",
            (shift_data["shift_id"],),
        )
        responses = cursor.fetchall()
        cursor.execute(
            "SELECT count(*) FROM shift_assignments WHERE shift_id=%s", (shift_data["shift_id"],)
        )
        assignment_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT count(*) FROM activity_logs WHERE business_id=%s", (shift_data["business_id"],)
        )
        log_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT employee_count FROM shift_open_positions WHERE shift_id=%s",
            (shift_data["shift_id"],),
        )
        places = cursor.fetchall()

    failures = error_response_failures(
        response,
        expected_status,
        field="user_id" if invalid_case == "negative-user" else None,
        detail=f"Shift {shift_data['shift_id']} was not found"
        if invalid_case == "missing-shift"
        else None,
    )
    if responses:
        failures.append(f"Expected no response rows, got {responses!r}")
    if assignment_count:
        failures.append(f"Expected no assignments, got {assignment_count}")
    if log_count:
        failures.append(f"Expected no activity logs, got {log_count}")
    expected_places = [] if invalid_case == "missing-shift" else [(shift_data["employee_count"],)]
    if places != expected_places:
        failures.append(f"Expected places {expected_places!r}, got {places!r}")

    if invalid_case == "negative-user" and vk_mock.call_count:
        failures.append(f"Expected no VK calls for invalid user_id, got {vk_mock.call_count}")
    assert not failures, "\n".join(failures)


def test_confirmation_returns_configured_code(client, vk_mock):
    response = client.post(
        "/vk/callback",
        json={"type": "confirmation", "secret": "test-secret"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "test-confirmation"
    vk_mock.assert_not_called()


def test_invalid_secret_rejects_shift_response(client, vk_mock, shift_data, db):

    response = client.post(
        "/vk/callback", json=make_shift_response(shift_data, secret="wrong-secret")
    )

    assert response.status_code == 403
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Invalid VK secret key"}
    vk_mock.assert_not_called()

    with db.cursor() as cursor:
        cursor.execute(
            "SELECT employee_count FROM shift_open_positions WHERE id=%s",
            (shift_data["open_position_id"],),
        )
        assert cursor.fetchone() == (shift_data["employee_count"],)
        cursor.execute(
            "SELECT count(*) FROM shift_responses WHERE shift_id=%s", (shift_data["shift_id"],)
        )
        assert cursor.fetchone()[0] == 0
        cursor.execute(
            "SELECT count(*) FROM shift_assignments WHERE shift_id=%s", (shift_data["shift_id"],)
        )
        assert cursor.fetchone()[0] == 0
        cursor.execute(
            "SELECT count(*) FROM activity_logs WHERE business_id=%s", (shift_data["business_id"],)
        )
        assert cursor.fetchone()[0] == 0


def test_new_message_sends_menu(client, vk_mock):
    response = client.post(
        "/vk/callback",
        json={
            "type": "message_new",
            "secret": "test-secret",
            "object": {"message": {"from_id": 900000001, "text": "Hello"}},
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "ok"

    vk_mock.assert_called_once()
    method, params = vk_mock.call_args.args
    assert method == "messages.send"
    assert params["user_id"] == 900000001
    assert "Выберите действие" in params["message"]
    assert json.loads(params["keyboard"])["buttons"]


def test_vk_calls_require_explicit_mock(client):

    with pytest.raises(AssertionError, match="VK API must be mocked explicitly"):
        client.post(
            "/vk/callback",
            json={
                "type": "message_new",
                "secret": "test-secret",
                "object": {"message": {"from_id": 900000001}},
            },
        )
