import json
import os
import random
from pathlib import Path
from typing import Any

if hasattr(os, "add_dll_directory"):
    postgres_bin_path = os.getenv("POSTGRES_BIN_PATH", "C:/Program Files/PostgreSQL/18/bin")
    if Path(postgres_bin_path).exists():
        os.add_dll_directory(postgres_bin_path)

import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

VK_COMMUNITY_TOKEN = os.getenv("VK_COMMUNITY_TOKEN", "")
VK_CONFIRMATION_CODE = os.getenv("VK_CONFIRMATION_CODE", "")
VK_SECRET_KEY = os.getenv("VK_SECRET_KEY", "")
if VK_SECRET_KEY == "change_me":
    VK_SECRET_KEY = ""
VK_API_VERSION = os.getenv("VK_API_VERSION", "5.199")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "vkr_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

app = FastAPI(title="VKR VK Bot Backend")


class ShiftPosition(BaseModel):
    position: str
    count: int = 1


class ShiftNotificationRequest(BaseModel):
    shift_id: int | None = None
    message: str
    user_ids: list[int]
    open_positions: list[ShiftPosition] = Field(default_factory=list)


def db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )


def init_db() -> None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS shift_responses (
                    id SERIAL PRIMARY KEY,
                    business_id INTEGER NOT NULL,
                    shift_id INTEGER,
                    vk_id TEXT,
                    employee_id INTEGER,
                    position_name TEXT,
                    response_status TEXT,
                    response_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT
                )
                """
            )
            cursor.execute("ALTER TABLE shift_responses ADD COLUMN IF NOT EXISTS raw_payload TEXT")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id SERIAL PRIMARY KEY,
                    shift_id INTEGER,
                    user_id INTEGER,
                    message_text TEXT,
                    send_status TEXT NOT NULL,
                    error_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def vk_api(method: str, params: dict[str, Any]) -> dict[str, Any]:
    if not VK_COMMUNITY_TOKEN:
        raise HTTPException(status_code=500, detail="VK_COMMUNITY_TOKEN is not configured")

    response = requests.post(
        f"https://api.vk.com/method/{method}",
        data={
            **params,
            "access_token": VK_COMMUNITY_TOKEN,
            "v": VK_API_VERSION,
        },
        timeout=15,
    )
    data = response.json()
    if "error" in data:
        raise HTTPException(status_code=502, detail=data["error"])
    return data["response"]


def vk_send_message(user_id: int, message: str, keyboard: str | None = None) -> None:
    params: dict[str, Any] = {
        "user_id": user_id,
        "random_id": random.randint(1, 2_147_483_647),
        "message": message,
    }
    if keyboard:
        params["keyboard"] = keyboard
    vk_api("messages.send", params)


def build_main_menu_keyboard() -> str:
    return json.dumps(
        {
            "one_time": False,
            "inline": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "callback",
                            "label": "Мои смены",
                            "payload": json.dumps({"type": "my_shifts"}, ensure_ascii=False),
                        },
                        "color": "primary",
                    },
                    {
                        "action": {
                            "type": "callback",
                            "label": "Доступные смены",
                            "payload": json.dumps({"type": "available_shifts"}, ensure_ascii=False),
                        },
                        "color": "positive",
                    },
                ]
            ],
        },
        ensure_ascii=False,
    )


def format_button_date(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return f"{text[8:10]}.{text[5:7]}"
    return text


def trim_button_label(label: str) -> str:
    return label if len(label) <= 40 else label[:37].rstrip() + "..."


def get_shift_info(connection, shift_id: int | None) -> dict[str, Any] | None:
    if not shift_id:
        return None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, business_id, shift_date, start_time, end_time
            FROM shifts
            WHERE id = %s
            LIMIT 1
            """,
            (shift_id,),
        )
        return cursor.fetchone()


def employee_has_shift_on_same_day(
    connection, business_id: int, shift_id: int, employee_id: int
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM shift_assignments sa
            JOIN shifts assigned_shift ON assigned_shift.id = sa.shift_id
            JOIN shifts target_shift ON target_shift.id = %s
            WHERE sa.employee_id = %s
                AND assigned_shift.business_id = %s
                AND target_shift.business_id = %s
                AND assigned_shift.shift_date = target_shift.shift_date
                AND assigned_shift.id <> target_shift.id
            LIMIT 1
            """,
            (shift_id, employee_id, business_id, business_id),
        )
        return cursor.fetchone() is not None


def shift_button_state(
    connection, vk_id: int, shift_id: int, position_name: str
) -> tuple[bool, str, str]:
    shift_info = get_shift_info(connection, shift_id)
    if not shift_info:
        return False, "secondary", "Смена не найдена"

    business_id = shift_info["business_id"]
    employee_id = get_employee_id_by_vk_id(connection, business_id, vk_id)
    if employee_id is None:
        return False, "secondary", "Сотрудник с таким VK ID не найден"

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM shift_assignments WHERE shift_id = %s AND employee_id = %s LIMIT 1",
            (shift_id, employee_id),
        )
        if cursor.fetchone():
            return False, "secondary", "Вы уже записаны на эту смену"

    if employee_has_shift_on_same_day(connection, business_id, shift_id, employee_id):
        return False, "negative", "В этот день у вас уже есть смена"

    if not employee_can_work_position(connection, business_id, employee_id, position_name):
        return False, "secondary", "Должность не подходит"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM shift_open_positions
            WHERE shift_id = %s AND position_name = %s AND employee_count > 0
            LIMIT 1
            """,
            (shift_id, position_name),
        )
        if not cursor.fetchone():
            return False, "secondary", "Свободных мест уже нет"

    return True, "positive", ""


def build_shift_keyboard(
    shift_id: int | None,
    open_positions: list[ShiftPosition],
    user_id: int | None = None,
) -> str | None:
    if not shift_id or not open_positions:
        return None

    buttons = []
    with db_connection() as connection:
        shift_info = get_shift_info(connection, shift_id)
        date_text = format_button_date(shift_info["shift_date"]) if shift_info else ""

        for open_position in open_positions:
            position_text = open_position.position
            label_prefix = "Хочу выйти"
            payload_type = "shift_response"
            payload_message = ""
            color = "positive"

            if user_id:
                is_available, color, payload_message = shift_button_state(
                    connection,
                    user_id,
                    shift_id,
                    position_text,
                )
                if not is_available:
                    label_prefix = "Нельзя взять"
                    payload_type = "shift_unavailable"

            payload = {
                "type": payload_type,
                "shift_id": shift_id,
                "position": position_text,
            }
            if payload_message:
                payload["message"] = payload_message

            buttons.append(
                [
                    {
                        "action": {
                            "type": "callback",
                            "label": trim_button_label(
                                f"{label_prefix}: {date_text} {position_text}".strip()
                            ),
                            "payload": json.dumps(payload, ensure_ascii=False),
                        },
                        "color": color,
                    }
                ]
            )

    if not buttons:
        return None

    return json.dumps({"one_time": False, "inline": True, "buttons": buttons}, ensure_ascii=False)


def build_available_shifts_keyboard(shifts: list[dict[str, Any]]) -> str:
    buttons = []
    for shift in shifts[:10]:
        date_text = format_button_date(shift.get("shift_date"))
        buttons.append(
            [
                {
                    "action": {
                        "type": "callback",
                        "label": trim_button_label(
                            f"Хочу выйти: {date_text} {shift['position_name']}".strip()
                        ),
                        "payload": json.dumps(
                            {
                                "type": "shift_response",
                                "shift_id": shift["shift_id"],
                                "position": shift["position_name"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    "color": "positive",
                }
            ]
        )
    return json.dumps({"one_time": False, "inline": True, "buttons": buttons}, ensure_ascii=False)


def build_my_shifts_keyboard(shifts: list[dict[str, Any]]) -> str:
    buttons = []
    for shift in shifts[:10]:
        date_text = format_button_date(shift.get("shift_date"))
        buttons.append(
            [
                {
                    "action": {
                        "type": "callback",
                        "label": trim_button_label(
                            f"Отменить: {date_text} {shift['position_name']}".strip()
                        ),
                        "payload": json.dumps(
                            {
                                "type": "cancel_shift",
                                "shift_id": shift["shift_id"],
                                "position": shift["position_name"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    "color": "negative",
                }
            ]
        )
    return json.dumps({"one_time": False, "inline": True, "buttons": buttons}, ensure_ascii=False)


def format_shift_line(shift: dict[str, Any]) -> str:
    business_name = shift.get("business_name") or "Предприятие"
    return (
        f"{business_name}: {shift['shift_date']} "
        f"{shift['start_time']}-{shift['end_time']} | {shift['position_name']}"
    )


def get_my_shifts(vk_id: int) -> list[dict[str, Any]]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT b.name AS business_name, s.id AS shift_id, s.shift_date,
                       s.start_time, s.end_time, sa.position_name, s.status
                FROM employees e
                JOIN shift_assignments sa ON sa.employee_id = e.id
                JOIN shifts s ON s.id = sa.shift_id
                LEFT JOIN businesses b ON b.id = s.business_id
                WHERE e.vk_id = %s
                    AND e.is_active = 1
                    AND TO_DATE(s.shift_date, 'YYYY-MM-DD') >= CURRENT_DATE
                ORDER BY s.shift_date ASC, s.start_time ASC
                LIMIT 10
                """,
                (str(vk_id),),
            )
            return cursor.fetchall()


def get_available_shifts(vk_id: int) -> list[dict[str, Any]]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT b.name AS business_name, s.id AS shift_id, s.shift_date,
                       s.start_time, s.end_time, sop.position_name, sop.employee_count
                FROM employees e
                JOIN shifts s ON s.business_id = e.business_id
                JOIN shift_open_positions sop
                    ON sop.shift_id = s.id
                    AND sop.employee_count > 0
                LEFT JOIN businesses b ON b.id = s.business_id
                LEFT JOIN positions employee_position
                    ON employee_position.business_id = e.business_id
                    AND employee_position.name = e.position
                LEFT JOIN position_capabilities pc
                    ON pc.position_id = employee_position.id
                LEFT JOIN positions covered_position
                    ON covered_position.id = pc.covered_position_id
                WHERE e.vk_id = %s
                    AND e.is_active = 1
                    AND TO_DATE(s.shift_date, 'YYYY-MM-DD') >= CURRENT_DATE
                    AND (e.position = sop.position_name OR covered_position.name = sop.position_name)
                    AND NOT EXISTS (
                        SELECT 1
                        FROM shift_assignments sa
                        WHERE sa.shift_id = s.id
                            AND sa.employee_id = e.id
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM shift_assignments busy_sa
                        JOIN shifts busy_shift ON busy_shift.id = busy_sa.shift_id
                        WHERE busy_sa.employee_id = e.id
                            AND busy_shift.shift_date = s.shift_date
                    )
                ORDER BY s.shift_date ASC, s.start_time ASC
                LIMIT 10
                """,
                (str(vk_id),),
            )
            return cursor.fetchall()


def send_main_menu(user_id: int) -> None:
    vk_send_message(
        user_id,
        "Выберите действие кнопкой меню. Текстовые сообщения бот пока не обрабатывает.",
        build_main_menu_keyboard(),
    )


def send_my_shifts(user_id: int) -> None:
    shifts = get_my_shifts(user_id)
    if not shifts:
        vk_send_message(
            user_id, "У вас пока нет будущих назначенных смен.", build_main_menu_keyboard()
        )
        return

    lines = ["Ваши ближайшие смены:"]
    lines.extend(
        f"{index}. {format_shift_line(shift)}" for index, shift in enumerate(shifts, start=1)
    )
    lines.append("Чтобы отказаться от смены, нажмите кнопку под сообщением.")
    vk_send_message(user_id, "\n".join(lines), build_my_shifts_keyboard(shifts))


def send_available_shifts(user_id: int) -> None:
    shifts = get_available_shifts(user_id)
    if not shifts:
        vk_send_message(
            user_id,
            "Сейчас нет доступных смен под вашу должность или вы уже заняты в подходящие дни.",
            build_main_menu_keyboard(),
        )
        return

    lines = ["Доступные смены:"]
    lines.extend(
        f"{index}. {format_shift_line(shift)}" for index, shift in enumerate(shifts, start=1)
    )
    lines.append("Чтобы занять место, нажмите кнопку под сообщением.")
    vk_send_message(user_id, "\n".join(lines), build_available_shifts_keyboard(shifts))


def get_business_id_by_shift(connection, shift_id: int | None) -> int | None:
    if not shift_id:
        return None
    with connection.cursor() as cursor:
        cursor.execute("SELECT business_id FROM shifts WHERE id = %s", (shift_id,))
        row = cursor.fetchone()
    return row["business_id"] if row else None


def get_employee_id_by_vk_id(connection, business_id: int, vk_id: int) -> int | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM employees
            WHERE business_id = %s AND vk_id = %s
            LIMIT 1
            """,
            (business_id, str(vk_id)),
        )
        row = cursor.fetchone()
    return row["id"] if row else None


def get_employee_name_by_id(connection, employee_id: int | None) -> str:
    if not employee_id:
        return ""
    with connection.cursor() as cursor:
        cursor.execute("SELECT full_name FROM employees WHERE id = %s LIMIT 1", (employee_id,))
        row = cursor.fetchone()
    return row["full_name"] if row else ""


def add_activity_log(
    connection,
    business_id: int,
    action_type: str,
    entity_type: str,
    entity_id: int | None,
    description: str,
    related_employee_id: int | None = None,
    related_shift_id: int | None = None,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO activity_logs (
                business_id, action_type, entity_type, entity_id,
                related_employee_id, related_shift_id, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                business_id,
                action_type,
                entity_type,
                entity_id,
                related_employee_id,
                related_shift_id,
                description,
            ),
        )


def employee_can_work_position(
    connection, business_id: int, employee_id: int, position_name: str
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM employees e
            LEFT JOIN positions employee_position
                ON employee_position.business_id = e.business_id
                AND employee_position.name = e.position
            LEFT JOIN position_capabilities pc
                ON pc.position_id = employee_position.id
            LEFT JOIN positions covered_position
                ON covered_position.id = pc.covered_position_id
            WHERE e.business_id = %s
                AND e.id = %s
                AND e.is_active = 1
                AND (e.position = %s OR covered_position.name = %s)
            LIMIT 1
            """,
            (business_id, employee_id, position_name, position_name),
        )
        return cursor.fetchone() is not None


def occupy_open_position(
    connection, shift_id: int, business_id: int, employee_id: int | None, position_name: str
) -> tuple[str, str]:
    if employee_id is None:
        return "rejected", "Сотрудник с таким VK ID не найден в предприятии"

    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM employees WHERE id = %s FOR UPDATE", (employee_id,))

        cursor.execute(
            "SELECT 1 FROM shift_assignments WHERE shift_id = %s AND employee_id = %s LIMIT 1",
            (shift_id, employee_id),
        )
        if cursor.fetchone():
            return "rejected", "Сотрудник уже назначен на эту смену"

        if employee_has_shift_on_same_day(connection, business_id, shift_id, employee_id):
            return "rejected", "В этот день у сотрудника уже есть смена"

        if not employee_can_work_position(connection, business_id, employee_id, position_name):
            return "rejected", "Должность сотрудника не подходит для этой позиции"

        cursor.execute(
            """
            SELECT id, employee_count, payment_type, hourly_rate, fixed_rate, percent_rate
            FROM shift_open_positions
            WHERE shift_id = %s AND position_name = %s AND employee_count > 0
            ORDER BY id
            LIMIT 1
            FOR UPDATE
            """,
            (shift_id, position_name),
        )
        open_position = cursor.fetchone()
        if not open_position:
            return "rejected", "Свободных мест по этой позиции уже нет"

        cursor.execute(
            """
            INSERT INTO shift_assignments (
                shift_id, employee_id, position_name, payment_type,
                hourly_rate, fixed_rate, percent_rate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                shift_id,
                employee_id,
                position_name,
                open_position["payment_type"],
                open_position["hourly_rate"],
                open_position["fixed_rate"],
                open_position["percent_rate"],
            ),
        )

        if open_position["employee_count"] <= 1:
            cursor.execute("DELETE FROM shift_open_positions WHERE id = %s", (open_position["id"],))
        else:
            cursor.execute(
                "UPDATE shift_open_positions SET employee_count = employee_count - 1 WHERE id = %s",
                (open_position["id"],),
            )

    return "accepted", "Сотрудник назначен на свободную позицию"


def cancel_assigned_shift(
    connection, shift_id: int, business_id: int, employee_id: int | None, position_name: str
) -> tuple[str, str]:
    if employee_id is None:
        return "cancel_rejected", "Сотрудник с таким VK ID не найден в предприятии"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, payment_type, hourly_rate, fixed_rate, percent_rate
            FROM shift_assignments
            WHERE shift_id = %s AND employee_id = %s AND position_name = %s
            LIMIT 1
            FOR UPDATE
            """,
            (shift_id, employee_id, position_name),
        )
        assignment = cursor.fetchone()
        if not assignment:
            return "cancel_rejected", "Эта смена уже не назначена сотруднику"

        cursor.execute("DELETE FROM shift_assignments WHERE id = %s", (assignment["id"],))

        cursor.execute(
            """
            SELECT id
            FROM shift_open_positions
            WHERE shift_id = %s AND position_name = %s
            LIMIT 1
            FOR UPDATE
            """,
            (shift_id, position_name),
        )
        open_position = cursor.fetchone()
        if open_position:
            cursor.execute(
                "UPDATE shift_open_positions SET employee_count = employee_count + 1 WHERE id = %s",
                (open_position["id"],),
            )
        else:
            cursor.execute(
                """
                INSERT INTO shift_open_positions (
                    shift_id, position_name, employee_count, payment_type,
                    hourly_rate, fixed_rate, percent_rate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    shift_id,
                    position_name,
                    1,
                    assignment["payment_type"],
                    assignment["hourly_rate"],
                    assignment["fixed_rate"],
                    assignment["percent_rate"],
                ),
            )

    return "cancelled", "Смена отменена, место снова стало свободным"


def save_shift_response(
    vk_id: int, payload: dict[str, Any], raw_payload: dict[str, Any]
) -> tuple[str, str]:
    with db_connection() as connection:
        shift_id = payload.get("shift_id")
        business_id = get_business_id_by_shift(connection, shift_id)
        if business_id is None:
            raise HTTPException(status_code=404, detail=f"Shift {shift_id} was not found")

        employee_id = get_employee_id_by_vk_id(connection, business_id, vk_id)
        employee_name = get_employee_name_by_id(connection, employee_id)
        position_name = payload.get("position", "")
        response_status, response_message = occupy_open_position(
            connection,
            shift_id,
            business_id,
            employee_id,
            position_name,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO shift_responses (
                    business_id, shift_id, vk_id, employee_id, position_name,
                    response_status, response_message, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    business_id,
                    shift_id,
                    str(vk_id),
                    employee_id,
                    position_name,
                    response_status,
                    response_message,
                    json.dumps(raw_payload, ensure_ascii=False),
                ),
            )

        add_activity_log(
            connection,
            business_id,
            "vk_response",
            "vk",
            shift_id,
            f"Получен отклик из VK: {employee_name or f'VK {vk_id}'} на позицию {position_name}",
            employee_id,
            shift_id,
        )

    return response_status, response_message


def save_shift_cancellation(
    vk_id: int, payload: dict[str, Any], raw_payload: dict[str, Any]
) -> tuple[str, str]:
    with db_connection() as connection:
        shift_id = payload.get("shift_id")
        business_id = get_business_id_by_shift(connection, shift_id)
        if business_id is None:
            raise HTTPException(status_code=404, detail=f"Shift {shift_id} was not found")

        employee_id = get_employee_id_by_vk_id(connection, business_id, vk_id)
        employee_name = get_employee_name_by_id(connection, employee_id)
        position_name = payload.get("position", "")
        response_status, response_message = cancel_assigned_shift(
            connection,
            shift_id,
            business_id,
            employee_id,
            position_name,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO shift_responses (
                    business_id, shift_id, vk_id, employee_id, position_name,
                    response_status, response_message, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    business_id,
                    shift_id,
                    str(vk_id),
                    employee_id,
                    position_name,
                    response_status,
                    response_message,
                    json.dumps(raw_payload, ensure_ascii=False),
                ),
            )

        add_activity_log(
            connection,
            business_id,
            "vk_cancel",
            "vk",
            shift_id,
            f"Сотрудник отменил смену через VK: {employee_name or f'VK {vk_id}'} ({position_name})",
            employee_id,
            shift_id,
        )

    return response_status, response_message


@app.get("/health")
def health() -> dict[str, str]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            cursor.fetchone()
    return {"status": "ok", "database": "ok"}


def disable_callback_button(peer_id: int | None, conversation_message_id: int | None) -> None:
    if not peer_id or not conversation_message_id:
        return

    try:
        vk_api(
            "messages.edit",
            {
                "peer_id": peer_id,
                "conversation_message_id": conversation_message_id,
                "keyboard": json.dumps({"inline": True, "buttons": []}, ensure_ascii=False),
            },
        )
    except HTTPException:
        pass


def send_message_event_answer(
    event_ids: str | list[str | None] | tuple[str | None, ...] | None,
    peer_id: int | None,
    user_id: int | None,
    text: str,
) -> bool:
    if isinstance(event_ids, str) or event_ids is None:
        candidate_event_ids = [event_ids]
    else:
        candidate_event_ids = list(event_ids)

    if not peer_id or not user_id:
        return False

    for event_id in candidate_event_ids:
        if not event_id:
            continue
        try:
            vk_api(
                "messages.sendMessageEventAnswer",
                {
                    "event_id": event_id,
                    "user_id": user_id,
                    "peer_id": peer_id,
                    "event_data": json.dumps(
                        {
                            "type": "show_snackbar",
                            "text": text,
                        },
                        ensure_ascii=False,
                    ),
                },
            )
            return True
        except HTTPException:
            continue

    return False


@app.post("/vk/callback", response_class=PlainTextResponse)
async def vk_callback(request: Request) -> PlainTextResponse:
    event = await request.json()

    if VK_SECRET_KEY and event.get("secret") != VK_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid VK secret key")

    event_type = event.get("type")
    if event_type == "confirmation":
        return PlainTextResponse(VK_CONFIRMATION_CODE)

    if event_type == "message_new":
        message = event.get("object", {}).get("message", {})
        user_id = message.get("from_id")
        if user_id:
            send_main_menu(user_id)
        return PlainTextResponse("ok")

    if event_type == "message_event":
        obj = event.get("object", {})
        payload = obj.get("payload") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)

        vk_id = obj.get("user_id")
        peer_id = obj.get("peer_id")
        button_event_id = obj.get("event_id")
        callback_event_id = event.get("event_id")
        event_ids = [button_event_id, callback_event_id]
        payload_type = payload.get("type")
        response_message = "Действие выполнено"
        answered_event = False

        if payload_type in {"my_shifts", "available_shifts", "shift_response", "cancel_shift"}:
            answered_event = send_message_event_answer(
                event_ids, peer_id, vk_id, "Обрабатываю запрос..."
            )

        if payload_type == "my_shifts" and vk_id:
            send_my_shifts(vk_id)
            response_message = "Отправил ваши смены"
        elif payload_type == "available_shifts" and vk_id:
            send_available_shifts(vk_id)
            response_message = "Отправил доступные смены"
        elif payload_type == "shift_response" and vk_id:
            _, response_message = save_shift_response(vk_id, payload, event)
            send_my_shifts(vk_id)
            disable_callback_button(peer_id, obj.get("conversation_message_id"))
        elif payload_type == "shift_unavailable" and vk_id:
            response_message = payload.get("message") or "Эту смену нельзя взять"
        elif payload_type == "cancel_shift" and vk_id:
            _, response_message = save_shift_cancellation(vk_id, payload, event)
            send_available_shifts(vk_id)
            disable_callback_button(peer_id, obj.get("conversation_message_id"))

        if not answered_event or payload_type == "shift_unavailable":
            send_message_event_answer(event_ids, peer_id, vk_id, response_message)

    return PlainTextResponse("ok")


@app.post("/api/send-shift-notification")
def send_shift_notification(payload: ShiftNotificationRequest) -> dict[str, Any]:
    results = []

    for user_id in payload.user_ids:
        keyboard = build_shift_keyboard(payload.shift_id, payload.open_positions, user_id)
        status = "sent"
        error_text = ""
        try:
            vk_send_message(user_id, payload.message, keyboard)
        except HTTPException as exc:
            status = "error"
            error_text = str(exc.detail)

        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sent_notifications (
                        shift_id, user_id, message_text, send_status, error_text
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (payload.shift_id, user_id, payload.message, status, error_text),
                )

        results.append({"user_id": user_id, "status": status, "error": error_text})

    return {"results": results}


@app.get("/api/shift-responses")
def get_shift_responses() -> dict[str, list[dict[str, Any]]]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, business_id, shift_id, vk_id, employee_id, position_name,
                       response_status, response_message, created_at, processed_at
                FROM shift_responses
                ORDER BY created_at DESC, id DESC
                """
            )
            rows = cursor.fetchall()

    return {"responses": rows}
