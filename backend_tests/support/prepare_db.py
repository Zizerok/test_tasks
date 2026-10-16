import argparse
import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values

from backend_tests.support.db_support import (
    BACKEND,
    MARKER,
    assert_test_database,
    connect_test_database,
    settings,
)


def psql_command(config, container):
    if container:
        command = ["docker", "exec", "-i", "--env", "PGPASSWORD", container, "psql"]
    else:
        values = {**dotenv_values(BACKEND / ".env.test"), **os.environ}
        binary_dir = values.get("POSTGRES_BIN_PATH", "C:/Program Files/PostgreSQL/18/bin")
        candidate = Path(binary_dir) / ("psql.exe" if os.name == "nt" else "psql")
        executable = str(candidate) if candidate.is_file() else shutil.which("psql")
        if not executable:
            raise RuntimeError(
                "psql not found: install PostgreSQL 18 client or set POSTGRES_BIN_PATH"
            )
        command = [executable]
    return command + [
        "-X",
        "--no-password",
        "--set",
        "ON_ERROR_STOP=1",
        "--single-transaction",
        "--host",
        config["host"],
        "--port",
        str(config["port"]),
        "--username",
        config["user"],
        "--dbname",
        config["dbname"],
    ]


def restore_schema(config, dump, digest, container, replace_empty):

    guard = f"""
DO $$
DECLARE item record; has_rows boolean;
BEGIN
    IF current_database() <> 'vkr_test' OR NOT EXISTS (
        SELECT 1 FROM pg_database WHERE datname = current_database()
        AND shobj_description(oid, 'pg_database') = '{MARKER}'
    ) THEN RAISE EXCEPTION 'Not the managed test database'; END IF;
"""
    if replace_empty:
        guard += """
    FOR item IN SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename LOOP
        EXECUTE format('LOCK TABLE public.%I IN ACCESS EXCLUSIVE MODE', item.tablename);
        IF item.tablename <> 'qa_schema_version' THEN
            EXECUTE format('SELECT EXISTS (SELECT 1 FROM public.%I)', item.tablename) INTO has_rows;
            IF has_rows THEN RAISE EXCEPTION 'Refusing replacement: table % is not empty', item.tablename;
            END IF;
        END IF;
    END LOOP;
"""
    guard += "END $$;\n"
    if replace_empty:
        guard += "DROP SCHEMA public CASCADE;\nCREATE SCHEMA public;\n"
    footer = f"""
CREATE TABLE public.qa_schema_version (
    singleton boolean PRIMARY KEY CHECK (singleton), sha256 text NOT NULL
);
INSERT INTO public.qa_schema_version VALUES (true, '{digest}');
"""
    result = subprocess.run(
        psql_command(config, container),
        input=guard + dump + "\n" + footer,
        encoding="utf-8",
        env={**os.environ, "PGPASSWORD": config["password"]},
        capture_output=True,
        timeout=120,
    )
    if result.returncode:
        raise RuntimeError(f"Schema restoration failed (transaction rolled back):\n{result.stderr}")
    print("Restored schema_export.sql using psql; schema version recorded.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace-empty",
        action="store_true",
        help="Replace public schema only if its business tables are empty",
    )
    parser.add_argument("--psql-container", help="Docker service container ID for CI")
    args = parser.parse_args()
    dump = (Path(__file__).resolve().parents[1] / "schema_export.sql").read_text(
        encoding="utf-8-sig"
    )
    digest = hashlib.sha256(dump.encode("utf-8")).hexdigest()
    expected_tables = set(re.findall(r"^CREATE TABLE public\.(\w+)\s*\(", dump, re.MULTILINE))
    if not expected_tables:
        raise RuntimeError("Export contains no public tables")
    config = settings()
    import psycopg2
    from psycopg2 import sql

    admin = psycopg2.connect(**{**config, "dbname": "postgres"})
    try:
        admin.autocommit = True
        with admin.cursor() as cursor:
            cursor.execute(
                "SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname=%s",
                (config["dbname"],),
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(config["dbname"]))
                )
                cursor.execute(
                    sql.SQL("COMMENT ON DATABASE {} IS %s").format(
                        sql.Identifier(config["dbname"])
                    ),
                    (MARKER,),
                )
                print("Created vkr_test with test ownership marker.")
            elif row[0] != MARKER:
                raise RuntimeError("Existing vkr_test is not marked as ours; left untouched.")
    finally:
        admin.close()

    connection = connect_test_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET lock_timeout='10s'")
            cursor.execute("SELECT pg_advisory_lock(784235901)")
        connection.commit()
        with connection:
            assert_test_database(connection)
            with connection.cursor() as cursor:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                tables = {row[0] for row in cursor.fetchall()}
                version = None
                if "qa_schema_version" in tables:
                    cursor.execute(
                        "SELECT sha256 FROM public.qa_schema_version WHERE singleton=true"
                    )
                    row = cursor.fetchone()
                    version = row[0] if row else None
        if version == digest and expected_tables <= tables:
            print("Schema already matches this export; no restoration needed.")
        else:
            if tables and not args.replace_empty:
                raise RuntimeError(
                    "Existing schema differs or has no version. If all test data is empty, "
                    "run again with --replace-empty. No data was deleted."
                )
            restore_schema(config, dump, digest, args.psql_container, args.replace_empty)
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            actual = {row[0] for row in cursor.fetchall()}
            if not expected_tables <= actual:
                raise RuntimeError(f"Missing tables: {sorted(expected_tables - actual)}")
            print(f"Verified {len(expected_tables)} exported tables (plus qa_schema_version).")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
