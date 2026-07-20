"""Tests for session persistence."""

from simplecoder import session as session_module
from simplecoder.session import list_sessions, load_session, save_session


def test_session_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSIONS_DIR", tmp_path)
    messages = [{"role": "user", "content": "hello"}]

    sid = save_session(messages, "test-model", "pytest_session")

    assert sid == "pytest_session"
    assert load_session(sid) == (messages, "test-model")


def test_default_session_ids_do_not_collide(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSIONS_DIR", tmp_path)

    first = save_session([{"role": "user", "content": "first"}], "model-a")
    second = save_session([{"role": "user", "content": "second"}], "model-b")

    assert first != second
    assert load_session(first)[1] == "model-a"
    assert load_session(second)[1] == "model-b"


def test_session_id_path_traversal_is_neutralized(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSIONS_DIR", tmp_path)

    sid = save_session([{"role": "user", "content": "x"}], "m", "../../secret")

    assert sid == "secret"
    assert (tmp_path / "secret.json").exists()
    assert load_session("../../secret") == ([{"role": "user", "content": "x"}], "m")


def test_corrupt_session_file_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSIONS_DIR", tmp_path)
    (tmp_path / "broken.json").write_text("{ invalid json", encoding="utf-8")

    assert load_session("broken") is None


def test_list_sessions_returns_newest_first(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSIONS_DIR", tmp_path)
    save_session([{"role": "user", "content": "first"}], "model-a", "first")
    save_session([{"role": "user", "content": "second"}], "model-b", "second")

    sessions = list_sessions()

    assert isinstance(sessions, list)
    assert {item["id"] for item in sessions} == {"first", "second"}
