from importlib import import_module
from pathlib import Path
from unittest.mock import Mock

import pytest

from backend_tests.support.db_support import backend_connection, connect_test_database
from backend_tests.support.data_support import prepared_shift


@pytest.fixture
def shift_data():
    with prepared_shift() as data:
        yield data


@pytest.fixture
def db():
    connection = connect_test_database()

    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def backend(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "backend"))
    backend = import_module("app")

    def block_vk_api(*args, **kwargs):
        raise AssertionError("VK API must be mocked explicitly in API tests")

    monkeypatch.setattr(backend, "vk_api", block_vk_api)
    monkeypatch.setattr(backend, "VK_COMMUNITY_TOKEN", "")
    monkeypatch.setattr(backend, "VK_SECRET_KEY", "test-secret")
    monkeypatch.setattr(backend, "VK_CONFIRMATION_CODE", "test-confirmation")
    return backend


@pytest.fixture
def vk_mock(backend, monkeypatch):

    def successful_response(method, params):
        responses = {
            "messages.send": 12345,
            "messages.edit": 1,
            "messages.sendMessageEventAnswer": 1,
        }
        if method not in responses:
            raise AssertionError(f"No test response configured for VK method: {method}")
        return responses[method]

    mocked_api = Mock(name="vk_api", side_effect=successful_response)
    monkeypatch.setattr(backend, "vk_api", mocked_api)
    return mocked_api


@pytest.fixture
def client(backend, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(backend, "db_connection", backend_connection)

    with TestClient(backend.app) as api_client:
        yield api_client
