import json
from contextlib import nullcontext

import pytest

from backend_tests.support.api_support import make_shift_response
from backend_tests.support.data_support import prepared_shift
from backend_tests.support.db_support import assert_test_database, settings


@pytest.mark.parametrize("initial_places", [2, 1], ids=["two-places", "last-place"])
def test_successful_response_updates_all_tables(client, vk_mock, shift_data, db, initial_places):

    with db:
        assert_test_database(db)
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE shift_open_positions SET employee_count=%s WHERE id=%s",
                (initial_places, shift_data["open_position_id"]),
            )
            cursor.execute(
                "SELECT employee_count FROM shift_open_positions WHERE id=%s",
                (shift_data["open_position_id"],),
            )
            assert cursor.fetchone() == (initial_places,)
            cursor.execute(
                "SELECT count(*) FROM shift_responses WHERE shift_id=%s", (shift_data["shift_id"],)
            )
            assert cursor.fetchone()[0] == 0
            cursor.execute(
                "SELECT count(*) FROM shift_assignments WHERE shift_id=%s",
                (shift_data["shift_id"],),
            )
            assert cursor.fetchone()[0] == 0
            cursor.execute(
                "SELECT count(*) FROM activity_logs WHERE business_id=%s",
                (shift_data["business_id"],),
            )
            assert cursor.fetchone()[0] == 0

    event = make_shift_response(shift_data)
    event["object"]["conversation_message_id"] = 100

    response = client.post("/vk/callback", json=event)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "ok"

    with db.cursor() as cursor:
        cursor.execute(
            "SELECT business_id, employee_id, vk_id, position_name, response_status, "
            "raw_payload, created_at FROM shift_responses WHERE shift_id=%s",
            (shift_data["shift_id"],),
        )
        responses = cursor.fetchall()
        assert len(responses) == 1
        assert responses[0][:5] == (
            shift_data["business_id"],
            shift_data["employee_id"],
            str(shift_data["vk_id"]),
            shift_data["position_name"],
            "accepted",
        )
        assert json.loads(responses[0][5]) == event
        assert responses[0][6] is not None

        cursor.execute(
            "SELECT id, employee_count FROM shift_open_positions "
            "WHERE shift_id=%s AND position_name=%s",
            (shift_data["shift_id"], shift_data["position_name"]),
        )
        expected_places = (
            [(shift_data["open_position_id"], initial_places - 1)] if initial_places > 1 else []
        )
        assert cursor.fetchall() == expected_places

        cursor.execute(
            "SELECT employee_id, position_name, payment_type, hourly_rate "
            "FROM shift_assignments WHERE shift_id=%s",
            (shift_data["shift_id"],),
        )
        assert cursor.fetchall() == [
            (shift_data["employee_id"], shift_data["position_name"], "hourly", "300")
        ]

        cursor.execute(
            "SELECT action_type, entity_type, entity_id, related_employee_id, related_shift_id, "
            "description, created_at FROM activity_logs WHERE business_id=%s",
            (shift_data["business_id"],),
        )
        logs = cursor.fetchall()
        assert len(logs) == 1
        assert logs[0][:5] == (
            "vk_response",
            "vk",
            shift_data["shift_id"],
            shift_data["employee_id"],
            shift_data["shift_id"],
        )
        assert shift_data["position_name"] in logs[0][5]
        assert logs[0][6] is not None

    sent_messages = [
        call.args[1] for call in vk_mock.call_args_list if call.args[0] == "messages.send"
    ]
    assert len(sent_messages) == 1
    assert sent_messages[0]["user_id"] == shift_data["vk_id"]


def test_connected_to_test_database(db):
    with db.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        database_name = cursor.fetchone()[0]

    assert database_name == "vkr_test"


def test_normal_database_is_rejected_before_connection(monkeypatch):
    monkeypatch.setenv("TEST_DB_NAME", "vkr_db")
    with pytest.raises(RuntimeError, match="TEST_DB_NAME must be vkr_test"):
        settings()


def test_database_marker_is_required():

    from unittest.mock import MagicMock

    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ("vkr_test", None)
    with pytest.raises(RuntimeError, match="ownership marker mismatch"):
        assert_test_database(connection)


def test_shift_data_visible_from_another_connection(shift_data, db):
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT s.business_id, e.vk_id, e.is_active, p.employee_count "
            "FROM shifts s JOIN employees e ON e.business_id=s.business_id "
            "JOIN shift_open_positions p ON p.shift_id=s.id "
            "WHERE s.id=%s AND e.id=%s",
            (shift_data["shift_id"], shift_data["employee_id"]),
        )
        assert cursor.fetchone() == (shift_data["business_id"], str(shift_data["vk_id"]), 1, 2)


@pytest.mark.parametrize("fail_inside", [False, True], ids=["success", "test-error"])
def test_cleanup_removes_committed_rows_only_for_its_dataset(db, shift_data, fail_inside):

    expected_error = (
        pytest.raises(AssertionError, match="simulated test failure")
        if fail_inside
        else nullcontext()
    )
    with expected_error:
        with prepared_shift() as temporary:
            with db:
                with db.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO shift_assignments(shift_id,employee_id,position_name,payment_type) "
                        "VALUES (%s,%s,%s,'hourly')",
                        (
                            temporary["shift_id"],
                            temporary["employee_id"],
                            temporary["position_name"],
                        ),
                    )
                    cursor.execute(
                        "INSERT INTO shift_responses(business_id,shift_id,response_status) VALUES (%s,%s,'accepted')",
                        (temporary["business_id"], temporary["shift_id"]),
                    )
                    cursor.execute(
                        "INSERT INTO activity_logs(business_id,action_type,entity_type,description) "
                        "VALUES (%s,'vk_response','vk','QA cleanup check')",
                        (temporary["business_id"],),
                    )
                    cursor.execute(
                        "INSERT INTO sent_notifications(shift_id,send_status) VALUES (%s,'sent')",
                        (temporary["shift_id"],),
                    )
                    cursor.execute(
                        "INSERT INTO position_capabilities(position_id,covered_position_id) VALUES (%s,%s)",
                        (temporary["position_id"], temporary["position_id"]),
                    )
            if fail_inside:
                raise AssertionError("simulated test failure")

    from psycopg2 import sql

    with db.cursor() as cursor:
        for table, column, value in [
            ("users", "id", temporary["owner_id"]),
            ("businesses", "id", temporary["business_id"]),
            ("employees", "business_id", temporary["business_id"]),
            ("positions", "business_id", temporary["business_id"]),
            ("position_capabilities", "position_id", temporary["position_id"]),
            ("shifts", "id", temporary["shift_id"]),
            ("shift_open_positions", "shift_id", temporary["shift_id"]),
            ("shift_assignments", "shift_id", temporary["shift_id"]),
            ("shift_responses", "business_id", temporary["business_id"]),
            ("activity_logs", "business_id", temporary["business_id"]),
            ("sent_notifications", "shift_id", temporary["shift_id"]),
        ]:
            cursor.execute(
                sql.SQL("SELECT count(*) FROM {} WHERE {}=%s").format(
                    sql.Identifier(table), sql.Identifier(column)
                ),
                (value,),
            )
            assert cursor.fetchone()[0] == 0, table
        cursor.execute(
            "SELECT employee_count FROM shift_open_positions WHERE id=%s",
            (shift_data["open_position_id"],),
        )
        assert cursor.fetchone()[0] == 2
