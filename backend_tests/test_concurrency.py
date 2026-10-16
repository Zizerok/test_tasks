from concurrent.futures import ThreadPoolExecutor
from functools import partial
from time import monotonic, sleep
from uuid import uuid4

from backend_tests.support.api_support import make_shift_response
from backend_tests.support.db_support import (
    assert_test_database,
    backend_connection,
    connect_test_database,
)


def test_two_employees_compete_for_last_place(
    client, backend, vk_mock, shift_data, db, monkeypatch
):
    from fastapi.testclient import TestClient

    with db:
        assert_test_database(db)
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE shift_open_positions SET employee_count=1 WHERE id=%s",
                (shift_data["open_position_id"],),
            )
            cursor.execute(
                "INSERT INTO employees(business_id,full_name,position,is_active) "
                "VALUES (%s,'QA second employee',%s,1) RETURNING id",
                (shift_data["business_id"], shift_data["position_name"]),
            )
            second_employee_id = cursor.fetchone()[0]
            second_vk_id = 1_000_000_000 + second_employee_id
            cursor.execute(
                "UPDATE employees SET vk_id=%s WHERE id=%s", (str(second_vk_id), second_employee_id)
            )

    application_name = f"qa-race-{uuid4().hex}"

    monkeypatch.setattr(
        backend, "db_connection", partial(backend_connection, application_name=application_name)
    )

    def respond(vk_id):

        worker_client = TestClient(backend.app)
        try:
            return worker_client.post(
                "/vk/callback", json=make_shift_response(shift_data, vk_id=vk_id)
            )
        finally:
            worker_client.close()

    observer = connect_test_database()
    observer.autocommit = True
    try:
        assert_test_database(db)
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM shift_open_positions WHERE id=%s FOR UPDATE",
                (shift_data["open_position_id"],),
            )
            assert cursor.fetchone() == (shift_data["open_position_id"],)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            try:
                futures = [
                    executor.submit(respond, vk_id) for vk_id in (shift_data["vk_id"], second_vk_id)
                ]
                deadline = monotonic() + 8
                waiting_pids = []
                while monotonic() < deadline:
                    with observer.cursor() as cursor:
                        cursor.execute(
                            "SELECT pid FROM pg_stat_activity WHERE datname=current_database() "
                            "AND application_name=%s AND wait_event_type='Lock' "
                            "AND query ILIKE '%%shift_open_positions%%' "
                            "AND query ILIKE '%%FOR UPDATE%%' "
                            "AND cardinality(pg_blocking_pids(pid)) > 0",
                            (application_name,),
                        )
                        waiting_pids = [row[0] for row in cursor.fetchall()]
                    if len(waiting_pids) == 2:
                        break
                    if any(future.done() for future in futures):
                        break
                    sleep(0.02)
                assert len(waiting_pids) == 2, (
                    f"Expected two PostgreSQL sessions waiting for the position lock; got {waiting_pids}. "
                    "The test has not proved real contention."
                )
            finally:
                db.rollback()

            responses = [future.result(timeout=20) for future in futures]
    finally:
        db.rollback()
        observer.close()

    for response in responses:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == "ok"

    with db.cursor() as cursor:
        cursor.execute(
            "SELECT employee_id, response_status, response_message FROM shift_responses "
            "WHERE shift_id=%s",
            (shift_data["shift_id"],),
        )
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert {row[0] for row in rows} == {shift_data["employee_id"], second_employee_id}
        assert sorted(row[1] for row in rows) == ["accepted", "rejected"]
        winner = next(row[0] for row in rows if row[1] == "accepted")
        rejection = next(row[2] for row in rows if row[1] == "rejected")
        assert rejection == "Свободных мест по этой позиции уже нет"

        cursor.execute(
            "SELECT employee_id, position_name FROM shift_assignments WHERE shift_id=%s",
            (shift_data["shift_id"],),
        )
        assert cursor.fetchall() == [(winner, shift_data["position_name"])]
        cursor.execute(
            "SELECT count(*) FROM shift_open_positions WHERE shift_id=%s", (shift_data["shift_id"],)
        )
        assert cursor.fetchone()[0] == 0
        cursor.execute(
            "SELECT related_employee_id, related_shift_id FROM activity_logs "
            "WHERE business_id=%s AND action_type='vk_response'",
            (shift_data["business_id"],),
        )
        assert set(cursor.fetchall()) == {
            (shift_data["employee_id"], shift_data["shift_id"]),
            (second_employee_id, shift_data["shift_id"]),
        }
        cursor.execute(
            "SELECT count(*) FROM activity_logs WHERE business_id=%s", (shift_data["business_id"],)
        )
        assert cursor.fetchone()[0] == 2
