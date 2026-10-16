from contextlib import contextmanager
from datetime import date, timedelta
from uuid import uuid4

from backend_tests.support.db_support import assert_test_database, connect_test_database


@contextmanager
def prepared_shift():
    connection = connect_test_database()
    data = {
        "position_name": "Пекарь",
        "employee_count": 2,
        "shift_date": (date.today() + timedelta(days=7)).isoformat(),
    }
    try:
        with connection:
            assert_test_database(connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users(login) VALUES (%s) RETURNING id", (f"qa_{uuid4().hex}",)
                )
                data["owner_id"] = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO businesses(owner_id,name) VALUES (%s,%s) RETURNING id",
                    (data["owner_id"], "Тестовое предприятие QA"),
                )
                data["business_id"] = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO positions(business_id,name) VALUES (%s,%s) RETURNING id",
                    (data["business_id"], data["position_name"]),
                )
                data["position_id"] = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO employees(business_id,full_name,position,is_active) "
                    "VALUES (%s,%s,%s,1) RETURNING id",
                    (data["business_id"], "Тестовый сотрудник QA", data["position_name"]),
                )
                data["employee_id"] = cursor.fetchone()[0]
                data["vk_id"] = 1_000_000_000 + data["employee_id"]
                cursor.execute(
                    "UPDATE employees SET vk_id=%s WHERE id=%s",
                    (str(data["vk_id"]), data["employee_id"]),
                )
                cursor.execute(
                    "INSERT INTO shifts(business_id,shift_date,start_time,end_time,status) "
                    "VALUES (%s,%s,'09:00','18:00','open') RETURNING id",
                    (data["business_id"], data["shift_date"]),
                )
                data["shift_id"] = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO shift_open_positions "
                    "(shift_id,position_name,employee_count,payment_type,hourly_rate) "
                    "VALUES (%s,%s,%s,'hourly','300') RETURNING id",
                    (data["shift_id"], data["position_name"], data["employee_count"]),
                )
                data["open_position_id"] = cursor.fetchone()[0]

        try:
            yield data
        finally:
            with connection:
                assert_test_database(connection)
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL lock_timeout = '5s'")
                    cursor.execute(
                        "DELETE FROM sent_notifications WHERE shift_id=%s", (data["shift_id"],)
                    )
                    cursor.execute(
                        "DELETE FROM shift_responses WHERE business_id=%s", (data["business_id"],)
                    )
                    cursor.execute(
                        "DELETE FROM activity_logs WHERE business_id=%s", (data["business_id"],)
                    )
                    cursor.execute(
                        "DELETE FROM shift_assignments WHERE shift_id=%s", (data["shift_id"],)
                    )
                    cursor.execute(
                        "DELETE FROM shift_open_positions WHERE shift_id=%s", (data["shift_id"],)
                    )
                    cursor.execute("DELETE FROM shifts WHERE id=%s", (data["shift_id"],))
                    cursor.execute(
                        "DELETE FROM position_capabilities WHERE position_id=%s OR covered_position_id=%s",
                        (data["position_id"], data["position_id"]),
                    )
                    cursor.execute(
                        "DELETE FROM employees WHERE business_id=%s", (data["business_id"],)
                    )
                    cursor.execute(
                        "DELETE FROM positions WHERE business_id=%s", (data["business_id"],)
                    )
                    cursor.execute("DELETE FROM businesses WHERE id=%s", (data["business_id"],))
                    cursor.execute("DELETE FROM users WHERE id=%s", (data["owner_id"],))
    finally:
        connection.close()
