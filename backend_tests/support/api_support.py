def make_shift_response(data, *, vk_id=None, secret="test-secret"):
    user_id = data["vk_id"] if vk_id is None else vk_id
    return {
        "type": "message_event",
        "secret": secret,
        "object": {
            "user_id": user_id,
            "peer_id": user_id,
            "event_id": f"test-response-{user_id}",
            "payload": {
                "type": "shift_response",
                "shift_id": data["shift_id"],
                "position": data["position_name"],
            },
        },
    }


def error_response_failures(response, expected_status, *, field=None, detail=None):

    failures = []
    is_json = response.headers.get("content-type", "").startswith("application/json")
    body = response.json() if is_json else response.text
    if response.status_code != expected_status:
        failures.append(f"Expected HTTP {expected_status}, got {response.status_code}")
    if not is_json or not isinstance(body, dict) or not body.get("detail"):
        failures.append(f"Expected JSON error with nonempty detail, got {body!r}")
    elif detail is not None and body["detail"] != detail:
        failures.append(f"Expected detail {detail!r}, got {body['detail']!r}")
    elif field is not None:
        errors = body["detail"]
        if not isinstance(errors, list) or not any(
            isinstance(error, dict)
            and isinstance(error.get("loc"), (list, tuple))
            and field in error["loc"]
            for error in errors
        ):
            failures.append(f"Expected validation error for {field}, got {errors!r}")
    return failures
