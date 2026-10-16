import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import dotenv_values

BACKEND = Path(__file__).resolve().parents[2] / "backend"
MARKER = "vkr-qa-test-database-v1"


def settings():
    values = {**dotenv_values(BACKEND / ".env.test"), **os.environ}
    if values.get("TEST_DB_NAME") != "vkr_test":
        raise RuntimeError("Refusing access: TEST_DB_NAME must be vkr_test")
    for name in ("TEST_DB_HOST", "TEST_DB_PORT", "TEST_DB_USER", "TEST_DB_PASSWORD"):
        if not values.get(name) or values[name] == "change_me":
            raise RuntimeError(f"Missing test setting: {name}")
    dll_path = values.get("POSTGRES_BIN_PATH", "C:/Program Files/PostgreSQL/18/bin")

    global _dll_handle
    if hasattr(os, "add_dll_directory") and Path(dll_path).is_dir():
        if "_dll_handle" not in globals():
            _dll_handle = os.add_dll_directory(dll_path)
    return dict(
        host=values["TEST_DB_HOST"],
        port=int(values["TEST_DB_PORT"]),
        dbname=values["TEST_DB_NAME"],
        user=values["TEST_DB_USER"],
        password=values["TEST_DB_PASSWORD"],
        connect_timeout=5,
    )


def assert_test_database(connection):

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database(), shobj_description(oid, 'pg_database') "
            "FROM pg_database WHERE datname = current_database()"
        )
        if cursor.fetchone() != ("vkr_test", MARKER):
            raise RuntimeError("Refusing writes: database name or ownership marker mismatch")


def connect_test_database():
    config = settings()
    import psycopg2

    connection = psycopg2.connect(**config)
    try:
        assert_test_database(connection)
        connection.rollback()
        return connection
    except BaseException:
        connection.close()
        raise


@contextmanager
def backend_connection(application_name=None):

    connection = connect_test_database()
    from psycopg2.extras import RealDictCursor

    connection.cursor_factory = RealDictCursor
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '12s'")
                cursor.execute("SET LOCAL statement_timeout = '15s'")
                if application_name:
                    cursor.execute(
                        "SELECT set_config('application_name',%s,false)", (application_name,)
                    )
            yield connection
    finally:
        connection.close()
